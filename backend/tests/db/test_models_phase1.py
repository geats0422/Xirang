from collections.abc import Iterable

import app.db.models  # noqa: F401
from app.db.base import Base


def get_table(table_name: str):
    return Base.metadata.tables[table_name]


def get_column_names(table_name: str) -> set[str]:
    return set(get_table(table_name).columns.keys())


def get_foreign_key_targets(table_name: str) -> set[tuple[str, str, str]]:
    return {
        (foreign_key.parent.name, foreign_key.column.table.name, foreign_key.column.name)
        for foreign_key in get_table(table_name).foreign_keys
    }


def get_unique_index_columns(table_name: str) -> set[tuple[str, ...]]:
    return {
        tuple(column.name for column in index.columns)
        for index in get_table(table_name).indexes
        if index.unique
    }


def get_unique_constraint_columns(table_name: str) -> set[tuple[str, ...]]:
    return {
        tuple(column.name for column in constraint.columns)
        for constraint in get_table(table_name).constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }


def assert_columns_present(table_name: str, expected_columns: Iterable[str]) -> None:
    assert set(expected_columns) <= get_column_names(table_name)


def test_phase1_tables_and_reserved_extension_tables_are_registered() -> None:
    expected_tables = {
        "users",
        "auth_credentials",
        "auth_sessions",
        "auth_identities",
        "profiles",
        "user_settings",
        "documents",
        "document_ingestion_jobs",
        "document_pageindex_trees",
        "document_question_sets",
        "questions",
        "question_options",
        "runs",
        "run_questions",
        "run_answers",
        "settlements",
        "mistakes",
        "mistake_embeddings",
        "question_feedback",
        "feedback_learning_jobs",
        "review_rule_candidates",
        "wallets",
        "wallet_ledger",
        "inventories",
        "purchase_records",
        "leaderboard_snapshots",
        "jobs",
        "audit_logs",
        "payment_transactions",
        "seasons",
        "subscriptions",
        "learning_path_versions",
        "learning_path_nodes",
        "learning_path_progress",
        "legend_review_progress",
        "path_regeneration_records",
        "daily_reward_cap_usage",
    }

    assert expected_tables <= set(Base.metadata.tables)


def test_auth_models_cover_email_password_and_oauth_extension_point() -> None:
    assert_columns_present(
        "users",
        {
            "id",
            "username",
            "username_normalized",
            "email",
            "email_normalized",
            "status",
            "last_login_at",
            "deleted_at",
            "created_at",
            "updated_at",
        },
    )
    assert_columns_present(
        "auth_credentials",
        {"user_id", "password_hash", "hash_version", "must_rotate", "password_changed_at"},
    )
    assert_columns_present(
        "auth_sessions",
        {
            "id",
            "user_id",
            "session_token_hash",
            "refresh_token_hash",
            "expires_at",
            "revoked_at",
        },
    )
    assert_columns_present(
        "auth_identities",
        {
            "id",
            "user_id",
            "provider_key",
            "provider_user_key",
            "provider_email",
            "unlinked_at",
        },
    )

    assert get_foreign_key_targets("auth_credentials") == {("user_id", "users", "id")}
    assert ("user_id", "users", "id") in get_foreign_key_targets("auth_sessions")
    assert ("user_id", "users", "id") in get_foreign_key_targets("auth_identities")


def test_document_and_question_models_cover_ingestion_and_generation_pipeline() -> None:
    assert_columns_present(
        "documents",
        {
            "id",
            "owner_user_id",
            "title",
            "file_name",
            "storage_path",
            "format",
            "file_size_bytes",
            "checksum_sha256",
            "ingest_status",
            "deleted_at",
        },
    )
    assert_columns_present(
        "jobs",
        {
            "id",
            "job_type",
            "queue_name",
            "status",
            "attempt_count",
            "max_attempts",
            "payload",
            "available_at",
        },
    )
    assert_columns_present(
        "document_ingestion_jobs",
        {"id", "job_id", "document_id", "ingest_version", "status", "error_code"},
    )
    assert_columns_present(
        "document_pageindex_trees",
        {"id", "document_id", "tree_key", "status", "indexed_at"},
    )
    assert_columns_present(
        "document_question_sets",
        {"id", "document_id", "generation_version", "status", "question_count"},
    )
    assert_columns_present(
        "questions",
        {
            "id",
            "question_set_id",
            "document_id",
            "question_type",
            "prompt",
            "explanation",
            "source_locator",
            "difficulty",
            "metadata",
        },
    )
    assert_columns_present(
        "question_options",
        {"id", "question_id", "option_key", "content", "is_correct", "sort_order"},
    )

    assert ("owner_user_id", "users", "id") in get_foreign_key_targets("documents")
    assert ("job_id", "jobs", "id") in get_foreign_key_targets("document_ingestion_jobs")
    assert ("document_id", "documents", "id") in get_foreign_key_targets("document_question_sets")
    assert ("question_set_id", "document_question_sets", "id") in get_foreign_key_targets(
        "questions"
    )
    assert ("question_id", "questions", "id") in get_foreign_key_targets("question_options")



