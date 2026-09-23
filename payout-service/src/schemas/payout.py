
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class BankCode(BaseModel):
    swift_code: str
    aba_code: str

class BankRequest(BaseModel):
    bank_codes: BankCode
    account_number: str
    bank_name: str
    country: str
    currency: str
    branch_name: str

class DestinationDetailRequest(BaseModel):
    type: str
    bank: BankRequest


class Address(BaseModel):
    line1: str
    city: str
    state: str
    country: str
    postal_code: str

class BeneficiaryDetails(BaseModel):
    name: str
    type: str
    address: Address

class PayoutRequest(BaseModel):
    requestId: str
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    purpose: str = Field(..., min_length=3, )
    transaction_description: str = Field(..., min_length=3, )
    beneficiary_details: BeneficiaryDetails
    destination_details: DestinationDetailRequest

class PayoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    requestId: str  = Field(alias="reference_id")
    status: str
    initiatedAt: datetime = Field(alias="created_at")
