import logging

from src.core.database import get_db_session
from src.schemas.payout import PayoutOutboxRequest
from src.models.payout import PayoutOutbox

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PayoutOutboxService:
    def __init__(self):
        pass

    async def create(self, payload: PayoutOutboxRequest):
        logger.info("Inside inbox create..")
        new_payout_inbox = PayoutOutbox(**payload.model_dump())
        with get_db_session() as session:
            logger.info("Inside inbox session..")
            session.add(new_payout_inbox)
            session.commit()
            session.refresh(new_payout_inbox)
            logger.info(f"Created new payout inbox")
        return new_payout_inbox

    def find_100_most_recent_new_messages(self):
        with get_db_session() as session:
            logger.info(f"About to query latest 100 inbox entries")
            statement = (session.query(PayoutOutbox)
                         .where(PayoutOutbox.status == "NEW")
                         .order_by(PayoutOutbox.created_at.asc())
                         .limit(100)
                         )
            inbox_data = session.scalars(statement).all()
            logger.info(f"Payout inbox with new entries returned")
            return inbox_data


    def update(self, inbox_id: int, **fields):
        logger.info(
            "Updating payout outbox: id=%s",
            inbox_id,
        )
        with get_db_session() as session:
            outbox =  (session.get(PayoutOutbox, inbox_id))

            if outbox is None:
                raise ValueError(
                    f"Payout outbox for  {inbox_id} not found"
                )

            logger.info(
                "Updating payout outbox: id=%s reference_id=%s",
                outbox.id,
                outbox.payout_reference_id,
            )
            for field, value in fields.items():
                setattr(outbox, field, value)

            session.commit()
            session.refresh(outbox)
            logger.info(
                "Payout outbox: reference_id=%s",
                outbox.payout_reference_id,
            )

        return outbox
