from sqlalchemy.util import await_only

from main.enum.guarantee_enum import GuaranteeTypeEnum
from main.model.device_base import DeviceBase
from main.model.guarantee_base import GuaranteeBase
from main.model.user_base import UserBase


class GuaranteeCreateBitrix24RequestDTO():

    def __init__(self, guarantee: GuaranteeBase, device: DeviceBase, user: UserBase):

        self.type = guarantee.guarantee_type.value
        self.price = guarantee.price
        self.device = device
        self.user = user


