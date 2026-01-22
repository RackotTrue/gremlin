from main.dto.device_response_dto import DeviceResponseDTO
from main.enum.device_type_enum import DeviceTypeEnum
from main.model.device_base import DeviceBase


class DeviceGoogleTableDTO(DeviceResponseDTO):

    id: int
    guarantee_standard_price: int
    guarantee_comfort_price: int
    guarantee_premium_price: int


    async def from_dict(self,dict):
        self.model = dict["model"]
        self.type: DeviceTypeEnum = DeviceTypeEnum(dict["type"])
        self.guarantee_standard_price = int(dict["guarantee_standard_price"])
        self.guarantee_comfort_price = int(dict["guarantee_comfort_price"])
        self.guarantee_premium_price = int(dict["guarantee_premium_price"])


    async def from_device_base(self, device: DeviceBase):

        self.id = device.id
        await super().from_device_base(device)
