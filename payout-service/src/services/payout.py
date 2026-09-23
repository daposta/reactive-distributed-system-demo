import base64
import logging
import uuid

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.producer import  message_producer
from src.models.payout import PayOut
# from ..core.database import  get_session
from src.core.settings import  settings
from src.schemas.payout import PayoutResponse, PayoutRequest

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PayOutService:
    def __init__(self, session:Session):
        self.session = session
        self.topic = settings.PAYOUT_TOPIC

    def _generate_auth(self):
        credentials = f"{settings.TAZAPAY_API_KEY}:{settings.TAZAPAY_API_SECRET}"
        encoded = (base64.encode(credentials.encode())).decode()
        return f"Basic {encoded}"

    async def initiate_payout(self, payload: PayoutRequest) -> PayoutResponse:
        print(f"Payload = {payload}")
        request_id = payload.requestId
        logger.info(f"Initiating payout")
        result =  await self.save({
            "reference_id": request_id,
            "status":"INITIATED",
        })
        payload = payload.model_dump()
        await message_producer.send(self.topic, request_id, payload)
        logger.info(f"Payout message sent")
        return result

    async def save(self, payload):
        new_payout = PayOut(**payload)
        self.session.add(new_payout)
        try:
            self.session.commit()
            self.session.refresh(new_payout)
            logger.info(f"Payout saved successfully")
            return new_payout
        except Exception as e:
            self.session.rollback()
            logger.error(f"Payout save error: {e.args}")
            raise e
        finally:
            self.session.close()

    async def get_by_id(self, request_id) -> PayoutResponse:
        statement = (self.session.query(PayOut)
                  .where(PayOut.reference_id == request_id))
        payout = self.session.scalar(statement)
        logger.info(f"Payout with {request_id} returned")
        return payout
