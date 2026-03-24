from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from app.db.models.documents import Job
    from app.services.review.facade import ReviewService

logger = logging.getLogger(__name__)


async def handle_feedback_learning_job(job: Job, *, review_service: ReviewService) -> None:
    payload = job.payload if isinstance(job.payload, dict) else {}
    raw_feedback_ids = payload.get("feedback_ids", [])
    feedback_ids = raw_feedback_ids if isinstance(raw_feedback_ids, list) else []

    if not feedback_ids:
        logger.warning(f"Job {job.id} has no feedback_ids in payload")
        return

    try:
        uuids = [UUID(fid) for fid in feedback_ids]
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid feedback_id format in job {job.id}: {e}")
        raise

    result = await review_service.summarize_feedback(uuids)

    summary = result.get("summary", "")
    suggestions = result.get("suggestions", [])

    job_id = UUID(str(job.id))
    for suggestion in suggestions[:5]:
        await review_service._repository.create_rule_candidate(
            source_job_id=job_id,
            rule_type=suggestion.get("type", "general"),
            title=suggestion.get("description", "Untitled")[:200],
            content=suggestion.get("description", ""),
        )

    logger.info(f"Feedback learning job {job.id} completed: {summary[:100]}")


def create_feedback_learning_handler(
    *,
    review_service: ReviewService,
) -> Callable[[Job], Coroutine[Any, Any, None]]:
    async def handler(job: Job) -> None:
        await handle_feedback_learning_job(job, review_service=review_service)

    return handler
