from datetime import datetime

from main.config.log_config import logger
from main.enum.device_type_enum import DeviceTypeEnum
from main.exception.exception import NotFoundDeviceBySerialNumberException, NotFoundDeviceException, \
    DeviceIsRegisteredException
from main.model.device_base import DeviceBase
from main.repository.device_repository import DeviceRepository


class DeviceService():
    """
    Сервис для работы с устройствами.
    Google Sheets верификация отключена - устройства создаются напрямую.
    """

    def __init__(self):
        self._device_repository = DeviceRepository()


    async def get_device(self, device_id: int):
        """
        Метод возвращает устройство по id

        :param device_id: id устройства
        :return: Устройство из БД
        """

        return await self._device_repository.get_by_id(device_id)


    async def get_device_with_guarantee(self, device_id):
        """
        Метод возвращает список устройств с подгруженными гарантиями.

        :param device_id: id устройства
        :return: Устройство с гарантиями
        """

        return await self._device_repository.get_with_guarantees_by_id(device_id)


    async def get_device_by_serial_number(self, serial_number):
        """
        Метод возвращает устройство по серийному номеру

        :param serial_number: серийный номер устройства
        :return: устройство из БД
        """

        return await self._device_repository.get_by_serial_number(serial_number)


    async def get_device_by_serial_number_and_user_id(self, serial_number, user_id):
        """
        Метод возвращает устройство по серийному номеру и id пользователя

        :param serial_number: cерийный номер устройства
        :param user_id: id пользователя
        :return: устройство из БД
        """

        return await self._device_repository.get_by_serial_number_and_user_id(serial_number, user_id)


    async def get_devices_by_user_id(self, user_id):
        """
        Метод возвращает все зарегистрированные устройства пользователя

        :param user_id: id пользователя
        :return: Список устройств
        """

        return await self._device_repository.get_by_user_id(user_id)


    async def get_device_or_identify_and_create(self, serial_number, user_id):
        """
        Метод ищет устройство в БД и создает новое, если не находит

        :param serial_number: cерийный номер устройства
        :param user_id: id пользователя
        :return: устройство из БД
        """

        try:
            # Ищем устройство в БД
            device: DeviceBase = await self.get_device_by_serial_number(serial_number)

            # Проверяем что оно принадлежит текущему пользователю:
            if device.user_id == user_id:
                return device
            # Если нет - кидаем исключение
            else:
                raise DeviceIsRegisteredException

        except NotFoundDeviceException:
            # Создаем устройство без верификации через Google
            return await self.create_device_simple(serial_number, user_id)


    async def create_device_simple(self, serial_number=None, user_id=None):
        """
        Создание устройства без верификации (Google Sheets отключен)

        :param serial_number: серийный номер устройства (опционально)
        :param user_id: id пользователя
        :return: созданное устройство
        """

        device = DeviceBase()
        device.serial_number = serial_number
        device.user_id = user_id
        device.type = DeviceTypeEnum.UNKNOWN

        return await self.__create_device(device)


    async def identify_device_and_create(self, serial_number, user_id):
        """
        Создание устройства (верификация через Google отключена)

        :param serial_number: серийный номер устройства
        :param user_id: id пользователя
        :return: устройство
        """

        return await self.create_device_simple(serial_number, user_id)


    async def identify_device_and_update(self, device_id, serial_number):
        """
        Обновление серийного номера устройства

        :param device_id: id устройства
        :param serial_number: серийный номер устройства
        :return: обновленное устройство
        """

        device = await self.get_device(device_id)
        device.serial_number = serial_number

        return await self.update_device(device)


    async def get_device_from_google(self, serial_number, device_id=None) -> DeviceBase:
        """
        ОТКЛЮЧЕНО: Google Sheets не используется.
        Метод оставлен для совместимости API.

        :param serial_number: серийный номер устройства
        :raises NotFoundDeviceBySerialNumberException: всегда
        """

        logger.warning(f"Попытка поиска устройства в Google Sheets (отключено): {serial_number}")
        raise NotFoundDeviceBySerialNumberException(serial_number)


    async def get_device_dto_from_google(self, serial_number):
        """
        ОТКЛЮЧЕНО: Google Sheets не используется.
        Метод оставлен для совместимости API.

        :param serial_number: серийный номер устройства
        :raises NotFoundDeviceBySerialNumberException: всегда
        """

        logger.warning(f"Попытка поиска устройства DTO в Google Sheets (отключено): {serial_number}")
        raise NotFoundDeviceBySerialNumberException(serial_number)


    async def create_device_from_device_google_dto(self, device_dto, user_id):
        """
        ОТКЛЮЧЕНО: Google Sheets не используется.
        Используйте create_device_simple вместо этого метода.

        :raises NotImplementedError: всегда
        """

        raise NotImplementedError("Google Sheets отключен. Используйте create_device_simple()")


    async def __create_device(self, new_device: DeviceBase):
        """
        Метод принимает на вход объект DeviceBase и создает в БД устройство

        :param new_device: новое устройство
        :return: созданное устройство
        """

        return await self._device_repository.create(new_device)


    async def update_device(self, update_device: DeviceBase):
        """
        Метод принимает на вход объект DeviceBase и обновляет в БД устройство

        :param update_device: обновленное устройство
        :return: обновленное устройство
        """

        update_device.updated_datetime = datetime.now()
        return await self._device_repository.update(update_device)


    async def delete_device(self, device: DeviceBase):
        """
        Метод проставляет устройству признак is_deleted = True
        :param device: Устройство
        :return: Обновленное устройство
        """

        device.is_deleted = True

        return await self.update_device(device)
