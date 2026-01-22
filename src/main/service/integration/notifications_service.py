from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy import select, and_, or_, func

from main.config.bot_config import bot, scheduler
from main.config.db_config import AsyncSessionLocal
from main.config.log_config import logger
from main.model.guarantee_base import GuaranteeBase
from main.model.device_base import DeviceBase
from main.model.user_base import UserBase
from main.model.automated_message_log import AutomatedMessageLog


DAY3_MESSAGE_TYPE = "DAY3_CONTENT"
DAY15_MESSAGE_TYPE = "DAY15_REVIEW"
SEASON_SPRING_MESSAGE_TYPE = "SEASON_SPRING"
SEASON_AUTUMN_MESSAGE_TYPE = "SEASON_AUTUMN"


async def _get_due_guarantees(days_after: int) -> List[Tuple[GuaranteeBase, DeviceBase, UserBase]]:
    """
    Возвращает список (guarantee, device, user), по которым прошло не менее days_after дней
    с момента создания гарантии и есть согласие на маркетинг.
    """
    now = datetime.now()
    threshold = now - timedelta(days=days_after)

    async with AsyncSessionLocal() as session:
        stmt = (
            select(GuaranteeBase, DeviceBase, UserBase)
            .join(DeviceBase, GuaranteeBase.device_id == DeviceBase.id)
            .join(UserBase, DeviceBase.user_id == UserBase.chat_id)
            .where(
                and_(
                    GuaranteeBase.created_datetime <= threshold,
                    GuaranteeBase.is_deleted.is_(False),
                    UserBase.marketing_consent.is_(True),
                )
            )
        )

        result = await session.execute(stmt)
        rows = result.all()
        return rows


async def _get_sent_guarantee_ids(message_type: str, guarantee_ids: List[int]) -> List[int]:
    """Возвращает список guarantee_id, для которых уже есть запись в логе по данному типу сообщения."""
    if not guarantee_ids:
        return []

    async with AsyncSessionLocal() as session:
        stmt = select(AutomatedMessageLog.guarantee_id).where(
            and_(
                AutomatedMessageLog.message_type == message_type,
                AutomatedMessageLog.guarantee_id.in_(guarantee_ids),
            )
        )
        result = await session.execute(stmt)
        return [gid for (gid,) in result.all() if gid is not None]


def _get_review_source_text(user: UserBase) -> str:
    """Возвращает понятный текст для источника заказа."""
    source = (user.order_source or "").lower()

    if "ozon" in source:
        return "Ozon"
    if "wild" in source or "wb" in source:
        return "Wildberries"
    if "яндекс" in source or "ym" in source or "market" in source:
        return "Яндекс Маркет"
    if "avito" in source:
        return "Avito"

    # Розница или неизвестный источник
    if "розниц" in source:
        return "месте покупки в рознице"

    return ""


async def send_day3_content_notifications():
    """
    Отправляет сообщение на 3-й день после создания гарантии:
    "Полезный контент - "
    """
    try:
        rows = await _get_due_guarantees(days_after=3)
        guarantee_ids = [g.id for g, _, _ in rows]

        already_sent = set(await _get_sent_guarantee_ids(DAY3_MESSAGE_TYPE, guarantee_ids))

        async with AsyncSessionLocal() as session:
            for guarantee, device, user in rows:
                if guarantee.id in already_sent:
                    continue

                try:
                    await bot.send_message(
                        chat_id=user.chat_id,
                        text="Полезный контент - ",
                    )

                    log = AutomatedMessageLog(
                        user_chat_id=user.chat_id,
                        guarantee_id=guarantee.id,
                        message_type=DAY3_MESSAGE_TYPE,
                    )
                    session.add(log)
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке сообщения дня 3 пользователю {user.chat_id}: {e}",
                        extra={"service": "notifications"},
                    )

            await session.commit()
    except Exception as e:
        logger.error(
            f"Ошибка при выполнении задачи day3 notifications: {e}",
            extra={"service": "notifications"},
        )


async def send_day15_review_notifications():
    """
    Отправляет сообщение на 15-й день после создания гарантии:
    "Оставь отзыв на [источник заказа]"
    """
    try:
        rows = await _get_due_guarantees(days_after=15)
        guarantee_ids = [g.id for g, _, _ in rows]

        already_sent = set(await _get_sent_guarantee_ids(DAY15_MESSAGE_TYPE, guarantee_ids))

        async with AsyncSessionLocal() as session:
            for guarantee, device, user in rows:
                if guarantee.id in already_sent:
                    continue

                source_text = _get_review_source_text(user)

                if source_text:
                    text = f"Оставь отзыв на {source_text}"
                else:
                    text = "Оставь отзыв о своём заказе"

                try:
                    await bot.send_message(
                        chat_id=user.chat_id,
                        text=text,
                    )

                    log = AutomatedMessageLog(
                        user_chat_id=user.chat_id,
                        guarantee_id=guarantee.id,
                        message_type=DAY15_MESSAGE_TYPE,
                    )
                    session.add(log)
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке сообщения дня 15 пользователю {user.chat_id}: {e}",
                        extra={"service": "notifications"},
                    )

            await session.commit()
    except Exception as e:
        logger.error(
            f"Ошибка при выполнении задачи day15 notifications: {e}",
            extra={"service": "notifications"},
        )


