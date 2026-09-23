

from fastapi import APIRouter, Response, Depends, HTTPException
from sqlalchemy.orm import Session

from src.schemas.payout import PayoutRequest, PayoutResponse
from src.services.payout import PayOutService
from src.core.database import get_session

router = APIRouter(prefix="/payouts")

@router.post("", response_model=PayoutResponse)
async def make_payout(
        payload: PayoutRequest,
        session: Session = Depends(get_session),
):
    payout_service = PayOutService(session)
    # data = payload.model_dump()
    result = await payout_service.initiate_payout(payload)
    return result


@router.get("/{reference_id}", response_model=PayoutResponse)
async def get_payout(reference_id: str,
                     session: Session = Depends(get_session),
                     ):
    payout_service = PayOutService(session)
    result = await payout_service.get_by_id(reference_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Payout reference:{reference_id} not found ")
    return result
