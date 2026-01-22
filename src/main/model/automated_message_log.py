from datetime import datetime

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Index

from main.config.db_config import Base


class AutomatedMessageLog(Base):
    """
    Лог отправленных автоматических сообщений (день 3, день 15, сезонные рассылки).
    Помогает не дублировать одно и то же сообщение одному и тому же пользователю/гарантии.
    """

    __tablename__ = "automated_message_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Кому отправили
    user_chat_id = Column(BigInteger, ForeignKey("user.chat_id"), index=True, nullable=False)

    # Для каких гарантий (может быть NULL для общих рассылок, например сезонных)
    guarantee_id = Column(BigInteger, ForeignKey("guarantee.id"), index=True, nullable=True)

    # Тип сообщения: DAY3_CONTENT, DAY15_REVIEW, SEASON_SPRING, SEASON_AUTUMN и т.п.
    message_type = Column(String, nullable=False)

    # Время отправки
    sent_at = Column(DateTime, default=datetime.now)


# Индекс для быстрого поиска по пользователю/типу/гарантии
Index(
    "ix_automated_message_log_user_msg_type",
    AutomatedMessageLog.user_chat_id,
    AutomatedMessageLog.message_type,
    AutomatedMessageLog.guarantee_id,
)