async def send_season_spring_notifications():
    """
    Сезонный триггер: 15 марта — напоминание переобуться на летнюю резину.
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(UserBase).where(UserBase.marketing_consent.is_(True))
            result = await session.execute(stmt)
            users = result.scalars().all()

            if not users:
                return

            chat_ids = [u.chat_id for u in users]

            # Проверяем, кому уже отправляли это сообщение
            log_stmt = select(AutomatedMessageLog.user_chat_id).where(
                and_(
                    AutomatedMessageLog.message_type == SEASON_SPRING_MESSAGE_TYPE,
                    AutomatedMessageLog.user_chat_id.in_(chat_ids),
                )
            )
            log_result = await session.execute(log_stmt)
            already_sent_chat_ids = {cid for (cid,) in log_result.all()}

            text = (
                "Скоро начинается тёплый сезон! Пора задуматься о переходе на летнюю резину.\\n\\n"
                "Для оформления заказа на шиномонтаж или покупку шин напишите @RackotXO."
            )

            for user in users:
                if user.chat_id in already_sent_chat_ids:
                    continue

                try:
                    await bot.send_message(chat_id=user.chat_id, text=text)
                    session.add(
                        AutomatedMessageLog(
                            user_chat_id=user.chat_id,
                            guarantee_id=None,
                            message_type=SEASON_SPRING_MESSAGE_TYPE,
                        )
                    )
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке весеннего сезонного сообщения пользователю {user.chat_id}: {e}",
                        extra={"service": "notifications"},
                    )

            await session.commit()
    except Exception as e:
        logger.error(
            f"Ошибка при выполнении задачи spring seasonal notifications: {e}",
            extra={"service": "notifications"},
        )


async def send_season_autumn_notifications():
    """
    Сезонный триггер: 15 сентября — напоминание переобуться на зимнюю резину.
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(UserBase).where(UserBase.marketing_consent.is_(True))
            result = await session.execute(stmt)
            users = result.scalars().all()

            if not users:
                return

            chat_ids = [u.chat_id for u in users]

            # Проверяем, кому уже отправляли это сообщение
            log_stmt = select(AutomatedMessageLog.user_chat_id).where(
                and_(
                    AutomatedMessageLog.message_type == SEASON_AUTUMN_MESSAGE_TYPE,
                    AutomatedMessageLog.user_chat_id.in_(chat_ids),
                )
            )
            log_result = await session.execute(log_stmt)
            already_sent_chat_ids = {cid for (cid,) in log_result.all()}

            text = (
                "Скоро похолодает! Пора переходить на зимнюю резину.\\n\\n"
                "Для оформления заказа на шиномонтаж или покупку шин напишите @RackotXO."
            )

            for user in users:
                if user.chat_id in already_sent_chat_ids:
                    continue

                try:
                    await bot.send_message(chat_id=user.chat_id, text=text)
                    session.add(
                        AutomatedMessageLog(
                            user_chat_id=user.chat_id,
                            guarantee_id=None,
                            message_type=SEASON_AUTUMN_MESSAGE_TYPE,
                        )
                    )
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке осеннего сезонного сообщения пользователю {user.chat_id}: {e}",
                        extra={"service": "notifications"},
                    )

            await session.commit()
    except Exception as e:
        logger.error(
            f"Ошибка при выполнении задачи autumn seasonal notifications: {e}",
            extra={"service": "notifications"},
        )


def setup_scheduled_jobs():
    """
    Регистрирует задачи в APScheduler.
    """
    # Ежедневные задачи (например, в 11:00 по серверному времени)
    scheduler.add_job(send_day3_content_notifications, "cron", hour=11, minute=0)
    scheduler.add_job(send_day15_review_notifications, "cron", hour=11, minute=5)

    # Сезонные задачи: 15 марта и 15 сентября в 11:00
    scheduler.add_job(
        send_season_spring_notifications,
        "cron",
        month=3,
        day=15,
        hour=11,
        minute=0,
    )
    scheduler.add_job(
        send_season_autumn_notifications,
        "cron",
        month=9,
        day=15,
        hour=11,
        minute=0,
    )


