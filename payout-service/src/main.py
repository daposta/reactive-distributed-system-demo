from fastapi import FastAPI

from src.routes.payout import router as payout_router
from src.routes.webhook import router as webhook_router

app = FastAPI(
    title="Payout Service API",
    version="1.0.0"
)

app.include_router(payout_router)
app.include_router(webhook_router)

@app.get("/health")
async def health():
    return {
        "status": "ok"
    }
