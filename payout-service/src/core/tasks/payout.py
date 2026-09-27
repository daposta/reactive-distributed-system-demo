import logging

from src.core.payout_producer import payout_producer
from src.core.database import get_db_session
from src.core.settings import settings
from src.services.payout_inbox_service import PayoutOutboxService
from src.corecelery_app import celery

logger = logging.getLogger(__name__)
outbox_service = PayoutOutboxService()

@celery.task(
    bind=True,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def publish_outbox(self):
    logger.info(f"Starting outbox")
    entries = outbox_service.find_100_most_recent_new_messages()
    if not entries:
        logger.info("No new outbox messages found")
        return
    for entry in entries:
        logger.info(f"Found entry with reference number:{entry.reference_id}")
        try:
            payout_producer.send(
                topic=settings.PAYOUT_TOPIC,
                key=entry.reference_id,
                payload=entry.payload
            )
            outbox_service.update(
                entry.id,
                status="SENT",
            )
            logger.info("send payload to topic succesfully")
        except Exception as e:
            logger.exception(f"Sending message failed for reference_id: {entry.reference_id}")
            raise self.retry(exc=e, countdown=5)
