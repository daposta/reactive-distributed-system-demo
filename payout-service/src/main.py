from fastapi import FastAPI

from src.routes.payout import router as payout_router




app = FastAPI(
    title="Payout Service API",
    version="1.0.0"
)


app.include_router(payout_router)

@app.get("/health")
async def health():
    return {
        "status": "ok"
    }
