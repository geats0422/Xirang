from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Select, func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.learning_paths import (
    LearningPathNode,
    LearningPathStatus,
    LearningPathVersion,
    PathRegenerationRecord,
    PathTriggerType,
)


class LearningPathRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_ready_version(self, *, document_id: UUID, mode: str) -> LearningPathVersion | None:
        stmt: Select[tuple[LearningPathVersion]] = (
            select(LearningPathVersion)
            .where(
                LearningPathVersion.document_id == document_id,
                LearningPathVersion.mode == mode,
                LearningPathVersion.status == LearningPathStatus.READY,
            )
            .order_by(LearningPathVersion.version_no.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_version(self, *, document_id: UUID, mode: str) -> LearningPathVersion | None:
        stmt: Select[tuple[LearningPathVersion]] = (
            select(LearningPathVersion)
            .where(LearningPathVersion.document_id == document_id, LearningPathVersion.mode == mode)
            .order_by(LearningPathVersion.version_no.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_generating_version(self, *, document_id: UUID, mode: str) -> LearningPathVersion | None:
        stmt: Select[tuple[LearningPathVersion]] = (
            select(LearningPathVersion)
            .where(
                LearningPathVersion.document_id == document_id,
                LearningPathVersion.mode == mode,
                LearningPathVersion.status.in_([LearningPathStatus.PENDING, LearningPathStatus.GENERATING]),
            )
            .order_by(LearningPathVersion.version_no.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_next_version_no(self, *, document_id: UUID, mode: str) -> int:
        stmt = select(func.max(LearningPathVersion.version_no)).where(
            LearningPathVersion.document_id == document_id,
            LearningPathVersion.mode == mode,
        )
        result = await self._session.execute(stmt)
        latest = result.scalar_one_or_none()
        return int(latest or 0) + 1

    async def create_version(
        self,
        *,
        document_id: UUID,
        mode: str,
        version_no: int,
        status: LearningPathStatus,
        trigger_type: PathTriggerType,
        generation_job_id: UUID | None = None,
    ) -> LearningPathVersion:
        item = LearningPathVersion(
            document_id=document_id,
            mode=mode,
            version_no=version_no,
            status=status,
            trigger_type=trigger_type,
            generation_job_id=generation_job_id,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def mark_version_ready(self, *, version_id: UUID) -> None:
        stmt: Select[tuple[LearningPathVersion]] = (
            select(LearningPathVersion).where(LearningPathVersion.id == version_id).limit(1)
        )
        result = await self._session.execute(stmt)
        item = result.scalar_one_or_none()
        if item is None:
            return
        item.status = LearningPathStatus.READY
        item.generated_at = datetime.now(UTC)
        item.error_code = None
        item.error_message = None
        item.failed_at = None
        item.failed_cleanup_at = None
        await self._session.flush()

    async def mark_version_failed(self, *, version_id: UUID, error_code: str, error_message: str) -> None:
        stmt: Select[tuple[LearningPathVersion]] = (
            select(LearningPathVersion).where(LearningPathVersion.id == version_id).limit(1)
        )
        result = await self._session.execute(stmt)
        item = result.scalar_one_or_none()
        if item is None:
            return
        item.status = LearningPathStatus.FAILED
        item.error_code = error_code
        item.error_message = error_message
        item.failed_at = datetime.now(UTC)
        item.failed_cleanup_at = item.failed_at + timedelta(days=7)
        await self._session.flush()

    async def clear_nodes_for_version(self, *, path_version_id: UUID) -> None:
        stmt = select(LearningPathNode).where(LearningPathNode.path_version_id == path_version_id)
        result = await self._session.execute(stmt)
        for row in result.scalars().all():
            await self._session.delete(row)
        await self._session.flush()

    async def create_nodes(self, *, path_version_id: UUID, seeds: list[dict[str, object]]) -> None:
        key_to_node_id: dict[str, UUID] = {}
        for item in seeds:
            node_key = str(item["node_key"])
            parent_key_raw = item.get("parent_key")
            parent_node_id = key_to_node_id.get(str(parent_key_raw)) if parent_key_raw else None
            node = LearningPathNode(
                path_version_id=path_version_id,
                node_type=item["node_type"],
                node_key=node_key,
                parent_node_id=parent_node_id,
                is_mode_branch=bool(item.get("is_mode_branch", False)),
                title=str(item["title"]),
                description=str(item.get("description") or ""),
                sort_order=self._to_int(item.get("sort_order"), default=0),
                unlock_rule_json=item.get("unlock_rule_json") or {},
                question_selector_json=item.get("question_selector_json") or {},
                meta_json=item.get("meta_json") or {},
            )
            self._session.add(node)
            await self._session.flush()
            key_to_node_id[node_key] = node.id

    async def list_nodes(self, *, path_version_id: UUID) -> list[LearningPathNode]:
        stmt: Select[tuple[LearningPathNode]] = (
            select(LearningPathNode)
            .where(LearningPathNode.path_version_id == path_version_id)
            .order_by(LearningPathNode.sort_order.asc(), LearningPathNode.node_key.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_recent_regenerations(self, *, document_id: UUID, mode: str, since: datetime) -> int:
        stmt = select(func.count()).select_from(PathRegenerationRecord).where(
            PathRegenerationRecord.document_id == document_id,
            PathRegenerationRecord.mode == mode,
            PathRegenerationRecord.created_at >= since,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def create_regeneration_record(
        self,
        *,
        document_id: UUID,
        mode: str,
        user_id: UUID,
        path_version_id: UUID,
    ) -> PathRegenerationRecord:
        record = PathRegenerationRecord(
            document_id=document_id,
            mode=mode,
            user_id=user_id,
            path_version_id=path_version_id,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    @staticmethod
    def _to_int(value: object | None, *, default: int) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default
