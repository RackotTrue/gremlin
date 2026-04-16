"""
fal.ai — сервис генерации видео-открыток (VEED Fabric 1.0, image+audio → talking video).

Поток:
1. Генерирует аудио через OpenAI TTS (голос nova, модель tts-1).
2. Загружает аудио-файл в fal.storage, получает публичный URL.
3. Отправляет задачу в fal.ai queue (veed/fabric-1.0).
4. Возвращает request_id для последующего опроса статуса.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

import fal_client
from openai import AsyncOpenAI

from main.config.dynaconf_config import config_setting
from main.config.log_config import logger

# https://fal.ai/models/veed/fabric-1.0/api — image_url + audio_url + resolution
FAL_MODEL = "veed/fabric-1.0"
FABRIC_RESOLUTION = "480p"  # допустимо: 480p, 720p

# Лимит длины всего произносимого текста (TTS → видео ~10 с).
# Русская речь у TTS грубо ~12–18 символов/с; запас до ~190 символов на фразу целиком.
MAX_SPOKEN_SCRIPT_CHARS = 190


def build_spoken_script(child_name: str, text: str) -> str:
    """Текст, который уходит в TTS и в lip-sync (как в create_avatar_task)."""
    text = (text or "").strip()
    child_name = (child_name or "").strip()
    if child_name:
        return f"Привет, {child_name}! {text}".strip()
    return text


def _load_heroes() -> dict:
    """Загружает конфиг героев из resources/heroes/heroes.yml."""
    import yaml
    path = Path(__file__).resolve().parents[3] / "resources" / "heroes" / "heroes.yml"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("heroes", {})


def get_hero(hero_id: str) -> Optional[dict]:
    """Возвращает конфиг героя по id или None."""
    return _load_heroes().get(hero_id)


def get_heroes_for_form() -> dict:
    """Возвращает options_map для формы: hero_id -> display_name."""
    heroes = _load_heroes()
    return {
        hid: h.get("display_name", h.get("name", hid))
        for hid, h in heroes.items()
    }


def _fal_key() -> str:
    fal = getattr(config_setting, "FAL", None)
    if fal and getattr(fal, "API_KEY", None):
        return fal.API_KEY
    return os.environ.get("FAL_KEY", "")


def _openai_key() -> str:
    openai_cfg = getattr(config_setting, "OPENAI", None)
    if openai_cfg and getattr(openai_cfg, "API_KEY", None):
        return openai_cfg.API_KEY
    return os.environ.get("OPENAI_API_KEY", "")


async def _create_tts_audio(script: str, *, job_id: int) -> Optional[str]:
    """
    Генерирует аудио через OpenAI TTS (nova, tts-1),
    загружает mp3 в fal.storage и возвращает публичный URL.
    """
    openai_api_key = _openai_key()
    if not openai_api_key:
        logger.warning("OPENAI API_KEY not configured, skipping TTS", extra={"service": "fal_video"})
        return None

    fal_key = _fal_key()
    if not fal_key:
        logger.warning("FAL API_KEY not configured, skipping TTS upload", extra={"service": "fal_video"})
        return None

    try:
        client = AsyncOpenAI(api_key=openai_api_key)
        response = await client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=script,
            response_format="mp3",
        )
        audio_bytes = response.content
    except Exception as e:
        logger.exception(f"OpenAI TTS failed for job {job_id}: {e}", extra={"service": "fal_video"})
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        os.environ["FAL_KEY"] = fal_key
        audio_url = fal_client.upload_file(tmp_path)
        logger.info(f"TTS audio uploaded for job {job_id}: {audio_url}", extra={"service": "fal_video"})
        return audio_url
    except Exception as e:
        logger.exception(f"fal.storage upload failed for job {job_id}: {e}", extra={"service": "fal_video"})
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def create_avatar_task(
    *,
    hero_id: str,
    text: str,
    child_name: str,
    job_id: int,
) -> Optional[str]:
    """
    Создаёт задачу генерации видео-открытки:
    1) генерирует аудио через OpenAI TTS,
    2) загружает его в fal.storage,
    3) отправляет задачу в fal.ai queue.

    :return: request_id от fal.ai или None при ошибке
    """
    hero = get_hero(hero_id)
    if not hero:
        logger.error(f"Hero '{hero_id}' not found in heroes.yml", extra={"service": "fal_video"})
        return None

    fal_key = _fal_key()
    if not fal_key:
        logger.warning("FAL API_KEY not configured, skipping video generation", extra={"service": "fal_video"})
        return None

    image_url = hero.get("image_url", "")
    if not image_url:
        logger.error(f"Hero '{hero_id}' has no image_url", extra={"service": "fal_video"})
        return None

    script = build_spoken_script(child_name, text)
    if len(script) > MAX_SPOKEN_SCRIPT_CHARS:
        logger.warning(
            f"Spoken script too long ({len(script)} > {MAX_SPOKEN_SCRIPT_CHARS}) for job {job_id}",
            extra={"service": "fal_video"},
        )
        return None

    audio_url = await _create_tts_audio(script, job_id=job_id)
    if not audio_url:
        return None

    try:
        os.environ["FAL_KEY"] = fal_key
        handle = fal_client.submit(
            FAL_MODEL,
            arguments={
                "image_url": image_url,
                "audio_url": audio_url,
                "resolution": FABRIC_RESOLUTION,
            },
        )
        request_id = handle.request_id
        logger.info(f"fal.ai task submitted: request_id={request_id} for job {job_id}", extra={"service": "fal_video"})
        return request_id
    except Exception as e:
        logger.exception(f"fal.ai submit failed for job {job_id}: {e}", extra={"service": "fal_video"})
        return None


async def get_task_status(request_id: str) -> tuple[str, Optional[str]]:
    """
    Проверяет статус задачи fal.ai.
    :return: (status, result_url)
             status: pending | succeed | failed
             result_url: URL видео при succeed, иначе None
    """
    fal_key = _fal_key()
    if not fal_key:
        return "failed", None

    try:
        os.environ["FAL_KEY"] = fal_key
        status = fal_client.status(FAL_MODEL, request_id, with_logs=False)
        state = type(status).__name__  # Queued | InProgress | Completed

        if state == "Completed":
            result = fal_client.result(FAL_MODEL, request_id)
            video_url = result.get("video", {}).get("url") if isinstance(result, dict) else None
            if video_url:
                logger.info(f"fal.ai task {request_id} completed, video_url={video_url}", extra={"service": "fal_video"})
                return "succeed", video_url
            logger.error(f"fal.ai task {request_id} completed but no video URL in result: {result}", extra={"service": "fal_video"})
            return "failed", None

        if state in ("Queued", "InProgress"):
            return "pending", None

        logger.warning(f"fal.ai task {request_id} unknown state: {state}", extra={"service": "fal_video"})
        return "pending", None

    except Exception as e:
        logger.warning(f"fal.ai status check failed for {request_id}: {e}", extra={"service": "fal_video"})
        return "pending", None
