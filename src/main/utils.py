import asyncio
import re
import requests
from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from email_validator import validate_email, EmailNotValidError
from datetime import datetime

from main.config.dynaconf_config import security_setting
from main.config.bot_config import bot
from main.config.log_config import logger
from main.keyboard.main_menu_keyboard import cancel_action_keyboard
from main.exception.exception import *
from main.enum.main_menu_enum import *


async def set_bot_commands(bot: Bot):
    """
    Создает кнопку 'Меню' с командами

    :param bot: Бот
    """

    commands = [
        BotCommand(command="guarantee", description=MainMenuButtonEnum.GUARANTEE.value),
        BotCommand(command="device_info", description=MainMenuButtonEnum.DEVICE_INFO.value),
        BotCommand(command="technical_support_department", description=MainMenuButtonEnum.TECHNICAL_SUPPORT_DEPARTMENT.value),
        BotCommand(command="promotion", description=MainMenuButtonEnum.PROMOTION.value),
        BotCommand(command="support", description="Техподдержка - @RackotXO"),
    ]
    await bot.set_my_commands(commands)


async def is_admin(user_id):
    """
    Метод проверки на то, что пользователь является Админом

    :param user_id: id пользователя
    """

    if user_id not in security_setting.IDS:
        raise IsNotAdminException


###
###### Работа с HTTP запросами
####
##


def send_request(type, url, headers=None, cookies=None, json=None, param=None):
    """
    Метод отправляет HTTP запрос

    :param type: тип HTTP запроса:
                    - GET
                    - POST
                    - PUT
    :param url: url HTTP запроса
    :param headers: headers HTTP запроса
    :param cookies: cookies HTTP запроса
    :param json: тело HTTP запроса в формате json
    :param param: параметры для HTTP запроса

    :return: Ответ запроса - объект класса Response
    """

    match type:
        case "GET":
            response = requests.get(url,
                                    headers=headers,
                                    cookies=cookies,
                                    params=param)
        case "POST":
            response = requests.post(url,
                                     headers=headers,
                                     cookies=cookies,
                                     json=json)
        case "PUT":
            response = requests.put(url,
                                    headers=headers,
                                    cookies=cookies,
                                    json=json)
        case _:
            raise Exception(f"Указан не верный тип запроса! Должен быть один из следующих: GET, POST, PUT!")

    #return response
    if response.status_code == 200:
        return response
    else:
        raise Exception(f"Запрос {url} вполнен с ошибкой!"
                    f"\nКод ошибки: {response.status_code}\n"
                        f"Описание ошибки: {response.text}")


###
###### Работа с сообщениями
####
##


async def send_message_as_human_from_msg(message: Message, text, keyboard=None, sec: int = 3):
    """
    Метод отвеччает с задержкой по времени тем самым имитируя общение с человеком

    :param message: Сообщение от пользователя
    :param text: Текст, который необходимо отправить пользователю (не больше 4096)
    :param keyboard: Клавиатура
    :param sec: Кол-во секунд задержки
    """

    await asyncio.sleep(sec)
    await send_message_from_msg(message, text, keyboard)


