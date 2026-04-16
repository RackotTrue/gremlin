"""
Submit Handlers для Form Engine.

Содержит обработчики отправки форм, которые интегрируются
с бизнес-логикой приложения (Bitrix24, БД, PDF и т.д.).

Каждый handler регистрируется для конкретного form_id.
"""

from typing import Dict, Any

from main.forms.engine import register_submit_handler
from main.forms.schemas import FormConfig, FormState, FormSubmitResult



@register_submit_handler("video_greeting")
async def handle_video_greeting_submit(
    data: Dict[str, Any],
    state: FormState,
    config: FormConfig
) -> FormSubmitResult:
    """
    Обработчик формы видео-открытки.
    Создаёт lead, video_job, отправляет запрос в fal.ai.
    """
    from main.config.log_config import logger
    from main.config.bot_config import bot
    from main.service.model.user_service import UserService
    from main.repository.lead_repository import LeadRepository
    from main.repository.video_job_repository import VideoJobRepository
    from main.service.integration.fal_video_service import (
        create_avatar_task,
        build_spoken_script,
        MAX_SPOKEN_SCRIPT_CHARS,
    )
    from main.model.lead_base import LeadBase
    from main.model.video_job_base import VideoJobBase

    user_service = UserService()
    lead_repo = LeadRepository()
    job_repo = VideoJobRepository()

    try:
        logger.info(f"Processing video_greeting for chat {state.chat_id}", extra={"service": "form_engine"})

        spoken = build_spoken_script(
            data.get("child_name", ""),
            data.get("message_text", ""),
        )
        if len(spoken) > MAX_SPOKEN_SCRIPT_CHARS:
            return FormSubmitResult(
                success=False,
                error=(
                    "Текст для озвучки слишком длинный: максимум примерно "
                    f"{MAX_SPOKEN_SCRIPT_CHARS} символов вместе с приветствием и именем ребёнка "
                    f"(чтобы уложиться примерно в 10 секунд). Сейчас: {len(spoken)} символов. "
                    "Сократите поздравление или имя ребёнка."
                ),
            )

        user = await user_service.create_user(
            chat_id=state.chat_id,
            username=None,
            full_name=data.get("buyer_name", "")
        )
        user.name = data.get("buyer_name", "")
        user.phone = data.get("phone", "")
        await user_service.update_user(user)

        lead = LeadBase()
        lead.user_chat_id = state.chat_id
        lead.buyer_name = data.get("buyer_name", "")
        lead.phone = data.get("phone", "")
        lead.child_name = data.get("child_name", "")
        lead.seller_id = data.get("seller_id") or "default"
        lead = await lead_repo.create(lead)

        job = VideoJobBase()
        job.lead_id = lead.id
        job.type = "welcome"
        job.hero_id = data.get("hero_id", "gremlin")
        job.text = data.get("message_text", "")
        job.status = "queued"
        job = await job_repo.create(job)

        task_id = await create_avatar_task(
            hero_id=job.hero_id,
            text=job.text,
            child_name=lead.child_name,
            job_id=job.id,
        )
        if task_id:
            job.fal_request_id = task_id
            job.status = "processing"
            await job_repo.update(job)
            msg = (
                "✅ *Спасибо!* Данные приняты, начинаем генерацию.\n\n"
                f"Герой: *{data.get('hero_id', 'gremlin')}*\n"
                "Обычно это занимает 2–5 минут. Как только видео будет готово, мы пришлём его сюда."
            )
        else:
            logger.error(f"Failed to create fal.ai task for job {job.id} (Hero: {job.hero_id})", extra={"service": "form_engine"})
            msg = (
                "❌ *Ошибка генерации*\n\n"
                "К сожалению, сейчас не удалось запустить процесс создания видео. "
                "Проверьте правильность выбора героя или попробуйте позже.\n\n"
                "Попробуйте позже."
            )

        return FormSubmitResult(success=True, message=msg, data={"lead_id": lead.id, "job_id": job.id})
    except Exception as e:
        logger.error(f"Error processing video_greeting: {e}", extra={"service": "form_engine"})
        return FormSubmitResult(success=False, error=str(e))
