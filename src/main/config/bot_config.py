from aiogram import *
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from main.config.dynaconf_config import config_setting


# Инициализация бота
bot = Bot(token=config_setting.BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

# Инициализация Шедулера
scheduler = AsyncIOScheduler()