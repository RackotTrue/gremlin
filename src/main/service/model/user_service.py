from datetime import datetime, timezone

from main.config.log_config import logger
from main.model.user_base import UserBase
from main.repository.user_repository import UserRepository


class UserService():

    def __init__(self):
        self._user_repository = UserRepository()


    async def create_user(self, chat_id, username, full_name):
        """
        Метод добавления пользователя

        :param chat_id: id пользователя
        :param username: Никнейм пользователя
        :param full_name: ФИО пользователя
        """

        new_user = UserBase()
        new_user.chat_id = chat_id
        new_user.username = username
        new_user.full_name_in_tg = full_name
        return await self._user_repository.create(new_user)


    async def update_user(self, user: UserBase):
        """
        Метод обновления пользователя

        :param user: обновленная модель пользователя
        """
        user.updated_datetime = datetime.now()

        return await self._user_repository.update(user)


    async def get_user(self, chat_id) -> UserBase:
        """
        Метод возвращает информацию по пользователю

        :param chat_id: id пользователя
        :return: пользователь
        """

        return await self._user_repository.get_by_chat_id(chat_id)


    async def set_name(self, chat_id, name):
        """
        Метод задает имя пользователя

        :param chat_id: id пользователя
        :param name: имя
        :return: обновленная модель пользователя
        """

        update_user =  await self.get_user(chat_id)
        update_user.name = name

        return await self.update_user(update_user)


    async def set_surname(self, chat_id, surname):
        """
        Метод задает фамилию пользователя

        :param chat_id: id пользователя
        :param surname: фамилия
        :return: обновленная модель пользователя
        """

        update_user =  await self.get_user(chat_id)
        update_user.surname = surname

        return await self.update_user(update_user)


    async def set_phone(self, chat_id, phone):
        """
        Метод задает телефон пользователя

        :param chat_id: id пользователя
        :param phone: телефон
        :return: обновленная модель пользователя
        """

        update_user =  await self.get_user(chat_id)
        update_user.phone = phone

        return await self.update_user(update_user)


    async def set_email(self, chat_id, email):
        """
        Метод задает email пользователя

        :param chat_id: id пользователя
        :param email: email
        :return: обновленная модель пользователя
        """

        update_user =  await self.get_user(chat_id)
        update_user.email = email

        return await self.update_user(update_user)


    async def get_or_create_support_assist_thread_id(self, chat_id) -> str:
        """
        Метод проверяет, есть ли id потока для ассистента тех. поддержки.
        Если нет, то создает и сохраняет в БД

        :param chat_id: id пользователя
        :return: id потока для ассистента тех. поддержки
        """

        user = await self.get_user(chat_id)

        if user.support_assist_thread_id is None:

            thread_id = await create_thread_for_assistant()
            user.support_assist_thread_id = thread_id
            new_user = await self.update_user(user)

            logger.debug("")
            return new_user.support_assist_thread_id

        else:
            return user.support_assist_thread_id


    async def get_or_create_sales_assist_thread_id(self, chat_id) -> str:
        """
        Метод проверяет, есть ли id потока для ассистента отдела продаж
        Если нет, то создает и сохраняет в БД

        :param chat_id: id пользователя
        :return: id потока для ассистента отдела продаж
        """

        user = await self.get_user(chat_id)

        if user.sales_assistant_thread_id is None:

            thread_id = await create_thread_for_assistant()
            user.sales_assistant_thread_id = thread_id
            new_user = await self.update_user(user)

            return new_user.sales_assistant_thread_id

        else:
            return user.sales_assistant_thread_id


    async def clear_support_assist_thread_id(self, user: UserBase):
        """
        Метод отчищает связь потока и пользователя (проставляет Null в столбец support_assist_thread_id)
        :param user: Пользователь
        """

        user.support_assist_thread_id = None

        await self.update_user(user)


    async def clear_sales_assist_data(self, user: UserBase):
        """
        Метод отчищает связь потока и пользователя (проставляет Null в столбец sales_assistant_thread_id)
        :param user: Пользователь
        """

        user.sales_assistant_thread_id = None
        user.last_sales_msg_datetime = None

        await self.update_user(user)


    async def set_last_sales_msg_datetime(self, user_id: int):
        """
        Метод задает дату и время последнего сообщения по отделу продаж от пользователя.
        Проставляет текущую

        :param user_id: id пользователя
        """

        now = datetime.now(timezone.utc)

        await self._user_repository.update_last_sales_msg_datetime_by_chat_id(user_id, now)


    async def set_last_support_msg_datetime(self, user_id: int):
        """
        Метод задает дату и время последнего сообщения по тех. поддержке от пользователя.
        Проставляет текущую

        :param user_id: id пользователя
        """

        now = datetime.now(timezone.utc)

        await self._user_repository.update_last_support_msg_datetime_by_chat_id(user_id, now)


    async def get_user_by_client_chat2desk_id(self, client_chat2desk_id):
        """
        Метод возвращает пользователя по id клиента в Chat2Desk

        :param client_chat2desk_id: id клиента в Chat2Desk
        :return: Пользователь
        """

        user: UserBase = await self._user_repository.get_by_client_chat2desk_id(client_chat2desk_id)

        return user


    async def is_completed_profile(self, user: UserBase):
        """
        Метод определяет заполнен ли профиль

        :param user: пользователь
        :return: True/False
        """

        if ((user.name is not None)
                and (user.surname is not None)
                and (user.phone is not None)
                and (user.email is not None)):

            return True

        else:
            return False


    async def set_city(self, chat_id, city):
        """
        Метод задает город/регион пользователя

        :param chat_id: id пользователя
        :param city: город/регион
        :return: обновленная модель пользователя
        """

        update_user = await self.get_user(chat_id)
        update_user.city = city

        return await self.update_user(update_user)


    async def set_order_source(self, chat_id, order_source):
        """
        Метод задает источник заказа

        :param chat_id: id пользователя
        :param order_source: источник заказа
        :return: обновленная модель пользователя
        """

        update_user = await self.get_user(chat_id)
        update_user.order_source = order_source

        return await self.update_user(update_user)


    async def set_pd_consent(self, chat_id):
        """
        Метод устанавливает согласие на обработку ПДн

        :param chat_id: id пользователя
        :return: обновленная модель пользователя
        """

        update_user = await self.get_user(chat_id)
        update_user.pd_consent = True
        update_user.pd_consent_datetime = datetime.now()

        return await self.update_user(update_user)


    async def set_marketing_consent(self, chat_id):
        """
        Метод устанавливает согласие на маркетинговые коммуникации

        :param chat_id: id пользователя
        :return: обновленная модель пользователя
        """

        update_user = await self.get_user(chat_id)
        update_user.marketing_consent = True
        update_user.marketing_consent_datetime = datetime.now()

        return await self.update_user(update_user)








