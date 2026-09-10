import logging
import uuid
from ..core.producer import  message_producer
from ..models.payout import PayOut
from ..core.database import  settings

class PayOutService:
    def __init__(self):
        self.session = settings
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    async def initiate_payout(self, payload):
        topic = "payout_initiated"
        request_id = uuid.uuid4()
        result = message_producer.send_payout(topic, request_id, payload)
        print(f"===result==== {result}")
        self.logger.info(f"Payout message sent")
        return result

    async def save(self, payload):
        new_payout = PayOut(**payload)
        self.session.add(new_payout)
        try:
            self.session.commit()
            self.logger.info(f"Payout saved successfully")
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Payout save error: {e.args}")
            raise e
        finally:
            self.session.close()


payout_service = PayOutService()
