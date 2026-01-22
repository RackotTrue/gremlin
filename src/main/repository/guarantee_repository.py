from sqlalchemy import select, and_

from main.config.db_config import AsyncSessionLocal
from main.config.log_config import logger
from main.exception.exception import NotFoundGuaranteeException
from main.model.guarantee_base import GuaranteeBase

class GuaranteeRepository:


    async def create(self, guarantee: GuaranteeBase):
        """
        Метод добавляет гарантийный план в БД

        :param guarantee: новый гарантийный план
        :return: id созданной гарантии
        """

        async with AsyncSessionLocal() as session, session.begin():
            session.add(guarantee)

        logger.info(f"Создан объект в таблице guarantee: id {guarantee.id}", extra={"service": "guarantee_repository"})
        return guarantee


    async def update(self, new_guarantee: GuaranteeBase):
        """
        Метод обновляет гарантийный план

        :param new_guarantee: обновленная гарантия
        :return: возвращает обновленную гарантию
        """
        async with AsyncSessionLocal() as session, session.begin():
            await session.merge(new_guarantee)

        logger.info(f"Обновлен объект в таблице guarantee: id {new_guarantee.id}", extra={"service": "guarantee_repository"})
        return new_guarantee


    async def get_by_id(self, id: int):
        """
        Метод возвращает гарантийный план по id

        :param id: id гарантийного плана
        :return: Гарантийный план
        """
        async with AsyncSessionLocal() as session, session.begin():
            result = await session.get(GuaranteeBase, id)

            logger.info(f"Найден объект из таблицы guarantee: id {result.id}", extra={"service": "guarantee_repository"})
            return result


    async def get_by_device_id(self, device_id):
        """
        Метод возвращает гарантийные планы по id устройства

        :param device_id: id устройства
        :return: Гарантийные планы
        """
        async with AsyncSessionLocal() as session:
            query = select(GuaranteeBase).where(
                and_(
                    GuaranteeBase.device_id == device_id,
                    GuaranteeBase.is_deleted == False
                )
            )
            result = await session.execute(query)
            guarantees = result.scalars().all()

            if not guarantees:
                raise NotFoundGuaranteeException

            logger.info(f"Найдено {len(guarantees)} гарантий по id устройства в таблице guarantee",
                        extra={"service": "guarantee_repository"})
            return guarantees