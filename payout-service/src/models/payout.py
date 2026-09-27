from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Integer, DateTime, String, Numeric, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

class PayOut(Base):
    __tablename__ = "payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_id: Mapped[str]
    status: Mapped[str]
    # payment_service_id: Mapped[str] = mapped_column(String(100), nullable=True)
    # currency_code: Mapped[str] = mapped_column(String(3), nullable=True)
    # fx_rate: Mapped[float]  = mapped_column(Numeric(precision=10, scale=2), nullable=True)
    # base_amount: Mapped[float] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc),)

class PayoutOutbox(Base):
    __tablename__ = "payouts_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payout_reference_id: Mapped[str] #request_id
    event_type: Mapped[str] = mapped_column(String(10), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)
    status:  Mapped[str] = mapped_column(String(3), index=True, default="PENDING") #new/set/error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
