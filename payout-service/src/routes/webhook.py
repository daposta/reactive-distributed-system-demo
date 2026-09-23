from fastapi import APIRouter
from src.services.webhook import WebhookService
from src.schemas.webhook import TazapayWebhook

router = APIRouter(prefix="/webhook")


@router.post("/tazapay", status_code=200)
async def webhook(payload:TazapayWebhook):
    await WebhookService().handle_tazapay_webhook(payload)
    return {"status": "success"}
