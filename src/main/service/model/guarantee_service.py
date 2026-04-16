from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from main.config.dynaconf_config import config_setting
from main.enum.guarantee_enum import GuaranteeTypeEnum, GUARANTEE_PERIOD_LENGTH_STANDARD
from main.exception.exception import NotFoundGuaranteeException
from main.model.device_base import DeviceBase
from main.model.guarantee_base import GuaranteeBase
from main.repository.guarantee_repository import GuaranteeRepository
from main.service.integration.bitrix24_service import *


class GuaranteeService:

    def __init__(self):
        self._guarantee_repository = GuaranteeRepository()


    async def create_guarantee(self, new_guarantee: GuaranteeBase):
        """
        Метод добавления гарантийного плана

        :param new_guarantee: гарантийный план
        :return: созданный гарантийный план
        """

        return await self._guarantee_repository.create(new_guarantee)


    async def create_guarantee_with_period(self, guarantee: GuaranteeBase, device: DeviceBase):
        """
        Метод создает гарантийный план и высчитывает дату начал действия и окончание

        :param guarantee: Гарантийный план
        :param device: Устройство
        :return: Созданный гарантийный план
        """

        # Если гарантийный план "Стандарт" - используем дату покупки или подставляем текущую дату
        if guarantee.guarantee_type == GuaranteeTypeEnum.STANDARD:
            # Проверяем, что purchase_date существует и является датой
            if device.purchase_date is not None and isinstance(device.purchase_date, date):
                guarantee.start_date = device.purchase_date
            else:
                guarantee.start_date = date.today()
            
            # Вычисляем дату окончания гарантии
            guarantee.end_date = guarantee.start_date + relativedelta(months=GUARANTEE_PERIOD_LENGTH_STANDARD)
        else:
            # Подстраховка для других типов: выставляем старт и конец, если их нет
            if guarantee.start_date is None or not isinstance(guarantee.start_date, date):
                guarantee.start_date = date.today()
            
            if guarantee.end_date is None or not isinstance(guarantee.end_date, date):
                guarantee.end_date = guarantee.start_date

        return await self.create_guarantee(guarantee)


    async def create_guarantee_deal_in_bitrix24(self, guarantee_dto: GuaranteeCreateBitrix24RequestDTO):
        """
        Находим и обновляем или создаем Контакт в системе Битрикс24 и создаем Сделку

        :param guarantee_dto: ДТО гарантийного плана для создания в Битрикс24
        :return: id Сделки из системы Битрикс24
        """
        if not getattr(getattr(config_setting, "BITRIX24", None), "ENABLED", True):
            return None  # Заглушка: Bitrix отключён

        # Проверяем, есть ли контакт в системе Битрикс24.

        user:UserBase = guarantee_dto.user

        try:
            # Если есть - то обновляем имеющийся
            contact_id = await get_contact_by_phone(user.phone)
            await update_contact(bitrix_contact_id=contact_id,
                                 user=user)
        except NotFoundContactInBitrix24Exception:
            # Если нет, то создаем новый
            contact_id = await create_contact(user)

        # Создаем Сделку

        return await create_guarantee_deal(guarantee_dto=guarantee_dto,
                                           contact_id=contact_id)


    async def update_guarantee(self, update_guarantee: GuaranteeBase):
        """
        Метод принимает на вход объект GuaranteeBase и обновляет в БД гарантийный план

        :param update_guarantee: обновленный гарантийный план
        :return: обновленный гарантийный план
        """

        update_guarantee.updated_datetime =  datetime.now()
        return await self._guarantee_repository.update(update_guarantee)


    async def get_guarantees_by_device_id(self, device_id):
        """
        Метод возвращает гарантийные планы по id устройства

        :param device_id: id устройства
        :return: Гарантийные планы
        """

        return await self._guarantee_repository.get_by_device_id(device_id)


    async def delete_guarantees_by_device_id(self, device_id):
        """
        Метод проставляет признак is_deleted = True всем найденным гарантийным планам по device_id

        :param device_id: id устройства
        """

        try:
            guarantees = await self.get_guarantees_by_device_id(device_id)

            for guarantee in guarantees:
                guarantee.is_deleted = True
                await self.update_guarantee(guarantee)

        except NotFoundGuaranteeException:
            pass

