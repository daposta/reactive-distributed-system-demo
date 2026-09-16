from decimal import Decimal

from pydantic import BaseModel


class PayInitiatedEvent(BaseModel):
    reference_id: str
    amount: Decimal
    currency: str
    purpose: str
    transaction_description: str
