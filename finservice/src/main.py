import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.payout_consumer import PayoutConsumer

from src.core.webhook_consumer import WebhookConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    payout_consumer = PayoutConsumer()
    webhook_consumer = WebhookConsumer()

    payout_task = asyncio.create_task(
        payout_consumer.start(),
        name = "payout-consumer",
    )
    webhook_task = asyncio.create_task(
        webhook_consumer.start(),
        name="webhook-consumer",
    )
    app.state.payout_consumer = payout_consumer
    app.state.webhook_consumer = webhook_consumer

    app.state.payout_task = payout_task
    app.state.webhook_task = webhook_task

    logger.info(f"Application started..")
    logger.info("Payout consumer started")
    logger.info("Webhook consumer started")

    try:
        yield
    finally:
        logger.info("Application shutting down...")
        payout_consumer.stop()
        webhook_consumer.stop()

        for task in (payout_task, webhook_task):
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception(
                    "Consumer task failed during shutdown: %s",
                    task.get_name(),
                )





app = FastAPI(
    title="Payout Service API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }
