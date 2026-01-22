from aiogram import *
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Router

from main.middleware.middleware import ChatActionMiddleware
from main.utils import send_message_from_msg, send_message_from_call

###
###### Хендлер для работы с Акциями и предложениями
####
##


router = Router()
router.message.middleware(ChatActionMiddleware())


#@router.message(Command('promotion'))
async def get_promotion(message: Message):
    """
    Метод возвращает ссылку на акции

    :param message: Сообщение от пользователя
    """
    # TODO: Заменить ссылку на сайт ТОП ШИН 24
    text = "Самые актуальные и лучшие предложения ждут Вас! Обращайтесь к нам за подробностями."

    await send_message_from_msg(message=message,
                                text=text)

