from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Date, BigInteger, DateTime, Boolean
from sqlalchemy.orm import relationship

from main.config.db_config import Base
from main.enum.guarantee_enum import GuaranteeTypeEnum


class GuaranteeBase(Base):
    __tablename__ = "guarantee"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    guarantee_type = Column(Enum(GuaranteeTypeEnum), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    created_datetime = Column(DateTime, default=datetime.now)
    updated_datetime = Column(DateTime)
    device_id = Column(BigInteger, ForeignKey("device.id"), index=True, nullable=False)
    price = Column(Integer)
    is_deleted = Column(Boolean, default=False)

    device = relationship("DeviceBase", back_populates="guarantees")


    async def enrich_from_inline_keyboard(self,device_id,
                                          guarantee_type,
                                          guarantee_standard_price,
                                          guarantee_comfort_price=None,
                                          guarantee_premium_price=None
                                          ):
        """
        Метод насыщает сущность параметрами из Inline клавиатуры
        :param device_id:
        :param guarantee_type: Тип гарантийного плана
        :param guarantee_standard_price: Стоимость плана "Стандарт"
        :param guarantee_comfort_price: Стоимость плана "Комфорт"
        :param guarantee_premium_price: Стоимость плана "Премиум"
        """

        self.device_id = int(device_id)

        match str(guarantee_type):
            case "standard":
                self.guarantee_type = GuaranteeTypeEnum.STANDARD
                self.price = int(guarantee_standard_price)
            case "comfort":
                self.guarantee_type = GuaranteeTypeEnum.COMFORT
                self.price = int(guarantee_comfort_price)
            case "premium":
                self.guarantee_type = GuaranteeTypeEnum.PREMIUM
                self.price = int(guarantee_premium_price)
