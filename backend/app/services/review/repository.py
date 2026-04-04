"""Review repository implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select, update

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.review import (
    FeedbackStatus,
    Mistake,
    QuestionFeedback,
    ReviewRuleCandidate,
    RuleCandidateStatus,
)
from app.services.review.schemas import FeedbackCreate, FeedbackRecord, MistakeRecord


class ReviewRepository:
    """SQLAlchemy implementation of ReviewRepositoryProtocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_feedback(
        self,
        *,
        user_id: UUID,
        feedback: FeedbackCreate,
    ) -> FeedbackRecord:
        """Create a new feedback record."""
        db_feedback = QuestionFeedback(
            user_id=user_id,
            question_id=feedback.question_id,
            document_id=feedback.document_id,
            run_id=feedback.run_id,
            feedback_type=feedback.feedback_type,
            detail_text=feedback.detail_text,
            status=FeedbackStatus.OPEN,
        )
        self._session.add(db_feedback)
        await self._session.flush()
        await self._session.refresh(db_feedback)

        return FeedbackRecord(
            id=db_feedback.id,
            user_id=db_feedback.user_id,
            question_id=db_feedback.question_id,
            document_id=db_feedback.document_id,
            run_id=db_feedback.run_id,
            feedback_type=db_feedback.feedback_type,
            detail_text=db_feedback.detail_text,
            status=db_feedback.status,
            created_at=db_feedback.created_at,
        )

    async def get_feedback(self, feedback_id: UUID) -> FeedbackRecord | None:
        """Get a feedback record by ID."""
        stmt = select(QuestionFeedback).where(QuestionFeedback.id == feedback_id)
        result = await self._session.execute(stmt)
        db_feedback = result.scalar_one_or_none()

        if db_feedback is None:
            return None

        return FeedbackRecord(
            id=db_feedback.id,
            user_id=db_feedback.user_id,
            question_id=db_feedback.question_id,
            document_id=db_feedback.document_id,
            run_id=db_feedback.run_id,
            feedback_type=db_feedback.feedback_type,
            detail_text=db_feedback.detail_text,
            status=db_feedback.status,
            created_at=db_feedback.created_at,
        )

    async def list_feedback_by_user(
        self,
        user_id: UUID,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedbackRecord]:
        """List feedback records for a user."""
        stmt = select(QuestionFeedback).where(QuestionFeedback.user_id == user_id)

        if status:
            stmt = stmt.where(QuestionFeedback.status == status)

        stmt = stmt.order_by(QuestionFeedback.created_at.desc()).offset(offset).limit(limit)

        result = await self._session.execute(stmt)
        db_feedbacks = result.scalars().all()

        return [
            FeedbackRecord(
                id=f.id,
                user_id=f.user_id,
                question_id=f.question_id,
                document_id=f.document_id,
                run_id=f.run_id,
                feedback_type=f.feedback_type,
                detail_text=f.detail_text,
                status=f.status,
                created_at=f.created_at,
            )
            for f in db_feedbacks
        ]

    async def create_mistake(
        self,
        *,
        user_id: UUID,
        question_id: UUID,
        document_id: UUID,
        run_id: UUID,
        explanation: str | None = None,
    ) -> MistakeRecord:
        """Create a new mistake record."""
        db_mistake = Mistake(
            user_id=user_id,
            question_id=question_id,
            document_id=document_id,
            run_id=run_id,
            explanation=explanation,
        )
        self._session.add(db_mistake)
        await self._session.flush()
        await self._session.refresh(db_mistake)

        return MistakeRecord(
            id=db_mistake.id,
            user_id=db_mistake.user_id,
            question_id=db_mistake.question_id,
            document_id=db_mistake.document_id,
            run_id=db_mistake.run_id,
            explanation=db_mistake.explanation,
            created_at=db_mistake.created_at,
        )

    async def get_mistake(self, mistake_id: UUID) -> MistakeRecord | None:
        """Get a mistake record by ID."""
        stmt = select(Mistake).where(Mistake.id == mistake_id)
        result = await self._session.execute(stmt)
        db_mistake = result.scalar_one_or_none()

        if db_mistake is None:
            return None

        return MistakeRecord(
            id=db_mistake.id,
            user_id=db_mistake.user_id,
            question_id=db_mistake.question_id,
            document_id=db_mistake.document_id,
            run_id=db_mistake.run_id,
            explanation=db_mistake.explanation,
            created_at=db_mistake.created_at,
        )

    async def list_mistakes_by_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MistakeRecord]:
        """List mistake records for a user."""
        stmt = (
            select(Mistake)
            .where(Mistake.user_id == user_id)
            .order_by(Mistake.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        db_mistakes = result.scalars().all()

        return [
            MistakeRecord(
                id=m.id,
                user_id=m.user_id,
                question_id=m.question_id,
                document_id=m.document_id,
                run_id=m.run_id,
                explanation=m.explanation,
                created_at=m.created_at,
            )
            for m in db_mistakes
        ]

    async def update_feedback_status(self, feedback_id: UUID, status: str) -> None:
        """Update the status of a feedback record."""
        stmt = (
            update(QuestionFeedback).where(QuestionFeedback.id == feedback_id).values(status=status)
        )
        await self._session.execute(stmt)

    async def create_rule_candidate(
        self,
        *,
        source_job_id: UUID,
        rule_type: str,
        title: str,
        content: str,
    ) -> dict[str, str]:
        """Create a rule candidate."""
        db_candidate = ReviewRuleCandidate(
            source_job_id=source_job_id,
            rule_type=rule_type,
            title=title,
            content=content,
            status=RuleCandidateStatus.PENDING_REVIEW,
        )
        self._session.add(db_candidate)
        await self._session.flush()
        await self._session.refresh(db_candidate)

        return {
            "id": str(db_candidate.id),
            "rule_type": db_candidate.rule_type,
            "title": db_candidate.title,
            "content": db_candidate.content,
            "status": db_candidate.status,
            "source_job_id": str(db_candidate.source_job_id),
        }

    async def list_rule_candidates(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, str]]:
        """List rule candidates."""
        stmt = select(ReviewRuleCandidate)

        if status:
            stmt = stmt.where(ReviewRuleCandidate.status == status)

        stmt = stmt.order_by(ReviewRuleCandidate.created_at.desc()).limit(limit)

        result = await self._session.execute(stmt)
        db_candidates = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "rule_type": c.rule_type,
                "title": c.title,
                "content": c.content,
                "status": c.status,
                "source_job_id": str(c.source_job_id),
            }
            for c in db_candidates
        ]
