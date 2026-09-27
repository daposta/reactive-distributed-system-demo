from celery import Celery
from src.core.settings import settings

celery = Celery(
 "payout_service",
    broker=settings.BROKER_URL,
    backend=settings.BACKEND_URL
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=(
        "src.core.tasks.payout",
    ),
    beat_schedule={
            "dispatch-outbox-every-5-seconds": {
                "task": "src.core.tasks.payout.publish_outbox",
                "schedule": 5.0,
            },
        },
)
