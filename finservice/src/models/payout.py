from datetime import datetime

from sqlalchemy import Integer, DateTime, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

class PayOut(Base):
    __tablename__ = "payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_id: Mapped[str]
    status: Mapped[str]
    payment_service_id: Mapped[str] = mapped_column(String(100), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=True)
    fx_rate: Mapped[float]  = mapped_column(Numeric(precision=10, scale=2), nullable=True)
    base_amount: Mapped[float] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
