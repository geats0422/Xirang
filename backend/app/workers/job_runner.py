from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.db.models.documents import Job
    from app.workers.registry import JobHandler, JobRegistry


class JobRepositoryProtocol(Protocol):
    async def claim_pending_job(self, *, queue_name: str) -> Job | None: ...
    async def mark_completed(self, *, job_id: str) -> None: ...
    async def mark_failed(
        self,
        *,
        job_id: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None: ...
    async def increment_attempt(self, *, job_id: str) -> None: ...


class JobRunner:
    def __init__(self, *, repository: JobRepositoryProtocol, registry: JobRegistry) -> None:
        self._repository = repository
        self._registry = registry

    async def run_one(self, *, queue_name: str = "default") -> bool:
        job = await self._repository.claim_pending_job(queue_name=queue_name)
        if job is None:
            return False

        handler = self._registry.get(job.job_type)
        if handler is None:
            await self._repository.increment_attempt(job_id=str(job.id))
            await self._repository.mark_failed(
                job_id=str(job.id),
                error_code="UNSUPPORTED_JOB_TYPE",
                error_message=f"No handler registered for job type: {job.job_type}",
            )
            return True

        try:
            await self._execute_handler(handler, job)
            await self._repository.mark_completed(job_id=str(job.id))
            return True
        except Exception as e:
            await self._repository.increment_attempt(job_id=str(job.id))
            error_message = str(e)
            error_code = None

            if job.attempt_count + 1 >= job.max_attempts:
                error_code = "MAX_ATTEMPTS_EXCEEDED"

            await self._repository.mark_failed(
                job_id=str(job.id),
                error_code=error_code,
                error_message=error_message,
            )
            return True

    async def _execute_handler(self, handler: JobHandler, job: Job) -> None:
        result = handler(job)
        if result is not None:
            await result
