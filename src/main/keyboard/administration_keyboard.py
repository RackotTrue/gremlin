from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from main.enum.administration_enum import DeleteDeviceButtonEnum
from main.enum.main_menu_enum import MainMenuButtonEnum

# Клавиатура для подтверждения удаления устройства
approve_delete_device_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=DeleteDeviceButtonEnum.APPROVE.value, callback_data="delete_device_approve")],
    [InlineKeyboardButton(text=MainMenuButtonEnum.MAIN_ACTION_CANCEL.value, callback_data="main_action_cancel")]
])