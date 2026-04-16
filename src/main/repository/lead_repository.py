"""Репозиторий для Lead (лид по QR/активации)."""

from main.config.db_config import AsyncSessionLocal
from main.model.lead_base import LeadBase


class LeadRepository:
    async def create(self, lead: LeadBase) -> LeadBase:
        async with AsyncSessionLocal() as session, session.begin():
            session.add(lead)
            await session.flush()
            await session.refresh(lead)
        return lead

    async def get_by_id(self, lead_id: int) -> LeadBase | None:
        async with AsyncSessionLocal() as session:
            return await session.get(LeadBase, lead_id)
