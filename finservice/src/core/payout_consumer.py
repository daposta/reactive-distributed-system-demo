import asyncio
import json
import logging

from confluent_kafka import Consumer
from sqlalchemy.orm import Session

from .database import get_session, get_db_session
from .settings import settings
from ..models.payout import PayoutStatus
from ..schemas.payment_service import TazapayServiceRequest, TazapayServiceResponse, TazapayBeneficiaryDetails, \
    TazapayDestinationDetail, TazapayBankCode, TazapayBank, TazapayAddress
from ..schemas.payout import PayoutEvent

from ..services.payout import PayoutService
from ..services.tazapay import TazapayService

logger = logging.getLogger(__name__)
logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

class PayoutConsumer:
    def __init__(self, ):
        self.conf = {
            "bootstrap.servers":"127.0.0.1:29092",
            "group.id": settings.PAYOUT_CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False

        }
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe([settings.PAYOUT_TOPIC])
        self.running = False
        self.tazapay_service = TazapayService()

    async def handle_initiated_payout(self, message):
        try:
            logger.info(f"Received payout initiated event: {message}")
            event_data = json.loads(message.value().decode('utf-8'))
            reference_id = event_data["requestId"]
            payout_event = PayoutEvent.model_validate(event_data)
            payload = TazapayServiceRequest(
                requestId=payout_event.requestId,
                reference_id= payout_event.requestId,
                amount=payout_event.amount,
                currency=payout_event.currency,
                purpose=payout_event.purpose,
                transaction_description=payout_event.transaction_description,

                beneficiary_details=TazapayBeneficiaryDetails(
                    name=payout_event.beneficiary_details.name,
                    type=payout_event.beneficiary_details.type,
                    address=TazapayAddress(
                        line1=payout_event.beneficiary_details.address.line1,
                        city=payout_event.beneficiary_details.address.city,
                        state=payout_event.beneficiary_details.address.state,
                        country=payout_event.beneficiary_details.address.country,
                        postal_code=payout_event.beneficiary_details.address.postal_code,
                    ),

                    destination_details=TazapayDestinationDetail(
                        type=payout_event.destination_details.destination_type,
                        bank=TazapayBank(
                            bank_codes=TazapayBankCode(
                                swift_code=payout_event.destination_details.bank.bank_codes.swift_code,
                                aba_code=payout_event.destination_details.bank.bank_codes.aba_code,
                            ),
                            account_number=payout_event.destination_details.bank.account_number,
                            bank_name=payout_event.destination_details.bank.bank_name,
                            country=payout_event.destination_details.bank.country,
                            currency=payout_event.destination_details.bank.currency,
                            branch_name=payout_event.destination_details.bank.branch_name
                        ),
                    ),
                ),)
            response = await self.process_payout(payload)
            logger.info(response.data.id)
            await asyncio.to_thread(
                self.consumer.commit, message=message
            )
            logger.info(
                "Successfully processed payout: %s",
                reference_id,
            )

        except json.JSONDecodeError as e:
            logger.exception(f"Invalid payout event: {message.value()}")
        except KeyError as exc:
            logger.exception(f"Missing field in payout event: {exc}")
        except Exception as e:
            logger.exception(f"Error processing payout event: {e}")


    async def process_payout(self, event):
        reference_id = event.requestId
        logger.info(
            f"Processing payout for : {reference_id}"
        )

        try:
            response = await self.tazapay_service.run_payout(event)
            await self.update_payout_status(reference_id, response)
            return response
        except Exception as e:
            logger.exception(f"Failed to process payout with reference_id: {reference_id}")
            raise

    async def start(self):
        self.running = True

        logger.info(
            f"Payout consumer started: topic={settings.PAYOUT_TOPIC}, group={settings.PAYOUT_CONSUMER_GROUP}"
        )
        try:
            while self.running:
                message = await  asyncio.to_thread(self.consumer.poll, 1.0)
                if message is None:
                    continue
                if message.error():
                    logger.error(f"Kafka consumer error: {message.error()}")
                    continue
                print(f"message -> {message}")
                await self.handle_initiated_payout(message)

        except asyncio.CancelledError:
            logger.info("Payout consumer cancellation received")
            raise
        finally:
            self.stop()

    def stop(self):
        if not self.running:
            return
        self.running = False
        logger.info("Stopping payout consumer")
        self.consumer.close()


    async def update_payout_status(self, reference_id, response: TazapayServiceResponse, ):
        with get_db_session() as session:
            payout_service =  PayoutService(session)
            try:
                data = response.data
                service_id = data.id
                currency = data.currency

                payout_obj = await payout_service.find_by_id(reference_id)
                if payout_obj:
                    payout_obj.payment_service_id = service_id
                    payout_obj.status = "PENDING"

                    if data.payout_fx_transaction:
                        final_currency = data.payout_fx_transaction.final_amount.currency
                        payout_obj.currency_code = currency + '/' + final_currency
                        payout_obj.fx_rate = data.payout_fx_transaction.exchange_rate
                        payout_obj.base_amount = data.payout_fx_transaction.final_amount.amount
                        logger.info(f"Updated payout status for request_id {reference_id} "
                                    f"with service_id: {service_id} "
                                    f"currency_code {payout_obj.currency_code} "
                                    f"fx_rate: {payout_obj.fx_rate} "
                                    f"base_amount: {payout_obj.base_amount }")
                    else:
                        payout_obj.currency_code = currency
                        logger.info(f"Updated payout status for request_id {reference_id} "
                                    f"with service_id: {service_id} "
                                    f"currency_code {payout_obj.currency_code}")
                    await payout_service.update(payout_obj)
                else:

                    await payout_service.save(reference_id, response)
                session.commit()
            except Exception as e:
                logger.exception(f"Update status had an exception: {e}")
