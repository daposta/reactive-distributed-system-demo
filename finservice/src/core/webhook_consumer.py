import asyncio
import json
import logging

from confluent_kafka import Consumer

from .database import get_db_session
from .settings import settings
from ..schemas.webhook import TazapayWebhook
from ..services.payout import PayoutService
from ..services.tazapay import TazapayService
from ..services.webhook import WebhookService

logger = logging.getLogger(__name__)
logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

class WebhookConsumer:
    def __init__(self):
        self.conf = {
            "bootstrap.servers": "127.0.0.1:29092",
            "group.id": settings.WEBHOOK_CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False

        }
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe([settings.WEBHOOK_TOPIC])
        self.running = False
        self.webhook_service = WebhookService()


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
                await self.handle_webhook_event(message)

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

    async def handle_webhook_event(self, message: str):
        logger.info(f"Received webhook event: {message}")
        try:
            event_data = json.loads(message.value().decode('utf-8'))
            webhook_event = TazapayWebhook.model_validate(event_data)
            data = webhook_event.data
            payout_id = data.id
            status = data.status
            logger.info(f"Processing webhook for payout id: {payout_id} with status: {status}")
            with get_db_session() as session:
                payout_service = PayoutService(session)
                payout = await  payout_service.find_by_tazapay_id(payout_id)
                if not payout:
                    logger.warn(f"No payout found for tazapay id: {payout_id}")
                    return
                payout.status = status.upper()
                await payout_service.update(payout)
                session.commit()
                logger.info(f"Updated payout for tazapay id: {payout_id} to status: {status}")

        except json.JSONDecodeError as e:
            logger.exception(f"Invalid payout event: {message.value()}")
        except KeyError as exc:
            logger.exception(f"Missing field in payout event: {exc}")
        except Exception as e:
            logger.exception(f"Error processing payout event: {e}")
