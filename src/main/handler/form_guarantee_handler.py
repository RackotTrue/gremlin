"""
Handler для активации гарантии через Form Engine.

Этот модуль предоставляет новый путь активации гарантии через
универсальный Form Engine. Старый handler (guarantee_handler.py) 
сохранён для совместимости.

Использование:
- /activate_new — запуск формы активации через Form Engine
- Кнопка "Активировать гарантию" в main_handler теперь использует Form Engine
"""

from pathlib import Path
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from main.forms import start_form, stop_form
from main.forms.handlers import FormEngineState
from main.config.log_config import logger
from main.middleware.middleware import ChatActionMiddleware
from main.service.model.user_service import UserService


router = Router(name="form_guarantee")
router.message.middleware(ChatActionMiddleware())

user_service = UserService()

# Путь к конфигурации формы активации
ACTIVATION_FORM_PATH = Path(__file__).resolve().parents[2] / "resources" / "forms" / "activation.yml"


@router.message(Command('activate_new'))
async def activate_guarantee_form_engine(message: Message, state: FSMContext):
    """
    Запуск формы активации гарантии через Form Engine.
    Команда: /activate_new
    """
    logger.info(
        f"User {message.from_user.id} started activation via Form Engine",
        extra={"service": "form_guarantee"}
    )
    
    # Проверяем/создаём пользователя
    user = await user_service.create_user(
        chat_id=message.chat.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    # Проверяем, есть ли уже заполненный профиль — предзаполняем данные
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
    
    # Запускаем форму
    await start_form(
        event=message,
        state=state,
        form_path=ACTIVATION_FORM_PATH,
        initial_data=initial_data if initial_data else None
    )


@router.callback_query(F.data == "activate_guarantee_new")
async def activate_guarantee_from_button_form_engine(call: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки активации гарантии (новый путь через Form Engine).
    Callback: activate_guarantee_new
    """
    logger.info(
        f"User {call.from_user.id} started activation via button (Form Engine)",
        extra={"service": "form_guarantee"}
    )
    
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
    
    # Запускаем форму
    await start_form(
        event=call,
        state=state,
        form_path=ACTIVATION_FORM_PATH,
        initial_data=initial_data if initial_data else None
    )


async def start_activation_form(
    event: Message | CallbackQuery, 
    state: FSMContext,
    initial_data: dict = None
):
    """
    Вспомогательная функция для запуска формы активации.
    Может вызываться из других модулей.
    
    :param event: Message или CallbackQuery
    :param state: FSMContext
    :param initial_data: Начальные данные для предзаполнения
    """
    await start_form(
        event=event,
        state=state,
        form_path=ACTIVATION_FORM_PATH,
        initial_data=initial_data
    )
