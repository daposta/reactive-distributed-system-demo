from datetime import date

from fastapi import FastAPI
from pydantic import BaseModel
from src.routes.payout import router as payout_router

app = FastAPI(
    title="Payout Service API",
    version="1.0.0"
)


app.include_router(payout_router)
