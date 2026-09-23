import logging

from sqlalchemy.orm import Session

from src.models.payout import PayoutStatus

from src.schemas.payment_service import TazapayServiceResponse

from src.schemas.enums import PaymentStatus

logger = logging.getLogger(__name__)

class PayoutService:
    def __init__(self, session: Session):
        self.session = session


    async def find_by_id(self, ref_id):
        statement =  self.session.query(PayoutStatus).where(PayoutStatus.reference_id == ref_id)
        payout = self.session.scalar(statement)
        logger.info(f"Payout with {ref_id} returned")
        return payout

    async def find_by_tazapay_id(self, tazapay_id):
        statement =  self.session.query(PayoutStatus).where(PayoutStatus.payment_service_id == tazapay_id)
        payout = self.session.scalar(statement)
        logger.info(f"Payout with {tazapay_id} returned")
        return payout

    async def save(self, reference_id,  response:TazapayServiceResponse):
        data = response.data
        service_id = data.id
        currency = data.currency
        payout_status = PayoutStatus(
            reference_id=reference_id,
            status=PaymentStatus.PROCESSING.value,
            payment_service_id=service_id
        )

        if data.payout_fx_transaction:
            final_currency = data.payout_fx_transaction.final_amount.currency
            payout_status.currency_code = currency + '/' + final_currency
            payout_status.fx_rate = data.payout_fx_transaction.exchange_rate
            payout_status.base_amount = data.payout_fx_transaction.final_amount.amount
            logger.info(f"Updated payout status for request_id {reference_id} "
                        f"with service_id: {service_id} "
                        f"currency_code {payout_status.currency_code} "
                        f"fx_rate: {payout_status.fx_rate} "
                        f"base_amount: {payout_status.base_amount}")

        self.session.add(payout_status)
        logger.info(f"Payout saved successfully")
        return payout_status


    async def update(self, payout: dict, **fields):
        for field, value in fields.items():
            setattr(payout, field, value)

        logger.info(
            "Payout updated: reference_id=%s",
            payout.reference_id,
        )

        return payout
