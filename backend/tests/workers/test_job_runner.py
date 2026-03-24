from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.db.models.documents import Job, JobStatus
from app.workers.job_runner import JobRunner
from app.workers.registry import JobRegistry


class FakeJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.claimed_ids: set[str] = set()

    def add_job(self, job: Job) -> None:
        self.jobs[str(job.id)] = job

    async def claim_pending_job(self, *, queue_name: str) -> Job | None:
        for job in self.jobs.values():
            if (
                job.status == JobStatus.PENDING
                and job.queue_name == queue_name
                and str(job.id) not in self.claimed_ids
            ):
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now(UTC)
                self.claimed_ids.add(str(job.id))
                return job
        return None

    async def mark_completed(self, *, job_id: str) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.finished_at = datetime.now(UTC)

    async def mark_failed(
        self, *, job_id: str, error_code: str | None = None, error_message: str | None = None
    ) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.finished_at = datetime.now(UTC)
            job.error_code = error_code
            job.error_message = error_message

    async def increment_attempt(self, *, job_id: str) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.attempt_count += 1


def make_job(
    *,
    job_type: str = "test_job",
    status: JobStatus = JobStatus.PENDING,
    queue_name: str = "default",
    attempt_count: int = 0,
    max_attempts: int = 3,
) -> Job:
    return Job(
        id=uuid4(),
        job_type=job_type,
        queue_name=queue_name,
        status=status,
        attempt_count=attempt_count,
        max_attempts=max_attempts,
        payload={},
        available_at=datetime.now(UTC),
    )


class TestJobRegistry:
    def test_register_handler_stores_callable(self) -> None:
        registry = JobRegistry()

        async def handler(job: Job) -> None:
            pass

        registry.register("test_job", handler)
        assert registry.get("test_job") == handler

    def test_get_returns_none_for_unknown_job_type(self) -> None:
        registry = JobRegistry()
        assert registry.get("unknown") is None


class TestJobRunner:
    @pytest.mark.asyncio
    async def test_claim_pending_job_returns_job_from_queue(self) -> None:
        repository = FakeJobRepository()
        job = make_job()
        repository.add_job(job)

        claimed = await repository.claim_pending_job(queue_name="default")

        assert claimed is not None
        assert claimed.id == job.id
        assert claimed.status == JobStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_claim_returns_none_when_no_pending_jobs(self) -> None:
        repository = FakeJobRepository()

        claimed = await repository.claim_pending_job(queue_name="default")

        assert claimed is None

    @pytest.mark.asyncio
    async def test_runner_executes_registered_handler(self) -> None:
        repository = FakeJobRepository()
        job = make_job(job_type="echo")
        repository.add_job(job)

        executed: list[Job] = []

        async def echo_handler(j: Job) -> None:
            executed.append(j)

        registry = JobRegistry()
        registry.register("echo", echo_handler)

        runner = JobRunner(repository=repository, registry=registry)
        await runner.run_one(queue_name="default")

        assert len(executed) == 1
        assert executed[0].id == job.id

    @pytest.mark.asyncio
    async def test_runner_marks_job_completed_after_success(self) -> None:
        repository = FakeJobRepository()
        job = make_job(job_type="success_job")
        repository.add_job(job)

        registry = JobRegistry()
        registry.register("success_job", AsyncMock())

        runner = JobRunner(repository=repository, registry=registry)
        await runner.run_one(queue_name="default")

        assert job.status == JobStatus.COMPLETED
        assert job.finished_at is not None

    @pytest.mark.asyncio
    async def test_runner_marks_job_failed_after_exception(self) -> None:
        repository = FakeJobRepository()
        job = make_job(job_type="failing_job")
        repository.add_job(job)

        async def failing_handler(j: Job) -> None:
            raise RuntimeError("boom")

        registry = JobRegistry()
        registry.register("failing_job", failing_handler)

        runner = JobRunner(repository=repository, registry=registry)
        await runner.run_one(queue_name="default")

        assert job.status == JobStatus.FAILED
        assert job.error_message == "boom"

    @pytest.mark.asyncio
    async def test_runner_skips_job_with_no_handler(self) -> None:
        repository = FakeJobRepository()
        job = make_job(job_type="orphan_job")
        repository.add_job(job)

        registry = JobRegistry()

        runner = JobRunner(repository=repository, registry=registry)
        await runner.run_one(queue_name="default")

        assert job.status == JobStatus.FAILED
        assert job.error_code == "UNSUPPORTED_JOB_TYPE"

    @pytest.mark.asyncio
    async def test_runner_respects_max_attempts(self) -> None:
        repository = FakeJobRepository()
        job = make_job(job_type="retry_job", attempt_count=2, max_attempts=3)
        repository.add_job(job)

        async def failing_handler(j: Job) -> None:
            raise RuntimeError("still failing")

        registry = JobRegistry()
        registry.register("retry_job", failing_handler)

        runner = JobRunner(repository=repository, registry=registry)
        await runner.run_one(queue_name="default")

        assert job.status == JobStatus.FAILED
        assert job.error_code == "MAX_ATTEMPTS_EXCEEDED"
