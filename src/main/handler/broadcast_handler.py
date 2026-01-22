import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from main.config.bot_config import bot
from main.config.log_config import logger
from main.middleware.middleware import ChatActionMiddleware
from main.repository.user_repository import UserRepository
from main.state.administration_state import BroadcastTextState, BroadcastPhotoState, BroadcastVideoState
from main.utils import is_admin, send_message_from_msg, send_message_from_call
from main.exception.exception import IsNotAdminException


###
###### Хендлер для рассылки сообщений
####
##


router = Router()
router.message.middleware(ChatActionMiddleware())

user_repository = UserRepository()


# Клавиатура подтверждения рассылки
confirm_broadcast_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm")],
    [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")]
])

# Клавиатура пропуска текста
skip_text_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⏭ Пропустить текст", callback_data="broadcast_skip_text")]
])


async def send_broadcast_report(chat_id: int, success: int, blocked: int, errors: int, total: int):
    """
    Отправляет отчёт о рассылке администратору
    """
    report = (
        f"📊 *Отчёт о рассылке:*\n\n"
        f"✅ Доставлено: {success}\n"
        f"🚫 Заблокировали бота: {blocked}\n"
        f"❌ Ошибки: {errors}\n\n"
        f"👥 Всего в базе: {total}"
    )
    await bot.send_message(chat_id, report, parse_mode="Markdown")


async def broadcast_text_to_users(admin_chat_id: int, text: str):
    """
    Рассылает текстовое сообщение всем пользователям
    """
    chat_ids = await user_repository.get_all_chat_ids()
    total = len(chat_ids)
    success = 0
    blocked = 0
    errors = 0

    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, text, parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)  # Задержка чтобы не превысить лимиты Telegram
        except Exception as e:
            error_msg = str(e).lower()
            if "blocked" in error_msg or "deactivated" in error_msg or "chat not found" in error_msg:
                blocked += 1
            else:
                errors += 1
                logger.error(f"Ошибка рассылки для {chat_id}: {e}", extra={"service": "broadcast"})

    await send_broadcast_report(admin_chat_id, success, blocked, errors, total)


