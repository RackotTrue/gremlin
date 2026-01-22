import logging
import sys
import threading

from main.config.dynaconf_config import environment_setting


class SafeFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'service'):
            record.service = 'unknown'
        return super().format(record)


# Настройка отображения логов
formatter = SafeFormatter('%(asctime)s | %(levelname)s | %(service)s | %(message)s')


# Настройка логгера
logger = logging.getLogger("setka_garmoshka_bot")
logger.handlers = []


# Вывод логов в консоль (для всех сред)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

if environment_setting.environment == "development":
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


# TODO: Когда будет настроен Logtail/BetterStack, раскомментировать:
# if environment_setting.environment == "production":
#     try:
#         from logtail import LogtailHandler
#         from main.config.dynaconf_config import config_setting
#         logtail_handler = LogtailHandler(source_token=config_setting.LOGTAIL.TOKEN,
#                                          host=config_setting.LOGTAIL.HOST)
#         logtail_handler.setFormatter(formatter)
#         logger.addHandler(logtail_handler)
#     except Exception:
#         pass  # Logtail не настроен, используем только консоль


# Глобальный перехват необработанных исключений
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Необработанное исключение", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = global_exception_handler


# Asyncio исключения
def asyncio_exception_handler(loop, context):
    logger.error(f"Исключение в asyncio: {context.get('message')}", exc_info=context.get("exception"))


# Threading исключения (если есть потоки)
def threading_exception_handler(args):
    logger.error(f"Ошибка в потоке {args.thread.name}", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

threading.excepthook = threading_exception_handler
