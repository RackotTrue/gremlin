from datetime import date

from main.enum.device_type_enum import DeviceTypeEnum
from main.model.device_base import DeviceBase


class DeviceResponseDTO():

    type: DeviceTypeEnum
    model: str
    serial_number: str
    purchase_date: date


    async def from_device_base(self, device: DeviceBase):

        self.type = device.type
        self.model = device.model
        self.serial_number = device.serial_number
        self.purchase_date = device.purchase_date

    async def get_device_text(self):
        """
        Метод возвращает текстовую информацию об устройстве

        :return: текстовая информация
        """

        text = (f"🔸 Тип устройства: *{self.type.value}*\n"
                f"🔸 Модель устройства: *{self.model}*\n")
                # Серийный номер и дата покупки больше не отображаются

        return text