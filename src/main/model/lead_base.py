"""Модель лида (активация по QR) для сценария видео-открытки."""
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship

from main.config.db_config import Base


class LeadBase(Base):
    """Лид: покупатель прошёл QR, заполнил форму, привязан к источнику (seller/sku/utm)."""

    __tablename__ = "lead"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_chat_id = Column(BigInteger, ForeignKey("user.chat_id"), index=True, nullable=False)
    buyer_name = Column(String)
    phone = Column(String)
    child_name = Column(String)
    child_birthdate = Column(Date, nullable=True)
    seller_id = Column(String)
    campaign_id = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    utm_source = Column(String, nullable=True)
    utm_medium = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    video_jobs = relationship("VideoJobBase", back_populates="lead")
