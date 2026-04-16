"""
aiogram Handlers для Form Engine.

Предоставляет:
- Router с обработчиками для Form Engine
- Функции для запуска форм
- Интеграция с FSMContext
"""

from typing import Optional, Dict, Any, Callable, Awaitable
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from pathlib import Path

from main.forms.engine import FormEngine, load_form, register_submit_handler
from main.forms.schemas import FormConfig, FormSubmitResult
from main.forms.renderer import FormRenderer
from main.config.log_config import logger


class FormEngineState(StatesGroup):
    """FSM состояние для Form Engine"""
    filling = State()  # Пользователь заполняет форму


# Создаём router для Form Engine
form_router = Router(name="form_engine")


# Кэш активных форм по user_id
_active_engines: Dict[int, FormEngine] = {}


def get_active_engine(user_id: int) -> Optional[FormEngine]:
    """Получить активный движок формы для пользователя"""
    return _active_engines.get(user_id)


def set_active_engine(user_id: int, engine: FormEngine):
    """Установить активный движок формы для пользователя"""
    _active_engines[user_id] = engine


def clear_active_engine(user_id: int):
    """Очистить активный движок формы"""
    _active_engines.pop(user_id, None)


async def start_form(
    event: Message | CallbackQuery,
    state: FSMContext,
    form_path: str | Path = None,
    form_config: FormConfig | Dict[str, Any] = None,
    initial_data: Optional[Dict[str, Any]] = None
) -> FormEngine:
    """
    Запустить форму для пользователя.
    
    :param event: Message или CallbackQuery
    :param state: FSMContext
    :param form_path: Путь к YAML/JSON конфигу формы
    :param form_config: Или готовый конфиг (dict/FormConfig)
    :param initial_data: Начальные данные для предзаполнения
    :return: FormEngine instance
    """
    # Загружаем или создаём engine
    if form_path:
        engine = load_form(form_path)
    elif form_config:
        engine = FormEngine(form_config)
    else:
        raise ValueError("Either form_path or form_config must be provided")
    
    user_id = event.from_user.id
    
    # Сохраняем engine в кэш
    set_active_engine(user_id, engine)
    
    # Устанавливаем FSM состояние
    await state.set_state(FormEngineState.filling)
    
    # Запускаем форму
    await engine.start(event, state, initial_data)
    
    return engine


async def stop_form(user_id: int, state: FSMContext):
    """
    Остановить форму для пользователя.
    
    :param user_id: ID пользователя
    :param state: FSMContext
    """
    clear_active_engine(user_id)
    await state.clear()


# Специальная обработка /start во время заполнения формы:
# сбрасываем форму и передаём управление основному /start-хендлеру.
@form_router.message(FormEngineState.filling, Command("start"))
async def handle_start_during_form(message: Message, state: FSMContext):
    """Если пользователь вводит /start во время формы — сбросить форму и показать главное меню."""
    from main.handler.main_handler import start as main_start  # ленивый импорт, чтобы избежать циклов

    await stop_form(message.from_user.id, state)
    await main_start(message)


# Handler для текстовых сообщений в состоянии заполнения формы
@form_router.message(FormEngineState.filling)
async def handle_form_message(message: Message, state: FSMContext):
    """Обработка текстового ввода в форме"""
    engine = get_active_engine(message.from_user.id)
    
    if not engine:
        # Форма не найдена — сбрасываем состояние
        await state.clear()
        return
    
    # Передаём ввод в движок
    processed = await engine.process_input(message, state)
    
    if not processed:
        # Форма завершена или отменена
        clear_active_engine(message.from_user.id)
        await state.clear()


# Handler для callback'ов формы
@form_router.callback_query(F.data.startswith(FormRenderer.CB_PREFIX))
async def handle_form_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка callback'ов от кнопок формы"""
    engine = get_active_engine(callback.from_user.id)
    
    if not engine:
        # Пробуем найти engine по состоянию
        current_state = await state.get_state()
        if current_state != FormEngineState.filling:
            await callback.answer("Форма не найдена. Начните заново.", show_alert=True)
            return
    
    if engine:
        # Передаём callback в движок
        processed = await engine.process_callback(callback, state)
        
        if not processed:
            await callback.answer()
    else:
        await callback.answer("Форма не активна", show_alert=True)


# Экспорт декоратора для удобства
__all__ = [
    "form_router",
    "FormEngineState",
    "start_form",
    "stop_form",
    "get_active_engine",
    "register_submit_handler",
]
