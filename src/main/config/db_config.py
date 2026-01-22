
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from main.config.dynaconf_config import config_setting

# URL для подключения к базе данных с асинхронным драйвером (asyncpg)
# Пример: "postgresql+asyncpg://username:password@localhost:port/dbname"
DB_URL = (f'postgresql+asyncpg://'
          f'{config_setting.POSTGRES.USER}:'
          f'{config_setting.POSTGRES.PASSWORD}@'
          f'{config_setting.POSTGRES.HOST}:'
          f'{config_setting.POSTGRES.PORT}/'
          f'{config_setting.POSTGRES.DATABASE}')

# Базовый класс для моделей
Base = declarative_base()

# Асинхронный движок для работы с БД
engine = create_async_engine(url=DB_URL, echo=False)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def create_tables():
    """
    Асинхронная функция для создания таблиц при запуске

    """
    async with engine.begin() as connect:
        # Создаем таблицы, если их еще нет
        await connect.run_sync(Base.metadata.create_all, checkfirst=True)
