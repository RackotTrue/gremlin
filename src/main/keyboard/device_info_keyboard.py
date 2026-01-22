from sys import prefix

from aiogram.filters.callback_data import CallbackData
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from main.model.device_base import DeviceBase


class ChoiceDeviceCall(CallbackData, prefix="choice_device"):
    device_id: int


async def get_device_keyboard(devices) -> InlineKeyboardMarkup:
    """
    Метод возвращает клавиатуру из массива устройств пользователя

    :param devices: Список устройств пользователя
    :return: Клавиатура
    """

    inline_keyboard = []

    for device in devices:

        id = device.id
        model = device.model
        serial_number = device.serial_number

        inline_keyboard.append([InlineKeyboardButton(text=f"{model} ({serial_number})",
                                                     callback_data=ChoiceDeviceCall(device_id=id).pack())])

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    return keyboard
