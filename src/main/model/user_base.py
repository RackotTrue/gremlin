from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, BigInteger, Boolean
from sqlalchemy.orm import relationship

from main.config.db_config import Base

class UserBase(Base):
    __tablename__ = "user"

    chat_id = Column(BigInteger, primary_key=True, autoincrement=False, index=True)
    username = Column(String)
    full_name_in_tg = Column(String)
    surname = Column(String)
    name = Column(String)
    created_datetime = Column(DateTime, default=datetime.now)
    updated_datetime = Column(DateTime)
    email = Column(String)
    phone = Column(String)
    
    # Новые поля
    city = Column(String)  # Город/регион
    order_source = Column(String)  # Источник заказа (Ozon, WB, YM, Avito, Розница)
    
    # Согласия
    pd_consent = Column(Boolean, default=False)  # Согласие на обработку ПДн
    pd_consent_datetime = Column(DateTime)  # Дата согласия на ПДн
    marketing_consent = Column(Boolean, default=False)  # Согласие на маркетинг
    marketing_consent_datetime = Column(DateTime)  # Дата согласия на маркетинг
    
    support_assist_thread_id = Column(String)
    sales_assistant_thread_id = Column(String)
    last_support_msg_datetime = Column(DateTime(timezone=True))
    last_sales_msg_datetime = Column(DateTime(timezone=True))
    client_chat2desk_id = Column(BigInteger, index=True)

    devices = relationship("DeviceBase", back_populates="user")