from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, BigInteger, DateTime, Date, Boolean, false
from sqlalchemy.orm import relationship

from main.config.db_config import Base
from main.enum.device_type_enum import DeviceTypeEnum


class DeviceBase(Base):
    __tablename__ = "device"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(Enum(DeviceTypeEnum), nullable=True, default=DeviceTypeEnum.UNKNOWN)
    model = Column(String)
    serial_number = Column(String)
    created_datetime = Column(DateTime, default=datetime.now)
    updated_datetime = Column(DateTime)
    purchase_date = Column(Date)
    user_id = Column(BigInteger, ForeignKey("user.chat_id"), index=True, nullable=False)
    is_deleted = Column(Boolean, default=False)

    user = relationship('UserBase', back_populates="devices")
    guarantees = relationship("GuaranteeBase", back_populates="device")


    async def enrich_from_dict(self, dict):
        """
        Метод донасыщает объект DeviceBase по словарю, полученному из Google таблиц

        :param dict: словарь из Google таблиц
        """
        self.model = dict["model"]
        self.type: DeviceTypeEnum = DeviceTypeEnum(dict["type"])


    async def enrich_from_device_google_dto(self, device_dto):
        """
        Метод донасыщает объект DeviceBase из объекта DeviceGoogleTableDTO

        :param device_dto: объект DeviceGoogleTableDTO
        """

        self.model = device_dto.model
        self.type = device_dto.type
        self.serial_number = device_dto.serial_number