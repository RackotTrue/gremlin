"""
Handler для формы видео-открытки.

Запуск формы видео-открытки по команде /start или кнопке.
"""

from pathlib import Path
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from main.forms import start_form
from main.middleware.middleware import ChatActionMiddleware
from main.service.model.user_service import UserService
from main.config.log_config import logger


router = Router(name="video_greeting")
router.message.middleware(ChatActionMiddleware())

user_service = UserService()
VIDEO_GREETING_FORM_PATH = Path(__file__).resolve().parents[2] / "resources" / "forms" / "video_greeting.yml"


@router.message(Command("video"))
async def start_video_form_command(message: Message, state: FSMContext):
    """Команда /video — запуск формы видео-открытки."""
    logger.info(f"User {message.from_user.id} started video form via command", extra={"service": "video_greeting"})
    await _start_video_form(message, state, message.from_user.username, message.from_user.full_name)


@router.callback_query(F.data == "start_video_greeting")
async def start_video_form_button(call: CallbackQuery, state: FSMContext):
    """Кнопка «Сделать видео-открытку»."""
    logger.info(f"User {call.from_user.id} started video form via button", extra={"service": "video_greeting"})
    await _start_video_form(call, state, call.from_user.username, call.from_user.full_name)
    await call.answer()


async def _start_video_form(event: Message | CallbackQuery, state: FSMContext, username: str = None, full_name: str = None):
    chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
    await user_service.create_user(chat_id=chat_id, username=username, full_name=full_name or "")
    await start_form(event=event, state=state, form_path=VIDEO_GREETING_FORM_PATH)


async def start_video_greeting_form(
    event: Message | CallbackQuery,
    state: FSMContext,
    initial_data: dict = None,
):
    """
    Вспомогательная функция для запуска формы видео-открытки.
    Вызов из других модулей.
    """
    await start_form(
        event=event,
        state=state,
        form_path=VIDEO_GREETING_FORM_PATH,
        initial_data=initial_data,
    )