async def broadcast_photo_to_users(admin_chat_id: int, photo_id: str, caption: str = None):
    """
    Рассылает фото всем пользователям
    """
    chat_ids = await user_repository.get_all_chat_ids()
    total = len(chat_ids)
    success = 0
    blocked = 0
    errors = 0

    for chat_id in chat_ids:
        try:
            await bot.send_photo(chat_id, photo_id, caption=caption, parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            error_msg = str(e).lower()
            if "blocked" in error_msg or "deactivated" in error_msg or "chat not found" in error_msg:
                blocked += 1
            else:
                errors += 1
                logger.error(f"Ошибка рассылки фото для {chat_id}: {e}", extra={"service": "broadcast"})

    await send_broadcast_report(admin_chat_id, success, blocked, errors, total)


async def broadcast_video_to_users(admin_chat_id: int, video_id: str, caption: str = None):
    """
    Рассылает видео всем пользователям
    """
    chat_ids = await user_repository.get_all_chat_ids()
    total = len(chat_ids)
    success = 0
    blocked = 0
    errors = 0

    for chat_id in chat_ids:
        try:
            await bot.send_video(chat_id, video_id, caption=caption, parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            error_msg = str(e).lower()
            if "blocked" in error_msg or "deactivated" in error_msg or "chat not found" in error_msg:
                blocked += 1
            else:
                errors += 1
                logger.error(f"Ошибка рассылки видео для {chat_id}: {e}", extra={"service": "broadcast"})

    await send_broadcast_report(admin_chat_id, success, blocked, errors, total)


# ==================== РАССЫЛКА ТЕКСТА ====================

@router.message(Command('send_text'))
async def cmd_send_text(message: Message, state: FSMContext):
    """
    Команда для начала рассылки текста
    """
    try:
        await is_admin(message.chat.id)

        await send_message_from_msg(
            message=message,
            text="📝 *Рассылка текста*\n\nВведите текст для рассылки:"
        )
        await state.set_state(BroadcastTextState.text)

    except IsNotAdminException as e:
        await send_message_from_msg(message=message, text=str(e))


@router.message(BroadcastTextState.text)
async def process_broadcast_text(message: Message, state: FSMContext):
    """
    Получает текст и запрашивает подтверждение
    """
    text = message.text
    await state.update_data(text=text)

    chat_ids = await user_repository.get_all_chat_ids()

    await send_message_from_msg(
        message=message,
        text=f"📝 *Предпросмотр рассылки:*\n\n{text}\n\n👥 Получателей: {len(chat_ids)}",
        keyboard=confirm_broadcast_keyboard
    )
    await state.set_state(BroadcastTextState.confirm)


# ==================== РАССЫЛКА ФОТО ====================

@router.message(Command('send_photo'))
async def cmd_send_photo(message: Message, state: FSMContext):
    """
    Команда для начала рассылки фото
    """
    try:
        await is_admin(message.chat.id)

        await send_message_from_msg(
            message=message,
            text="🖼 *Рассылка фото*\n\nОтправьте фото для рассылки:"
        )
        await state.set_state(BroadcastPhotoState.photo)

    except IsNotAdminException as e:
        await send_message_from_msg(message=message, text=str(e))


@router.message(BroadcastPhotoState.photo, F.photo)
async def process_broadcast_photo(message: Message, state: FSMContext):
    """
    Получает фото и запрашивает текст
    """
    photo_id = message.photo[-1].file_id  # Берём фото максимального размера
    await state.update_data(photo_id=photo_id)

    await send_message_from_msg(
        message=message,
        text="✍️ Теперь введите текст подписи к фото (или нажмите кнопку чтобы пропустить):",
        keyboard=skip_text_keyboard
    )
    await state.set_state(BroadcastPhotoState.text)


@router.message(BroadcastPhotoState.text)
async def process_broadcast_photo_text(message: Message, state: FSMContext):
    """
    Получает текст для фото и запрашивает подтверждение
    """
    caption = message.text
    await state.update_data(caption=caption)

    state_data = await state.get_data()
    photo_id = state_data["photo_id"]
    chat_ids = await user_repository.get_all_chat_ids()

    await bot.send_photo(
        message.chat.id,
        photo_id,
        caption=f"📝 *Предпросмотр рассылки:*\n\n{caption}\n\n👥 Получателей: {len(chat_ids)}",
        parse_mode="Markdown"
    )
    await send_message_from_msg(
        message=message,
        text="Подтвердите отправку:",
        keyboard=confirm_broadcast_keyboard
    )
    await state.set_state(BroadcastPhotoState.confirm)


@router.callback_query(BroadcastPhotoState.text, F.data == "broadcast_skip_text")
async def skip_photo_text(call: CallbackQuery, state: FSMContext):
    """
    Пропуск текста для фото
    """
    await state.update_data(caption=None)

    state_data = await state.get_data()
    photo_id = state_data["photo_id"]
    chat_ids = await user_repository.get_all_chat_ids()

    await bot.send_photo(
        call.message.chat.id,
        photo_id,
        caption=f"📝 *Предпросмотр рассылки (без текста)*\n\n👥 Получателей: {len(chat_ids)}",
        parse_mode="Markdown"
    )
    await send_message_from_call(
        call=call,
        text="Подтвердите отправку:",
        keyboard=confirm_broadcast_keyboard
    )
    await state.set_state(BroadcastPhotoState.confirm)


# ==================== РАССЫЛКА ВИДЕО ====================

@router.message(Command('send_video'))
async def cmd_send_video(message: Message, state: FSMContext):
    """
    Команда для начала рассылки видео
    """
    try:
        await is_admin(message.chat.id)

        await send_message_from_msg(
            message=message,
            text="🎬 *Рассылка видео*\n\nОтправьте видео для рассылки:"
        )
        await state.set_state(BroadcastVideoState.video)

    except IsNotAdminException as e:
        await send_message_from_msg(message=message, text=str(e))


@router.message(BroadcastVideoState.video, F.video)
async def process_broadcast_video(message: Message, state: FSMContext):
    """
    Получает видео и запрашивает текст
    """
    video_id = message.video.file_id
    await state.update_data(video_id=video_id)

    await send_message_from_msg(
        message=message,
        text="✍️ Теперь введите текст подписи к видео (или нажмите кнопку чтобы пропустить):",
        keyboard=skip_text_keyboard
    )
    await state.set_state(BroadcastVideoState.text)


@router.message(BroadcastVideoState.text)
async def process_broadcast_video_text(message: Message, state: FSMContext):
    """
    Получает текст для видео и запрашивает подтверждение
    """
    caption = message.text
    await state.update_data(caption=caption)

    state_data = await state.get_data()
    video_id = state_data["video_id"]
    chat_ids = await user_repository.get_all_chat_ids()

    await bot.send_video(
        message.chat.id,
        video_id,
        caption=f"📝 *Предпросмотр рассылки:*\n\n{caption}\n\n👥 Получателей: {len(chat_ids)}",
        parse_mode="Markdown"
    )
    await send_message_from_msg(
        message=message,
        text="Подтвердите отправку:",
        keyboard=confirm_broadcast_keyboard
    )
    await state.set_state(BroadcastVideoState.confirm)


@router.callback_query(BroadcastVideoState.text, F.data == "broadcast_skip_text")
async def skip_video_text(call: CallbackQuery, state: FSMContext):
    """
    Пропуск текста для видео
    """
    await state.update_data(caption=None)

    state_data = await state.get_data()
    video_id = state_data["video_id"]
    chat_ids = await user_repository.get_all_chat_ids()

    await bot.send_video(
        call.message.chat.id,
        video_id,
        caption=f"📝 *Предпросмотр рассылки (без текста)*\n\n👥 Получателей: {len(chat_ids)}",
        parse_mode="Markdown"
    )
    await send_message_from_call(
        call=call,
        text="Подтвердите отправку:",
        keyboard=confirm_broadcast_keyboard
    )
    await state.set_state(BroadcastVideoState.confirm)


# ==================== ПОДТВЕРЖДЕНИЕ / ОТМЕНА ====================

@router.callback_query(F.data == "broadcast_confirm")
async def confirm_broadcast(call: CallbackQuery, state: FSMContext):
    """
    Подтверждение и запуск рассылки
    """
    current_state = await state.get_state()
    state_data = await state.get_data()

    await call.message.edit_text("⏳ Рассылка запущена...")

    if current_state == BroadcastTextState.confirm:
        text = state_data["text"]
        await broadcast_text_to_users(call.message.chat.id, text)

    elif current_state == BroadcastPhotoState.confirm:
        photo_id = state_data["photo_id"]
        caption = state_data.get("caption")
        await broadcast_photo_to_users(call.message.chat.id, photo_id, caption)

    elif current_state == BroadcastVideoState.confirm:
        video_id = state_data["video_id"]
        caption = state_data.get("caption")
        await broadcast_video_to_users(call.message.chat.id, video_id, caption)

    await state.clear()


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(call: CallbackQuery, state: FSMContext):
    """
    Отмена рассылки
    """
    await state.clear()
    await call.message.edit_text("❌ Рассылка отменена")


