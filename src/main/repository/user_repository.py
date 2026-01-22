from sqlalchemy import update, select

from main.config.db_config import AsyncSessionLocal
from main.config.log_config import logger
from main.exception.exception import NotFoundUserException
from main.model.user_base import UserBase


class UserRepository():

    async def create(self, user: UserBase):
        """
        Метод проверяет наличие пользователя в БД.
        Если пользователя нет - добавляет в БД.
        Если пользователь есть - ничего не делается.

        :param user: новый пользователь
        """

        async with AsyncSessionLocal() as session, session.begin():
            result = await session.get(UserBase, user.chat_id)
            # Проверяем, есть ли такой пользователь
            if result is None:
                # Если нет, то создаем
                session.add(user)
                result = user

                logger.info(f"Создан объект в таблице user: id {result.chat_id}", extra={"service": "user_repository"})
            return result


    async def update(self, new_user: UserBase):
        """
        Метод обновляет пользователя

        :param new_user: обновленный пользователь
        """
        async with AsyncSessionLocal() as session, session.begin():
            await session.merge(new_user)

        logger.info(f"Пользователь обновлен: id {new_user.chat_id}", extra={"service": "user_repository"})

        return new_user


    async def delete(self, delete_user):
        """
        Метод удаления пользователя

        :param delete_user: Пользователь, которого необходимо удалить
        """
        async with AsyncSessionLocal() as session, session.begin():
            await session.delete(delete_user)

        logger.info(f"Пользователь удален: id {delete_user.chat_id}", extra={"service": "user_repository"})


    async def get_by_chat_id(self,chat_id: int):
        """
        Метод возвращает пользователя по id в ТГ

        :param chat_id: id пользователя в ТГ
        :return: Пользователь
        """
        async with AsyncSessionLocal() as session, session.begin():
            result = await session.get(UserBase, chat_id)

            if result is None:
                raise NotFoundUserException
            else:
                logger.info(f"Пользователь найден: id {result.chat_id}", extra={"service": "user_repository"})
                return result


    async def get_by_client_chat2desk_id(self, client_chat2desk_id):
        """
        Метод возвращает пользователя по id клиента в системе Chat2Desk

        :param client_chat2desk_id: id клиента в системе Chat2Desk
        :return: Пользователь
        """

        async with AsyncSessionLocal() as session:
            query = select(UserBase).where(UserBase.client_chat2desk_id == client_chat2desk_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user is None:
                raise NotFoundUserException
            else:
                logger.info(f"Пользователь найден: id {user.chat_id}", extra={"service": "user_repository"})
                return user


    async def update_last_sales_msg_datetime_by_chat_id(self, chat_id, datetime):
        """
        Метод обновляет дату последнего сообщения по отделу продаж от пользователя (last_sales_msg_datetime)

        :param chat_id: id пользователя в ТГ
        :param datetime: дата и время последнего сообщения
        """

        async with AsyncSessionLocal() as session:
            query = (update(UserBase)
                     .where(UserBase.chat_id == chat_id)
                     .values(last_sales_msg_datetime = datetime)
                     .execution_options(synchronize_session=False))
            await session.execute(query)
            await session.commit()

        logger.info(f"Дата последнего сообщения по отделу продаж пользователя с id {chat_id} успешно обновлена", extra={"service": "user_repository"})


    async def update_last_support_msg_datetime_by_chat_id(self, chat_id, datetime):
        """
        Метод обновляет дату последнего сообщения по тех. поддержке от пользователя (last_support_msg_datetime)

        :param chat_id: id пользователя в ТГ
        :param datetime: дата и время последнего сообщения
        """

        async with AsyncSessionLocal() as session:
            query = (update(UserBase)
                     .where(UserBase.chat_id == chat_id)
                     .values(last_support_msg_datetime=datetime)
                     .execution_options(synchronize_session=False))
            await session.execute(query)
            await session.commit()

        logger.info(f"Дата последнего сообщения по отделу продаж пользователя с id {chat_id} успешно обновлена", extra={"service": "user_repository"})


    async def get_all_chat_ids(self):
        """
        Метод возвращает список всех chat_id пользователей для рассылки

        :return: Список chat_id
        """

        async with AsyncSessionLocal() as session:
            query = select(UserBase.chat_id)
            result = await session.execute(query)
            chat_ids = result.scalars().all()

            logger.info(f"Получено {len(chat_ids)} chat_id для рассылки", extra={"service": "user_repository"})
            return chat_ids
