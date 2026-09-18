
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class EventBankCode(BaseModel):
    swift_code: str
    aba_code: str

class EventBank(BaseModel):
    bank_codes: EventBankCode
    account_number: str
    bank_name: str
    country: str
    currency: str
    branch_name:str

class EventDestinationDetail(BaseModel):
    destination_type: str = Field(alias="type")
    bank: EventBank

    model_config = {
        "populate_by_name": True
    }


class EventAddress(BaseModel):
    line1: str
    city: str
    state: str
    country: str
    postal_code: str

class EventBeneficiaryDetails(BaseModel):
    name: str
    type: str
    address: EventAddress


class PayoutEvent(BaseModel):
    reference_id: str
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    purpose: str = Field(..., min_length=3, )
    transaction_description: str = Field(..., min_length=3, )
    beneficiary_details: EventBeneficiaryDetails
    destination_details: EventDestinationDetail


# class PayoutResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True, populate_by_name=True)
#
#     requestId: str  = Field(alias="reference_id")
#     status: str
#     initiatedAt: datetime = Field(alias="created_at")
#     payment_service_id: str
#     currency_code: str
#     fx_rate: Decimal
#     base_amount: int
