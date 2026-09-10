

from fastapi import APIRouter, Response
from ..schemas.payout import PayoutRequest, PayoutResponse
from ..services.payout import payout_service

router = APIRouter(prefix="/payout")

@router.post("", response_model=PayoutResponse)
def make_payout(payload: PayoutRequest):
    #create record in db with status
    #publish event to topic payout_initiate
    data = payload.model_dump()
    result = await payout_service.initiate_payout(data)
    await payout_service.save(data)
    return result
