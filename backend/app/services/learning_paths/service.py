from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from app.db.models.learning_paths import LearningPathNodeType, LearningPathStatus, PathTriggerType
from app.services.learning_paths.generator import LearningPathGenerator


class LearningPathRepositoryProtocol(Protocol):
    async def get_latest_ready_version(self, *, document_id: UUID, mode: str) -> Any | None: ...

    async def get_generating_version(self, *, document_id: UUID, mode: str) -> Any | None: ...

    async def get_latest_version(self, *, document_id: UUID, mode: str) -> Any | None: ...

    async def get_next_version_no(self, *, document_id: UUID, mode: str) -> int: ...

    async def create_version(
        self,
        *,
        document_id: UUID,
        mode: str,
        version_no: int,
        status: LearningPathStatus,
        trigger_type: PathTriggerType,
    ) -> Any: ...

    async def mark_version_failed(
        self,
        *,
        version_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None: ...

    async def count_recent_regenerations(
        self, *, document_id: UUID, mode: str, since: datetime
    ) -> int: ...

    async def create_regeneration_record(
        self,
        *,
        document_id: UUID,
        mode: str,
        user_id: UUID,
        path_version_id: UUID,
    ) -> None: ...

    async def clear_nodes_for_version(self, *, path_version_id: UUID) -> None: ...

    async def create_nodes(self, *, path_version_id: UUID, seeds: list[dict[str, Any]]) -> None: ...

    async def mark_version_ready(self, *, version_id: UUID) -> None: ...

    async def list_nodes(self, *, path_version_id: UUID) -> list[Any]: ...

    async def commit(self) -> None: ...


class LearningPathServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class PathGenerationInProgressError(LearningPathServiceError):
    status_code = 409


class PathGenerationFailedError(LearningPathServiceError):
    status_code = 409


class RegenerationLimitExceededError(LearningPathServiceError):
    status_code = 429


class LearningPathService:
    def __init__(
        self,
        *,
        repository: LearningPathRepositoryProtocol,
        generator: LearningPathGenerator | None = None,
    ) -> None:
        self._repository = repository
        self._generator = generator or LearningPathGenerator()

    async def get_path_options(self, *, document_id: UUID, mode: str) -> dict[str, Any]:
        mode_value = mode.lower()
        ready_version = await self._repository.get_latest_ready_version(
            document_id=document_id, mode=mode_value
        )
        if ready_version is not None:
            options = await self._build_options(ready_version.id)
            return {
                "generation_status": "ready",
                "mode": mode_value,
                "path_version_id": str(ready_version.id),
                "version_no": ready_version.version_no,
                "options": options,
            }

        generating_version = await self._repository.get_generating_version(
            document_id=document_id,
            mode=mode_value,
        )
        if generating_version is not None:
            return {
                "generation_status": "generating",
                "mode": mode_value,
                "path_version_id": str(generating_version.id),
                "version_no": generating_version.version_no,
                "job_id": None
                if generating_version.generation_job_id is None
                else str(generating_version.generation_job_id),
                "options": [],
            }

        latest_version = await self._repository.get_latest_version(
            document_id=document_id, mode=mode_value
        )
        if latest_version is not None and latest_version.status == LearningPathStatus.FAILED:
            raise PathGenerationFailedError(
                latest_version.error_message or "Path generation failed. Please retry generation."
            )

        version_no = await self._repository.get_next_version_no(
            document_id=document_id, mode=mode_value
        )
        version = await self._repository.create_version(
            document_id=document_id,
            mode=mode_value,
            version_no=version_no,
            status=LearningPathStatus.GENERATING,
            trigger_type=PathTriggerType.AUTO_LAZY,
        )
        await self._repository.commit()

        try:
            await self._materialize_path(
                version_id=version.id, mode=mode_value, version_no=version.version_no
            )
            await self._repository.commit()
        except Exception as error:
            await self._repository.mark_version_failed(
                version_id=version.id,
                error_code="PATH_GENERATION_FAILED",
                error_message=str(error),
            )
            await self._repository.commit()

        return {
            "generation_status": "generating",
            "mode": mode_value,
            "path_version_id": str(version.id),
            "version_no": version.version_no,
            "job_id": None,
            "options": [],
        }

    async def regenerate_path(
        self, *, document_id: UUID, mode: str, user_id: UUID
    ) -> dict[str, Any]:
        mode_value = mode.lower()
        active = await self._repository.get_generating_version(
            document_id=document_id, mode=mode_value
        )
        if active is not None:
            raise PathGenerationInProgressError("Path generation already in progress")

        window_start = datetime.now(UTC) - timedelta(hours=24)
        regenerate_count = await self._repository.count_recent_regenerations(
            document_id=document_id,
            mode=mode_value,
            since=window_start,
        )
        if regenerate_count >= 3:
            raise RegenerationLimitExceededError("Path regeneration limit reached (3 / 24h)")

        version_no = await self._repository.get_next_version_no(
            document_id=document_id, mode=mode_value
        )
        version = await self._repository.create_version(
            document_id=document_id,
            mode=mode_value,
            version_no=version_no,
            status=LearningPathStatus.GENERATING,
            trigger_type=PathTriggerType.REGENERATE,
        )
        await self._repository.create_regeneration_record(
            document_id=document_id,
            mode=mode_value,
            user_id=user_id,
            path_version_id=version.id,
        )
        await self._repository.commit()

        try:
            await self._materialize_path(
                version_id=version.id, mode=mode_value, version_no=version.version_no
            )
            await self._repository.commit()
        except Exception as error:
            await self._repository.mark_version_failed(
                version_id=version.id,
                error_code="PATH_REGENERATE_FAILED",
                error_message=str(error),
            )
            await self._repository.commit()

        return {
            "generation_status": "generating",
            "mode": mode_value,
            "path_version_id": str(version.id),
            "next_version_no": version.version_no,
            "job_id": None,
        }

    async def _materialize_path(self, *, version_id: UUID, mode: str, version_no: int) -> None:
        await self._repository.clear_nodes_for_version(path_version_id=version_id)
        seeds = self._generator.build_nodes(mode=mode, version_no=version_no)
        await self._repository.create_nodes(path_version_id=version_id, seeds=seeds)
        await self._repository.mark_version_ready(version_id=version_id)

    async def _build_options(self, path_version_id: UUID) -> list[dict[str, Any]]:
        nodes = await self._repository.list_nodes(path_version_id=path_version_id)
        options: list[dict[str, Any]] = []
        for node in nodes:
            if node.node_type != LearningPathNodeType.LEVEL:
                continue
            meta = node.meta_json or {}
            raw_goal = meta.get("goal_total", 10)
            goal_total = int(raw_goal) if isinstance(raw_goal, int) else 10
            options.append(
                {
                    "path_id": node.node_key,
                    "label": str(meta.get("label") or node.title),
                    "kind": str(meta.get("kind") or "level"),
                    "description": node.description or "",
                    "goal_total": goal_total,
                    "path_version_id": str(path_version_id),
                    "level_node_id": str(node.id),
                }
            )
        return options
