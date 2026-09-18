from pydantic import BaseModel, Field


class TazapayBankCode(BaseModel):
    swift_code: str
    aba_code: str

class TazapayBank(BaseModel):
    bank_codes: TazapayBankCode  #= Field(alias="bankCodes")
    account_number: str
    bank_name: str
    country: str
    currency: str
    branch_name: str

    model_config = {
        "populate_by_name": True
    }

class TazapayDestinationDetail(BaseModel):
    destination_type: str = Field(alias="type")
    bank: TazapayBank

    model_config = {
        "populate_by_name": True
    }


class TazapayAddress(BaseModel):
    line1: str
    city: str
    state: str
    country: str
    postal_code: str

class TazapayBeneficiaryDetails(BaseModel):
    name: str
    type: str
    address: TazapayAddress
    destination_details: TazapayDestinationDetail


class TazapayServiceRequest(BaseModel):
    reference_id: str
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    purpose: str = Field(..., min_length=3, )
    transaction_description: str = Field(..., min_length=3, )
    beneficiary_details: TazapayBeneficiaryDetails



class Amount(BaseModel):
    amount: float
    currency: str

class PayoutFXTransactionResponse(BaseModel):
    exchange_rate: float
    final_amount: Amount = Field(alias="final")
    initial_amount: Amount = Field(alias="initial")
    id: str


class TazapayPayoutData(BaseModel):
    id: str
    reference_id: str
    amount: float
    currency: str
    type: str
    balance_transaction: str
    beneficiary: str
    beneficiary_details: TazapayBeneficiaryDetails
    # destination_details: TazapayDestinationDetail
    # bank: TazapayBank
    payout_fx_transaction: PayoutFXTransactionResponse

class TazapayServiceResponse(BaseModel):
    status: str
    message: str
    data: TazapayPayoutData
