"""Модель задачи генерации видео (fal.ai VEED Fabric 1.0)."""
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from main.config.db_config import Base


class VideoJobBase(Base):
    """
    Задача генерации видео-открытки.
    Статусы: queued -> processing -> done / failed.
    """

    __tablename__ = "video_job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lead_id = Column(BigInteger, ForeignKey("lead.id"), index=True, nullable=False)
    type = Column(String, nullable=False)  # welcome | birthday
    hero_id = Column(String, nullable=False)  # ID героя из heroes.yml
    text = Column(Text, nullable=False)  # Текст, который герой произносит
    fal_request_id = Column(String, nullable=True, index=True)  # request_id от fal.ai API
    status = Column(String, nullable=False, default="queued")  # queued | processing | done | failed
    result_url = Column(String, nullable=True)  # Ссылка на готовое видео
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    lead = relationship("LeadBase", back_populates="video_jobs")
