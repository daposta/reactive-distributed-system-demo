import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.payout_consumer import PayoutConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    payout_consumer = PayoutConsumer()
    consumer_task = asyncio.create_task(
        payout_consumer.start()
    )
    app.state.payout_consumer = payout_consumer
    app.state.consumer_task = consumer_task

    logger.info(f"Application started..")
    try:
        yield
    finally:
        logger.info("Application shutting down...")
        payout_consumer.stop()
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass





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
