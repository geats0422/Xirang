from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import func, select

from app.db.models.auth import User
from app.db.models.documents import Document
from app.db.models.profile import Profile
from app.db.models.questions import Question
from app.db.models.runs import Run, RunStatus, Settlement

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class LeaderboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_global_leaderboard(self, limit: int, offset: int = 0) -> list[Any]:
        stmt = (
            select(
                Settlement.user_id,
                func.coalesce(Profile.display_name, User.username).label("display_name"),
                func.coalesce(func.sum(Settlement.xp_gained), 0).label("total_xp"),
            )
            .join(User, User.id == Settlement.user_id)
            .outerjoin(Profile, Profile.user_id == Settlement.user_id)
            .group_by(Settlement.user_id, Profile.display_name, User.username)
            .order_by(func.sum(Settlement.xp_gained).desc(), Settlement.user_id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def count_global_leaderboard_users(self) -> int:
        stmt = select(func.count(func.distinct(Settlement.user_id)))
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def get_user_total_xp(self, user_id: UUID) -> Any | None:
        stmt = (
            select(
                User.id.label("user_id"),
                func.coalesce(Profile.display_name, User.username).label("display_name"),
                func.coalesce(func.sum(Settlement.xp_gained), 0).label("total_xp"),
            )
            .select_from(User)
            .outerjoin(Profile, Profile.user_id == User.id)
            .outerjoin(Settlement, Settlement.user_id == User.id)
            .where(User.id == user_id)
            .group_by(User.id, Profile.display_name, User.username)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.first()

    async def get_user_rank(self, user_id: UUID, total_xp: int) -> int:
        leaderboard_subquery = (
            select(
                Settlement.user_id.label("user_id"),
                func.coalesce(func.sum(Settlement.xp_gained), 0).label("total_xp"),
            )
            .group_by(Settlement.user_id)
            .subquery()
        )

        outrank_stmt = (
            select(func.count())
            .select_from(leaderboard_subquery)
            .where(
                (leaderboard_subquery.c.total_xp > total_xp)
                | (
                    (leaderboard_subquery.c.total_xp == total_xp)
                    & (leaderboard_subquery.c.user_id < user_id)
                )
            )
        )
        outrank_result = await self._session.execute(outrank_stmt)
        outrank_count = int(outrank_result.scalar_one() or 0)

        has_user_stmt = (
            select(func.count())
            .select_from(leaderboard_subquery)
            .where(leaderboard_subquery.c.user_id == user_id)
        )
        has_user_result = await self._session.execute(has_user_stmt)
        has_user = int(has_user_result.scalar_one() or 0) > 0
        if not has_user:
            total_users = await self.count_global_leaderboard_users()
            return total_users + 1

        return outrank_count + 1

    async def get_daily_focus_documents(
        self,
        *,
        user_id: UUID,
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list[Any]:
        stmt = (
            select(
                Run.document_id.label("document_id"),
                Document.title.label("title"),
                func.count(Run.id).label("completed_runs"),
                func.coalesce(func.sum(Run.correct_answers), 0).label("correct_sum"),
                func.coalesce(func.sum(Run.total_questions), 0).label("total_sum"),
                func.max(Run.ended_at).label("last_ended_at"),
            )
            .join(Document, Document.id == Run.document_id)
            .where(
                Run.user_id == user_id,
                Run.status == RunStatus.COMPLETED,
                Run.document_id.is_not(None),
                Run.ended_at.is_not(None),
                Run.ended_at >= start_at,
                Run.ended_at < end_at,
            )
            .group_by(Run.document_id, Document.title)
            .order_by(func.max(Run.ended_at).desc(), Run.document_id.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def get_document_semantic_context(self, document_id: UUID, limit: int = 5) -> list[str]:
        safe_limit = max(1, min(limit, 20))
        stmt = (
            select(Question.prompt)
            .where(Question.document_id == document_id)
            .order_by(Question.created_at.desc())
            .limit(safe_limit)
        )
        result = await self._session.execute(stmt)
        return [str(row[0]).strip() for row in result.all() if row and row[0]]