async def send_message_from_msg(message: Message, text, keyboard=None):
    """
    Метод отправляет ответ пользователю на переданное сообщение

    :param message: Сообщение от пользователя
    :param text: Текст, который необходимо отправить пользователю (не больше 4096)
    :param keyboard: Клавиатура
    """

    try:
        if text is None:
            raise Exception

        await message.answer(text=text,
                             parse_mode=ParseMode.MARKDOWN,
                             reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        #logger.exception(f"Ошибка при отправке сообщения: {e}", extra={"service": "general"})
        await message.answer(f"Произошла непредвиденная ошибка, пожалуста обратитесь к администратору!")


async def send_message_from_call(call: CallbackQuery, text, keyboard=None):
    """
    Метод отправляет ответ пользователю на нажатую кнопку

    :param call: Текст кнопки
    :param text: Текст, который необходимо отправить пользователю (не больше 4096)
    :param keyboard: Клавиатура
    """

    try:
        if text is None:
            raise Exception

        await call.message.answer(text=text,
                                  parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=keyboard)

    except Exception as e:
        #logger.exception(f"Ошибка при отправке сообщения: {e}", extra={"service": "general"})
        await call.message.answer(f"Произошла непредвиденная ошибка, пожалуста обратитесь к администратору!")


async def send_photo_from_msg(message: Message, photo, text=None, keyboard=None):
    """
    Метод отправляет ответ пользователю с картинкой на нажатую кнопку

    :param message: Сообщение от пользователя
    :param photo: Картинка, которую надо отправить пользователю
    :param text: Текст, который необходимо отправить пользователю (не больше 1024)
    :param keyboard: Клавиатура
    """

    try:
        if photo is None:
            raise Exception

        await message.answer_photo(photo=photo,
                                   caption=text,
                                   parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboard)
    except Exception as e:
        #logger.exception(f"Ошибка при отправке сообщения: {e}", extra={"service": "general"})
        await message.answer(f"Произошла непредвиденная ошибка, пожалуста обратитесь к администратору!")


async def send_photo_from_call(call: CallbackQuery, photo, text=None, keyboard=None):
    """
   Метод отправляет ответ пользователю с картинкой на переданное сообщение

   :param call: Текст кнопки
   :param photo: Картинка, которую надо отправить пользователю
   :param text: Текст, который необходимо отправить пользователю (не больше 1024)
   :param keyboard: Клавиатура
   """

    try:
        if photo is None:
            raise Exception

        await call.message.answer_photo(photo=photo,
                                   caption=text,
                                   parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=keyboard)
    except Exception as e:
        #logger.exception(f"Ошибка при отправке сообщения: {e}", extra={"service": "general"})
        await call.message.answer(f"Произошла непредвиденная ошибка, пожалуста обратитесь к администратору!")


async def send_exception_and_request_data_again_from_msg(message: Message, exception_text=None):
    """
    Метод отправляет сообщение с исключением и предлагает повторить ввод

    :param message: Сообщение от пользователя
    :param exception_text: Текст исключения
    """

    await send_message_from_msg(message=message,
                                text=str(exception_text))
    await send_message_from_msg(message=message,
                                text="Пожалуйста, попробуйте еще раз.",
                                keyboard=cancel_action_keyboard)


async def send_exception_and_request_data_again_from_call(call: CallbackQuery, exception_text=None):
    """
    Метод отправляет сообщение с исключением и предлагает повторить ввод

    :param call: Текст кнопки
    :param exception_text: Текст исключения
    """

    await send_message_from_call(call=call,
                                text=str(exception_text))
    await send_message_from_call(call=call,
                                text="Пожалуйста, попробуйте еще раз.",
                                keyboard=cancel_action_keyboard)


async def delete_message(chat_id, message_id):
    """
    Метод удаляет сообщение по id

    :param chat_id: id чата
    :param message_id: id сообщения
    """

    await bot.delete_message(chat_id=chat_id, message_id=message_id)


async def delete_previous_message_and_send_new_from_call(call: CallbackQuery, text,  keyboard=None):
    """
    Метод вначале удаляет предыдущее сообщение и отправляет вместо него новое

    :param call: Вызов кнопки
    :param text: Текст, который необходимо отправить пользователю (не больше 4096)
    :param keyboard: Клавиатура
    """

    await delete_message(chat_id=call.message.chat.id,
                         message_id=call.message.message_id)

    await send_message_from_call(call=call,
                                 text=text,
                                 keyboard=keyboard)

async def delete_previous_message_and_send_new_from_msg(message: Message, text,  keyboard=None):
    """
    Метод вначале удаляет предыдущее сообщение и отправляет вместо него новое

    :param message: Сообщение от пользователя
    :param text: Текст, который необходимо отправить пользователю (не больше 4096)
    :param keyboard: Клавиатура
    """

    await delete_message(chat_id=message.chat.id,
                         message_id=message.message_id)

    await send_message_from_msg(message=message,
                                text=text,
                                keyboard=keyboard)


async def send_message_from_bot(chat_id, text, keyboard=None):
    """
    Отправляет сообщение через бота пользователю по chat_id

    :param keyboard: Клавиатура
    :param chat_id: id чата
    :param text: Сообщение
    """

    await bot.send_message(chat_id=chat_id,
                           text=text,
                           parse_mode=ParseMode.MARKDOWN,
                           reply_markup=keyboard)


###
###### Проверки на корректный формат данных
####
##


async def is_correct_format_name(value):
    """
    Метод проверяет формат переданного имени/фамилии на корректность.
    Должны быть только буквы и возможен дефис между частями слова.
    Иначе выбрасывает исключение IncorrectNameException.

    :param value: значение, которое необходимо проверить
    """

    # Проверка, что на вход передаются только буквы и допускается один или несколько дефисов между частями слова
    if not re.fullmatch(r'^[A-Za-zА-Яа-яЁё]+(?:-[A-Za-zА-Яа-яЁё]+)*$', str(value)):
        raise IncorrectNameException


async def is_correct_format_date(value):
    """
    Метод проверяет формат переданной даты на корректность.
    Дата должна быть в формате "ДД.ММ.ГГГГ" (где день от 01 до 31, месяц от 01 до 12, и год — 4 цифры).
    Иначе выбрасывает исключение IncorrectDateOfPurchaseException.

    :param value: значение, которое необходимо проверить
    """

    # Проверка, что на вход передается дата в формате "ДД.ММ.ГГГГ" (где день от 01 до 31, месяц от 01 до 12, и год — 4 цифры)
    if not re.fullmatch( r'^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(\d{4})$', str(value)):
        raise IncorrectDateOfPurchaseException


async def is_correct_period_date(value):
    """
    Метод проверяет, что переданная дата не раньше 01.01.1900 и не позже сегодняшнего дня
    :param value: значение, которое необходимо проверить
    """
    try:
        date = datetime.strptime(value, "%d.%m.%Y").date()

        # Ограничение по минимальной дате (опционально, можно убрать)
        min_date = datetime(1900, 1, 1).date()

        # Текущая дата
        today = datetime.today().date()

        # Проверка что дата не в будущем и не раньше min_date
        if not min_date <= date <= today:
            raise IncorrectPeriodDateException

    except ValueError:
        raise IncorrectPeriodDateException




async def is_correct_format_serial_number(value):
    """
    Метод проверяет формат переданного серийного номера на корректность.
    Серийный номер должен состоять из чисел.
    Иначе выбрасывает исключение IncorrectSerialNumberException.

    :param value: значение серийного номера
    """

    # Проверка, что на вход передаются числа
    if not re.fullmatch(r'^\d+$', str(value)):
        raise IncorrectSerialNumberException


async def is_correct_format_phone(value):
    """
    Метод проверяет формат переданного номера телефона на корректность.
    Номер должен начинаться с +7, без пробелов и спец символов, и содержать 11 цифр.
    Иначе выбрасывает исключение IncorrectPhoneException.

    :param value: значение серийного номера
    """

    # Проверка, что на вход передаются числа длинной в 11 цифр, начинающиеся с +7, без пробелов и спец символов
    if not re.fullmatch(r'^\+7\d{10}$', str(value)):
        raise IncorrectPhoneException


async def is_correct_format_email(value):
    """
    Метод проверяет формат переданного email на квалидность. Возвращет нормализированный адрес электронной почты
    Email должен иметь формат: [буквы, цифры, подчёркивания, точки, плюсы и дефисы]@[буквы, цифры и дефис].[любое кол-во символов].
    Иначе выбрасывает исключение IncorrectEmailException.

    :param value: адрес электронной почты
    :return нормализированный адрес электронной почты
    """

    try:
        valid = validate_email(value)
        return valid.normalized
    except EmailNotValidError:
        raise IncorrectEmailException


async def is_correct_checking_email_code(code_from_user, checking_code):
    """
    Метод проверяет введенный проверочный код от пользователя с реальным

    :param code_from_user: Проверочный код, введенный пользователем
    :param checking_code: Реальный проверочный код
    """

    # Проверяем, что пользователь ввел числа
    if not re.fullmatch(r'^\d+$', str(code_from_user)):
        raise IncorrectCheckingEmailCodeException

    # Нормализуем коды для сравнения (убираем ведущие нули)
    user_code_int = int(code_from_user)
    checking_code_int = int(checking_code)
    
    # Проверяем корректность введенного кода
    # Также принимаем "0000" или "0" если checking_code равен 0 (заглушка)
    if user_code_int != checking_code_int:
        # Если это заглушка (код = 0), принимаем "0000" или "0"
        if checking_code_int == 0 and user_code_int == 0:
            return  # Код верный
        raise WrongCheckingEmailCodeException


async def is_pdf_file(document):
    """
    Метод проверяет, что передан файл в формате .pdf

    :param file: Файл
    """

    if document.mime_type != 'application/pdf' or not document.file_name.lower().endswith('.pdf'):
        raise IncorrectFileFormatException


async def is_filename_latin(value):
    """
    Метод проверяет, что название файла написано на латинице

    :param value: Название файла
    """

    # Проверка, что переданы латинские буквы (a-z, A-Z), цифры, подчеркивания, дефисы и точки
    if not re.fullmatch(r'^[A-Za-z0-9_.-]+$' , str(value)):
        raise IncorrectFileNameException