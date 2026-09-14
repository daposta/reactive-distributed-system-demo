import base64
import logging
import uuid

from fastapi import Depends
from sqlalchemy.orm import Session

from ..core.producer import  message_producer
from ..models.payout import PayOut
from ..core.database import  get_session
from ..core.settings import  settings
from ..schemas.payout import PayoutResponse

class PayOutService:
    def __init__(self, session:Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.topic = settings.PAYOUT_TOPIC

    def _generate_auth(self):
        credentials = f"{settings.TAZAPAY_API_KEY}:{settings.TAZAPAY_API_SECRET}"
        encoded = (base64.encode(credentials.encode())).decode()
        return f"Basic {encoded}"

    async def initiate_payout(self, payload) -> PayoutResponse:
        request_id = str(uuid.uuid4())
        self.logger.info(f"Initiating payout")
        result =  await self.save({
            "reference_id": request_id,
            "status":"INITIATED",
        })
        await message_producer.send_payout(self.topic, request_id, payload)
        self.logger.info(f"Payout message sent")
        return result

    async def save(self, payload):
        new_payout = PayOut(**payload)
        self.session.add(new_payout)
        try:
            self.session.commit()
            self.session.refresh(new_payout)
            self.logger.info(f"Payout saved successfully")
            return new_payout
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Payout save error: {e.args}")
            raise e
        finally:
            self.session.close()

    async def get_by_id(self, request_id) -> PayoutResponse:
        print("innie....")
        statement = (self.session.query(PayOut)
                  .where(PayOut.reference_id == request_id))
        payout = self.session.scalar(statement)
        self.logger.info(f"Payout with {request_id} returned")
        return payout
