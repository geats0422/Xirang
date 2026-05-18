"""enable RLS on remaining public application tables

Revision ID: 20260516_remaining_rls
Revises: 20260516_sensitive_rls
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260516_remaining_rls"
down_revision: Union[str, Sequence[str], None] = "20260516_sensitive_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REMAINING_PUBLIC_TABLES = (
    "active_effects",
    "alembic_version",
    "community_comment_likes",
    "community_comments",
    "community_notifications",
    "community_post_favorites",
    "community_post_likes",
    "community_post_reports",
    "community_posts",
    "daily_reward_cap_usage",
    "document_ingestion_jobs",
    "document_pageindex_trees",
    "document_question_sets",
    "documents",
    "feedback_learning_jobs",
    "inventories",
    "jobs",
    "leaderboard_snapshots",
    "learning_path_nodes",
    "learning_path_progress",
    "learning_path_stages",
    "learning_path_versions",
    "learning_paths",
    "legend_review_progress",
    "mistake_embeddings",
    "mistakes",
    "notifications",
    "path_regeneration_records",
    "profiles",
    "quest_assignments",
    "question_feedback",
    "question_options",
    "questions",
    "review_rule_candidates",
    "run_answers",
    "run_questions",
    "runs",
    "seasons",
    "settlements",
    "shop_offers",
    "subscriptions",
    "use_records",
    "user_settings",
)


def upgrade() -> None:
    for table_name in REMAINING_PUBLIC_TABLES:
        op.execute(f'ALTER TABLE public."{table_name}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    for table_name in reversed(REMAINING_PUBLIC_TABLES):
        op.execute(f'ALTER TABLE public."{table_name}" DISABLE ROW LEVEL SECURITY')