def test_learning_path_and_subscription_models_cover_versioned_progress_schema() -> None:
    assert_columns_present(
        "subscriptions",
        {
            "id",
            "user_id",
            "plan_type",
            "status",
            "current_period_start",
            "current_period_end",
            "provider_txn_id",
        },
    )
    assert_columns_present(
        "learning_path_versions",
        {
            "id",
            "document_id",
            "mode",
            "version_no",
            "status",
            "trigger_type",
            "generator_config_json",
            "source_content_hash",
            "generation_job_id",
            "failed_cleanup_at",
        },
    )
    assert_columns_present(
        "learning_path_nodes",
        {
            "id",
            "path_version_id",
            "node_type",
            "node_key",
            "parent_node_id",
            "is_mode_branch",
            "title",
            "sort_order",
            "unlock_rule_json",
            "question_selector_json",
            "meta_json",
        },
    )
    assert_columns_present(
        "learning_path_progress",
        {
            "id",
            "user_id",
            "path_version_id",
            "node_id",
            "status",
            "first_completed_run_id",
            "completed_runs_count",
            "last_completed_at",
        },
    )
    assert_columns_present(
        "legend_review_progress",
        {
            "id",
            "user_id",
            "path_version_id",
            "unit_node_id",
            "legend_round_count",
            "last_legend_run_at",
        },
    )
    assert_columns_present(
        "path_regeneration_records",
        {
            "id",
            "document_id",
            "mode",
            "user_id",
            "path_version_id",
            "created_at",
        },
    )
    assert_columns_present(
        "daily_reward_cap_usage",
        {
            "id",
            "user_id",
            "date_key",
            "xp_legend_earned",
            "coin_legend_earned",
            "timezone_policy",
        },
    )

    assert ("user_id", "users", "id") in get_foreign_key_targets("subscriptions")
    assert ("document_id", "documents", "id") in get_foreign_key_targets("learning_path_versions")
    assert ("generation_job_id", "jobs", "id") in get_foreign_key_targets("learning_path_versions")
    assert ("path_version_id", "learning_path_versions", "id") in get_foreign_key_targets("learning_path_nodes")
    assert ("parent_node_id", "learning_path_nodes", "id") in get_foreign_key_targets("learning_path_nodes")
    assert ("user_id", "users", "id") in get_foreign_key_targets("learning_path_progress")
    assert ("path_version_id", "learning_path_versions", "id") in get_foreign_key_targets("learning_path_progress")
    assert ("node_id", "learning_path_nodes", "id") in get_foreign_key_targets("learning_path_progress")
    assert ("first_completed_run_id", "runs", "id") in get_foreign_key_targets("learning_path_progress")
    assert ("unit_node_id", "learning_path_nodes", "id") in get_foreign_key_targets("legend_review_progress")
    assert ("user_id", "users", "id") in get_foreign_key_targets("daily_reward_cap_usage")

    assert ("document_id", "mode", "version_no") in get_unique_constraint_columns(
        "learning_path_versions"
    )
    assert ("path_version_id", "node_key") in get_unique_constraint_columns("learning_path_nodes")
    assert ("user_id", "path_version_id", "node_id") in get_unique_constraint_columns(
        "learning_path_progress"
    )
    assert ("user_id", "path_version_id", "unit_node_id") in get_unique_constraint_columns(
        "legend_review_progress"
    )
    assert ("user_id", "date_key") in get_unique_constraint_columns("daily_reward_cap_usage")



