import os
from aiogram import *
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram import Router

from main.handler.device_info_handler import devices_info
from main.handler.guarantee_handler import guarantee
from main.handler.promotion_handler import get_promotion
from main.handler.technical_department_handler import technical_support_department
from main.middleware.middleware import ChatActionMiddleware
from main.service.model.user_service import UserService
from main.utils import send_message_from_msg, send_message_from_call


# Флаг использования Form Engine (по умолчанию включен)
USE_FORM_ENGINE = os.environ.get("USE_FORM_ENGINE", "1") == "1"


###
###### Хендлер для работы с основными командами
####
##


router = Router()
router.message.middleware(ChatActionMiddleware())

user_service = UserService()


@router.message(Command('start'))
async def start(message: Message):
    """
    Метод запускает бота

    :param message: Сообщение от пользоваетля
    """

    await user_service.create_user(chat_id=message.chat.id,
                                   username=message.from_user.username,
                                   full_name=message.from_user.full_name)

    # Создаем inline-клавиатуру с двумя кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Активировать гарантию 📑", callback_data="activate_guarantee")],
        [InlineKeyboardButton(text="Обратиться в техническую поддержку 🔧", url="https://t.me/support")]
    ])

    await send_message_from_msg(message=message,
                                text="Это Бот-помощник для активации гарантии! Используя данного бота вы соглашаетесь на обработку персональных данных "
                                     "и на получение Email писем с выгодными предложениями.\n\n"
                                     "Для работы выберите команды из списка по кнопке 'Меню'\n\n"
                                     "Мои возможности:\n"
                                     "  🔹 Активировать гарантию 📑\n"
                                     "  🔹 Обратиться в рамках гарантийной поддержки 🔧",
                                keyboard=keyboard)


@router.message(Command('guarantee'))
async def guarantee_main(message: Message, state: FSMContext):
    """
    Вызов метода инициализации гарантии.
    
    Использует Form Engine если USE_FORM_ENGINE=1.

    :param state: Состояние
    :param message: Сообщение от пользователя
    """
    if USE_FORM_ENGINE:
        from main.handler.form_guarantee_handler import start_activation_form
        
        user = await user_service.create_user(
            chat_id=message.chat.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )
        
        initial_data = {}
        if user.name:
            initial_data['name'] = user.name
        if user.surname:
            initial_data['surname'] = user.surname
        if user.phone:
            initial_data['phone'] = user.phone
        if user.email:
            initial_data['email'] = user.email
        if user.city:
            initial_data['city'] = user.city
        
        await start_activation_form(
            event=message,
            state=state,
            initial_data=initial_data if initial_data else None
        )
    else:
        await guarantee(message, state)


@router.message(Command('promotion'))
async def promotion_main(message: Message):
    """
    Вызов метода работы с акциями

    :param message: Сообщение от пользователя
    """

    await get_promotion(message)


@router.message(Command('device_info'))
async def device_info_main(message: Message):
    """
    Вызов метода работы с информацией о устройствах клиента

    :param message: Сообщение от пользователя
    """

    await devices_info(message)


@router.message(Command('technical_support_department'))
async def technical_support_department_main(message: Message):
    """
    Вызов метода работы с сервисным центром

    :param message: Сообщение от пользователя
    """

    await technical_support_department(message)


@router.message(Command('support'))
async def support_command(message: Message):
    """
    Команда /support — выводит контакт техподдержки.
    """

    await send_message_from_msg(
        message=message,
        text="Техподдержка - @RackotXO "
    )


@router.callback_query(F.data == "activate_guarantee")
async def activate_guarantee_from_button(call: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки активации гарантии из главного меню.
    
    Использует Form Engine если USE_FORM_ENGINE=1 (по умолчанию),
    иначе использует legacy handler.

    :param call: CallbackQuery
    :param state: Состояние
    """
    if USE_FORM_ENGINE:
        # Новый путь через Form Engine
        from main.handler.form_guarantee_handler import start_activation_form
        
        # Проверяем/создаём пользователя
        user = await user_service.create_user(
            chat_id=call.message.chat.id,
            username=call.from_user.username,
            full_name=call.from_user.full_name
        )
        
        # Предзаполняем данные если есть
        initial_data = {}
        if user.name:
            initial_data['name'] = user.name
        if user.surname:
            initial_data['surname'] = user.surname
        if user.phone:
            initial_data['phone'] = user.phone
        if user.email:
            initial_data['email'] = user.email
        if user.city:
            initial_data['city'] = user.city
        
        await start_activation_form(
            event=call,
            state=state,
            initial_data=initial_data if initial_data else None
        )
    else:
        # Legacy путь
        from main.handler.guarantee_handler import guarantee
        await guarantee(call.message, state)
        await call.answer()


@router.callback_query(F.data.startswith('main_action_'))
async def cancel_action(call: CallbackQuery, state: FSMContext):
    """
    Метод отменяет текущее действие (отчищает заданное состояние)

    :param call: Текст кнопки
    :param state: Состояние
    """

    await state.clear()
    action_type = str(call.data.replace('main_action_', ''))

    match action_type:
        case "cancel":
            await send_message_from_call(call=call,
                                         text="Действие отменено")
        case "refuse":
            await send_message_from_call(call=call,
                                         text="Благодарим за Ваш выбор")
