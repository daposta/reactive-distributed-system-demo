from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class BankCode(BaseModel):
    ifsc_code: str

class BankRequest(BaseModel):
    bank_code: BankCode
    account_number: str
    bank_name: str
    country: str
    currency: str

class DestinationDetailRequest(BaseModel):
    destination_type: str
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
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    purpose: str = Field(..., min_length=3, )
    transaction_description: str = Field(..., min_length=3, )
    beneficiary_details: BeneficiaryDetails
    destination_details: DestinationDetailRequest

class PayoutResponse(BaseModel):
    requestId: str
    status: str
    initiatedAt: datetime
