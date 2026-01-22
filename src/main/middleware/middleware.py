from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, TelegramObject
from aiogram.utils.chat_action import ChatActionSender

from main.config.log_config import logger


class ChatActionMiddleware(BaseMiddleware):
    # Показывает пользователю анимацию "...печатает" при получении сообщения и до отправки ответа

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:

        async with ChatActionSender.typing(event.chat.id, event.bot):
            return await handler(event, data)


class ErrorLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict
    ):
        try:
            return await handler(event, data)
        except Exception as e:
            # Логируем полную информацию об ошибке
            logger.exception(f"Ошибка при обработке события {type(event).__name__}: {e}", extra={"service": "general"})
            
            # Отправляем сообщение пользователю, если это Message или CallbackQuery
            try:
                from aiogram.types import Message, CallbackQuery
                if isinstance(event, Message):
                    await event.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже или обратитесь к администратору.")
                elif isinstance(event, CallbackQuery):
                    await event.message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже или обратитесь к администратору.")
            except Exception as send_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}", extra={"service": "general"})
            
            # Пробрасываем исключение дальше для обработки в dispatcher.errors
            raise