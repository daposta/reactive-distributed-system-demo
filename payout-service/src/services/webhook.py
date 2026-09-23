import logging

from src.core.settings import settings
from src.schemas.webhook import TazapayWebhook
from src.core.producer import  message_producer

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self):
        self.topic = settings.WEBHOOK_TOPIC

    async def handle_tazapay_webhook(self, payload: TazapayWebhook):
        try:
            # webhook_event = TazapayWebhook.model_validate(payload)

            data = payload.data
            payout_id = data.id
            status = data.status
            logger.info(f"Processing webook for payout ID: {payout_id} with status: {status}")
            payload = payload.model_dump()
            await message_producer.send(self.topic, payout_id, payload)
            logger.info(f"Successfully sent webhook event to Kafka topic: {self.topic} for payout ID: {payout_id}")

        except Exception as e:
            logger.exception(f"Error processing webhook: {e}")
