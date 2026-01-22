from aiogram.filters.callback_data import CallbackData
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from main.enum.main_menu_enum import MainMenuButtonEnum


class CheckingEmailCall(CallbackData, prefix = "resend_checking_email"):
    state: str


# Клавиатура главного меню
main_menu_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=MainMenuButtonEnum.SALES_DEPARTMENT.value), KeyboardButton(text=MainMenuButtonEnum.TECHNICAL_SUPPORT_DEPARTMENT.value)],
    [KeyboardButton(text= MainMenuButtonEnum.GUARANTEE.value), KeyboardButton(text=MainMenuButtonEnum.PROMOTION.value)]
],resize_keyboard=True)


# Клавиатура для отмены действия
cancel_action_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=MainMenuButtonEnum.MAIN_ACTION_CANCEL.value, callback_data="main_action_cancel")]
])


# Клавиатура для закрытия сессии
close_session_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=MainMenuButtonEnum.CLOSE_SESSION.value)]
], resize_keyboard=True, one_time_keyboard=True)


async def get_checking_email_keyboard(state: str):
    """
    # Клавиатура для проверки Email

    :param state: Состояние, в которое надо перейти после запроса Email
    :return: клавиатура
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MainMenuButtonEnum.RESEND_CHECKING_EMAIL.value, callback_data=CheckingEmailCall(state=state).pack())],
        [InlineKeyboardButton(text=MainMenuButtonEnum.MAIN_ACTION_CANCEL.value, callback_data="main_action_cancel")]
    ])

    return keyboard