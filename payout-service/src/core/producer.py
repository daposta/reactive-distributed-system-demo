import json
import logging
from datetime import datetime, timezone

from confluent_kafka import Producer
from ..schemas.payout import PayoutResponse


class MessageProducer:
    def __init__(self):
        self.conf = {
            "bootstrap.servers": "127.0.0.1:29092",
            "acks": "all",
            "retries": 5,
            "enable.idempotence": True,
            "client.id": "payout-producer",  # Added for better tracking
            "delivery.timeout.ms": 120000,   # Added for robustness
            "request.timeout.ms": 30000,     # Added for robustness

        }
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
        level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.producer = Producer(self.conf)


    def _delivery_report(self, err, msg):
        if err:
            self.logger.error(f'❌ Delivery failed: {err}')
        else:
            self.logger.info(f'✅ Delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

    def send_payout(self, topic, request_id, payload):
        self.producer.produce(topic=topic, value=json.dumps(payload).encode("utf-8"), callback=self._delivery_report)
        self.producer.poll(0)
        return PayoutResponse(
            requestId=str(request_id), status="PENDING", initiatedAt=datetime.now(timezone.utc)
        )


message_producer = MessageProducer()
