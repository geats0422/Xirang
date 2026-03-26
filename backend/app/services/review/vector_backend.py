from __future__ import annotations

from uuid import UUID


class PgvectorBackend:
    async def find_similar_mistakes(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
        threshold: float = 0.8,
    ) -> list[tuple[UUID, float]]:
        return []

    async def store(self, mistake_id: UUID, embedding: list[float]) -> None:
        pass
