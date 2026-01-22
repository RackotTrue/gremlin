from sqlalchemy.orm import selectinload

from main.config.db_config import AsyncSessionLocal
from main.config.log_config import logger
from main.exception.exception import NotFoundDeviceException
from main.model.device_base import DeviceBase
from sqlalchemy.future import select
from sqlalchemy import and_


class DeviceRepository():

    async def create(self, device: DeviceBase):
        """
        Метод добавляет новое устройство

        :param device: новое устройство
        :return: созданное устройство
        """

        async with AsyncSessionLocal() as session, session.begin():
            session.add(device)

        logger.info(f"Создан объект в таблице device: id {device.id}", extra={"service": "device_repository"})
        return device


    async def update(self, device: DeviceBase):
        """
        Метод обновляет устройство

        :param device: обновленное устройство
        :return: обновленное устройство
        """

        async with AsyncSessionLocal() as session, session.begin():
            await session.merge(device)

        logger.info(f"Обновлен объект в таблице device: id {device.id}", extra={"service": "device_repository"})
        return device


    async def get_by_id(self, id: int):
        """
        Метод возвращает устройство по id

        :param id: id устройства
        :return: Устройство
        """

        async with AsyncSessionLocal() as session, session.begin():
            result = await session.get(DeviceBase, id)

            if result is None:
                raise NotFoundDeviceException
            else:

                logger.info(f"Найден объект в таблице device: id {result.id}", extra={"service": "device_repository"})
                return result


    async def get_by_serial_number(self, serial_number: str):
        """
        Метод возвращает устройство по серийному номеру

        :param serial_number: серийный номер устройства
        :return: Устройство
        """

        async with AsyncSessionLocal() as session:
            query = select(DeviceBase).where(
                and_(
                    DeviceBase.serial_number == serial_number,
                    DeviceBase.is_deleted == False
                )
            )
            result = await session.execute(query)
            device = result.fetchone()

            if device is None:
                raise NotFoundDeviceException
            else:

                logger.info(f"Найден объект по серийному номеру в таблице device: id {device[0].id}", extra={"service": "device_repository"})
                return device[0]


    async def get_by_serial_number_and_user_id(self, serial_number: str, user_id: int):
        """
        Метод возвращает устройство по серийному номеру и id пользователя

        :param serial_number: серийный номер устройства
        :param user_id: id пользователя
        :return: Устройство
        """

        async with AsyncSessionLocal() as session:
            query = select(DeviceBase).where(
                and_(
                    DeviceBase.serial_number == serial_number,
                    DeviceBase.user_id == user_id,
                    DeviceBase.is_deleted == False
                )
            )
            result = await session.execute(query)
            device = result.fetchone()

            if device is None:
                raise NotFoundDeviceException
            else:

                logger.info(f"Найден объект по серийному номеру и id пользователя в таблице device: id {device[0].id}", extra={"service": "device_repository"})
                return device[0]


    async def get_by_user_id(self, user_id: int):
        """
        Метод возвращает список устройст пользователя

        :param user_id: id пользователя
        :return: Список устройств
        """

        async with AsyncSessionLocal() as session:
            query = select(DeviceBase).where(
                and_(
                    DeviceBase.user_id == user_id,
                    DeviceBase.is_deleted == False
                )
            )
            result = await session.execute(query)
            devices = result.scalars().all()

            if not devices:
                raise NotFoundDeviceException

            logger.info(f"Найдено {len(devices)} устройств по id пользователя в таблице device",
                        extra={"service": "device_repository"})
            return devices


    async def get_with_guarantees_by_id(self, id: int):
        """
        Метод возвращает устройство с подгруженными гарантиями по id.

        :param id: id устройства
        :return: устройство с гарантиями
        """
        async with AsyncSessionLocal() as session:
            query = (
                select(DeviceBase)
                .options(selectinload(DeviceBase.guarantees))
                .where(
                    and_(
                        DeviceBase.id == id,
                        DeviceBase.is_deleted == False
                    )
                )
            )
            result = await session.execute(query)
            device = result.fetchone()

            if not device:
                raise NotFoundDeviceException

            logger.info(
                f"Найден объект c гарантиями в таблице device: id = {id}",
                extra={"service": "device_repository"}
            )

            return device[0]