def test_run_and_review_models_cover_settlement_and_feedback_loop() -> None:
    assert_columns_present(
        "runs",
        {
            "id",
            "user_id",
            "document_id",
            "source_question_set_id",
            "mode",
            "status",
            "score",
            "mode_state",
            "started_at",
            "ended_at",
        },
    )
    assert_columns_present(
        "run_questions",
        {"id", "run_id", "question_id", "sequence_no", "selection_reason"},
    )
    assert_columns_present(
        "run_answers",
        {
            "id",
            "run_id",
            "run_question_id",
            "question_id",
            "selected_option_ids",
            "free_text_answer",
            "is_correct",
            "answered_at",
        },
    )
    assert_columns_present(
        "settlements",
        {
            "id",
            "run_id",
            "user_id",
            "xp_gained",
            "coin_reward",
            "combo_count",
            "accuracy_pct",
            "settled_at",
        },
    )
    assert_columns_present(
        "mistakes",
        {"id", "user_id", "question_id", "document_id", "run_id", "explanation", "created_at"},
    )
    assert_columns_present(
        "mistake_embeddings",
        {"id", "mistake_id", "embedding", "embedding_model", "created_at"},
    )
    assert_columns_present(
        "question_feedback",
        {
            "id",
            "user_id",
            "question_id",
            "document_id",
            "run_id",
            "feedback_type",
            "detail_text",
            "status",
            "created_at",
        },
    )
    assert_columns_present(
        "feedback_learning_jobs",
        {"id", "job_id", "status", "feedback_count", "window_started_at", "window_ended_at"},
    )
    assert_columns_present(
        "review_rule_candidates",
        {"id", "source_job_id", "rule_type", "title", "content", "status"},
    )

    embedding_type_name = (
        get_table("mistake_embeddings").columns["embedding"].type.__class__.__name__
    )
    assert "VECTOR" in embedding_type_name.upper()

    assert ("run_id", "runs", "id") in get_foreign_key_targets("run_questions")
    assert ("run_question_id", "run_questions", "id") in get_foreign_key_targets("run_answers")
    assert ("run_id", "runs", "id") in get_foreign_key_targets("settlements")
    assert ("job_id", "jobs", "id") in get_foreign_key_targets("feedback_learning_jobs")
    assert ("source_job_id", "feedback_learning_jobs", "id") in get_foreign_key_targets(
        "review_rule_candidates"
    )


def test_economy_models_use_ledger_inventory_and_purchase_records() -> None:
    assert_columns_present("wallets", {"user_id", "created_at", "updated_at"})
    assert_columns_present(
        "wallet_ledger",
        {
            "id",
            "user_id",
            "asset_code",
            "delta",
            "balance_after",
            "reason_code",
            "source_type",
            "source_id",
            "idempotency_key",
            "created_at",
        },
    )
    assert_columns_present("inventories", {"id", "user_id", "item_code", "quantity", "updated_at"})
    assert_columns_present(
        "purchase_records",
        {
            "id",
            "user_id",
            "item_code",
            "price_asset_code",
            "price_amount",
            "status",
            "purchased_at",
            "idempotency_key",
        },
    )
    assert_columns_present(
        "leaderboard_snapshots",
        {"id", "user_id", "leaderboard_scope", "xp_total", "rank_position", "snapshot_date"},
    )
    assert_columns_present(
        "payment_transactions",
        {
            "id",
            "user_id",
            "provider_key",
            "external_transaction_id",
            "amount",
            "currency_code",
            "status",
            "created_at",
        },
    )
    assert_columns_present(
        "seasons",
        {"id", "season_code", "starts_at", "ends_at", "status", "created_at"},
    )
    assert_columns_present(
        "audit_logs",
        {
            "id",
            "actor_user_id",
            "entity_table",
            "entity_pk",
            "action_type",
            "payload",
            "occurred_at",
        },
    )

    assert ("user_id", "users", "id") in get_foreign_key_targets("wallets")
    assert ("user_id", "users", "id") in get_foreign_key_targets("wallet_ledger")
    assert ("user_id", "users", "id") in get_foreign_key_targets("inventories")
    assert ("user_id", "users", "id") in get_foreign_key_targets("purchase_records")
    assert ("user_id", "users", "id") in get_foreign_key_targets("payment_transactions")

    assert ("idempotency_key",) in get_unique_index_columns("wallet_ledger")
    assert ("idempotency_key",) in get_unique_index_columns("purchase_records")
