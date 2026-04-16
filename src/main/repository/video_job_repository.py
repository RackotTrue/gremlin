"""Репозиторий для VideoJob (задачи генерации видео)."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from main.config.db_config import AsyncSessionLocal
from main.model.video_job_base import VideoJobBase


class VideoJobRepository:
    async def create(self, job: VideoJobBase) -> VideoJobBase:
        async with AsyncSessionLocal() as session, session.begin():
            session.add(job)
            await session.flush()
            await session.refresh(job)
        return job

    async def get_by_id(self, job_id: int) -> VideoJobBase | None:
        async with AsyncSessionLocal() as session:
            return await session.get(VideoJobBase, job_id)

    async def get_pending_by_fal_request_id(self, fal_request_id: str) -> VideoJobBase | None:
        async with AsyncSessionLocal() as session:
            r = await session.execute(
                select(VideoJobBase).where(
                    VideoJobBase.fal_request_id == fal_request_id,
                    VideoJobBase.status.in_(("queued", "processing")),
                )
            )
            return r.scalar_one_or_none()

    async def get_all_pending(self) -> list[VideoJobBase]:
        async with AsyncSessionLocal() as session:
            r = await session.execute(
                select(VideoJobBase)
                .options(selectinload(VideoJobBase.lead))
                .where(
                    VideoJobBase.status.in_(("queued", "processing")),
                    VideoJobBase.fal_request_id.isnot(None),
                )
            )
            return list(r.scalars().all())

    async def update(self, job: VideoJobBase) -> VideoJobBase:
        async with AsyncSessionLocal() as session, session.begin():
            await session.merge(job)
        return job
