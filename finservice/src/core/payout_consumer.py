import asyncio
import json
import logging

from confluent_kafka import Consumer

from .settings import settings

logger = logging.getLogger(__name__)
logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

class PayoutConsumer:
    def __init__(self):
        self.conf = {
            "bootstrap.servers":"127.0.0.1:29092",
            "group.id": settings.PAYOUT_CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False

        }
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe([settings.PAYOUT_TOPIC])
        self.running = False


    async def handle_initiated_payout(self, message):
        try:
            logger.info(f"Received payout initiated event: {message}")
            event = json.loads(message.value().decode('utf-8'))
            reference_id = event["reference_id"]
            await self.process_payout(event)
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
        reference_id = event["reference_id"]
        logger.info(
            f"Processing payout for : {reference_id}"
        )

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
                await self.handle_initiated_payout(message)
        except asyncio.CancelledError:
            logger.info("Payout consumer cancellation received")
            raise
        finally:
            self.stop()

    def stop(self):
        self.running = False
        logger.info("Stopping payout consumer")
        self.consumer.close()
