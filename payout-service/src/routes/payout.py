

from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session

from ..schemas.payout import PayoutRequest, PayoutResponse
from ..services.payout import PayOutService
from ..core.database import get_session

router = APIRouter(prefix="/payout")

@router.post("", response_model=PayoutResponse)
async def make_payout(
        payload: PayoutRequest,
        session: Session = Depends(get_session),
):
    payout_service = PayOutService(session)
    data = payload.model_dump()
    result = await payout_service.initiate_payout(data)
    return result


@router.get("/{response_id}", response_model=PayoutResponse)
async def get_payout(response_id: str):
    return await payout_service.get_by_id(response_id)
