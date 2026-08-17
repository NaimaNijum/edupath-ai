from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.memory import MemoryService


class FakeMemoryRepository:
    def __init__(self) -> None:
        self.profile_calls: list[UUID] = []

    async def list_for_profile(self, session, profile_id):
        self.profile_calls.append(profile_id)
        return [SimpleNamespace(id=UUID("11111111-1111-1111-1111-111111111111"), profile_id=profile_id, memory_type="profile", scope="long_term", content={"note": "remember"}, source="seed", created_at="2026-08-16T00:00:00Z", updated_at="2026-08-16T00:00:00Z")]


class FakeLongTermMemory:
    async def retrieve_context(self, session, *, profile_id, query_text, limit=5):
        return [{"profile_id": str(profile_id), "query_text": query_text, "limit": limit}]


@pytest.mark.asyncio
async def test_memory_service_loads_context() -> None:
    service = MemoryService(repository=FakeMemoryRepository(), long_term_memory=FakeLongTermMemory())
    result = await service.load_context(SimpleNamespace(), UUID("11111111-1111-1111-1111-111111111111"), "funded phd", limit=3)

    assert result[0]["query_text"] == "funded phd"
