from aiogram import *
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Router

from main.middleware.middleware import ChatActionMiddleware
from main.utils import send_message_from_msg


###
###### Хендлер для работы с Сервисным центром
####
##


router = Router()
router.message.middleware(ChatActionMiddleware())


async def technical_support_department(message: Message):
    """
    Метод возвращает информацию по технической поддержке

    :param message: Сообщение от пользователя
    """
    text = 'В случае возникновения неполадок свяжитесь с нами: *89858546153*'

    await send_message_from_msg(message=message,
                                text=text)
