import asyncio
import sys
import threading
from pathlib import Path
from aiogram import *
from aiogram.types import ErrorEvent
from aiogram.fsm.storage.memory import MemoryStorage


# Добавляем папку src в sys.path
project_root = Path(__file__).resolve().parent  # Получаем путь к корню проекта
src_folder = project_root / 'src'  # Путь к папке src
sys.path.append(str(src_folder))  # Добавляем путь в sys.path

from main.config.bot_config import scheduler
from main.config.db_config import create_tables
# Импорт моделей для регистрации в Base.metadata (lead, video_job)
from main.model.lead_base import LeadBase  # noqa: F401
from main.model.video_job_base import VideoJobBase  # noqa: F401
from main.config.log_config import asyncio_exception_handler
from main.middleware.middleware import ErrorLoggingMiddleware
from main.handler.main_handler import router as main_router
from main.handler.administration_handler import router as admin_router
from main.handler.guarantee_handler import router as guarantee_router
from main.handler.promotion_handler import router as promotion_router
from main.handler.device_info_handler import router as device_info_router
from main.handler.broadcast_handler import router as broadcast_router
from main.handler.video_greeting_handler import router as video_greeting_router  # Видео-открытка
from main.forms.handlers import form_router  # Form Engine router
from main.service.integration.notifications_service import setup_scheduled_jobs
from main.utils import *


async def run_bot():
    """
    Метод запуска бота
    """

    dispatcher = Dispatcher(storage=MemoryStorage())

    # Перехват возможных ошибок
    dispatcher.message.middleware(ErrorLoggingMiddleware())
    dispatcher.callback_query.middleware(ErrorLoggingMiddleware())
    
    # Глобальный обработчик ошибок
    @dispatcher.errors()
    async def error_handler(event: ErrorEvent, **kwargs):
        from main.config.log_config import logger
        exception = event.exception

        logger.exception(f"Глобальная ошибка: {exception}", extra={"service": "error_handler"})

        try:
            update = event.update
            if update.message:
                await update.message.answer("Произошла ошибка. Пожалуйста, попробуйте ещё раз.")
            elif update.callback_query:
                await update.callback_query.message.answer("Произошла ошибка. Пожалуйста, попробуйте ещё раз.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}", extra={"service": "error_handler"})

        return True

    # Подключение роутеров
    # Form Engine router должен быть первым для обработки callback'ов формы
    dispatcher.include_routers(form_router,
                               video_greeting_router,  # Видео-открытка
                               main_router,
                               admin_router,
                               broadcast_router,
                               guarantee_router,  # Legacy guarantee handler (совместимость)
                               device_info_router,
                               promotion_router)

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await set_bot_commands(bot)
    await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())


async def start():
    """
    Метод запуска приложения
    """

    # Создание таблиц
    await create_tables()

    # Настройка и запуск задач APScheduler
    setup_scheduled_jobs()
    scheduler.start()

    print("Бот запущен")
    logger.info("Бот запущен", extra={"service": "main"})

    await run_bot()


if __name__ == '__main__':
    try:

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_exception_handler(asyncio_exception_handler)
        loop.run_until_complete(start())

    # except ConnectionError as e:
    #     logger.error(f"Ошибка соединени: {e}", extra={"service": "main"})
    # except Exception as r:
    #     logger.error(f"Непридвиденная ошибка: {r}", extra={"service": "main"})
    finally:
        logger.info("Бот завершил работу", extra={"service": "main"})
        print("Бот завершил работу")

