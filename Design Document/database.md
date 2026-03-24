很好，下面给你一套 **PostgreSQL DDL v1**，按批次可直接执行。  
我按“先主数据 → 再认证 → 再业务”排好了依赖顺序，复制到 `psql` 逐批执行即可。

**执行说明**
- 先执行 `Batch 0`，再按 `Batch 1 -> 6` 顺序执行。
- 每个批次都自带 `BEGIN/COMMIT`，单批失败可回滚，不影响前面批次。
- 兼容 PostgreSQL 13+（需要 `pgcrypto` 扩展用于 `gen_random_uuid()`）。

```sql
-- =========================
-- Batch 0: prerequisites
-- =========================
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

COMMIT;
```

```sql
-- =========================
-- Batch 1: dictionaries / master data
-- =========================
BEGIN;

CREATE TABLE IF NOT EXISTS game_modes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mode_code VARCHAR(40) NOT NULL UNIQUE,           -- endless / speed / draft
  display_name VARCHAR(100) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS asset_catalog (
  asset_code VARCHAR(40) PRIMARY KEY,              -- coins / xp
  display_name VARCHAR(80) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS item_catalog (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  item_code VARCHAR(80) NOT NULL UNIQUE,
  item_type VARCHAR(40) NOT NULL,                  -- consumable / revive / boost / ticket
  display_name VARCHAR(120) NOT NULL,
  rarity VARCHAR(20) NOT NULL,                     -- common/uncommon/rare/epic/legendary
  is_stackable BOOLEAN NOT NULL DEFAULT TRUE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (rarity IN ('common','uncommon','rare','epic','legendary'))
);

CREATE TABLE IF NOT EXISTS model_catalog (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_code VARCHAR(80) NOT NULL UNIQUE,          -- gemini-2.5-flash, gemini-3.1-pro
  display_name VARCHAR(120) NOT NULL,
  tier VARCHAR(20) NOT NULL DEFAULT 'standard',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (tier IN ('standard','pro','enterprise'))
);

CREATE TABLE IF NOT EXISTS subscription_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_code VARCHAR(60) NOT NULL UNIQUE,
  display_name VARCHAR(120) NOT NULL,
  billing_interval VARCHAR(20) NOT NULL,           -- monthly/yearly
  price_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
  currency_code CHAR(3) NOT NULL DEFAULT 'USD',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (billing_interval IN ('monthly','yearly')),
  CHECK (price_amount >= 0)
);

CREATE TABLE IF NOT EXISTS leagues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  league_code VARCHAR(50) NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS legal_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_type VARCHAR(40) NOT NULL,                   -- terms/privacy
  version VARCHAR(40) NOT NULL,
  title VARCHAR(200) NOT NULL,
  url TEXT NOT NULL,
  effective_at TIMESTAMPTZ NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (doc_type, version),
  CHECK (doc_type IN ('terms','privacy','community','help'))
);

INSERT INTO game_modes (mode_code, display_name) VALUES
('endless','Endless Abyss'),
('speed','Speed Survival'),
('draft','Knowledge Draft')
ON CONFLICT (mode_code) DO NOTHING;

INSERT INTO asset_catalog (asset_code, display_name) VALUES
('coins','Coins'),
('xp','Experience')
ON CONFLICT (asset_code) DO NOTHING;

COMMIT;
```

```sql
-- =========================
-- Batch 2: users + auth
-- =========================
BEGIN;

CREATE TABLE IF NOT EXISTS users (
  uid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(100) NOT NULL,
  username_normalized VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  email_normalized VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',    -- active/locked/deleted
  email_verified_at TIMESTAMPTZ,
  last_login_at TIMESTAMPTZ,
  failed_login_attempts INT NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ,
  CHECK (status IN ('active','locked','deleted')),
  CHECK (failed_login_attempts >= 0)
);

-- soft-delete 友好的唯一约束
CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username_norm_active
ON users (username_normalized) WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_norm_active
ON users (email_normalized) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_users_status ON users(status);
CREATE INDEX IF NOT EXISTS ix_users_last_login ON users(last_login_at DESC);

CREATE TABLE IF NOT EXISTS auth_password_credentials (
  user_id UUID PRIMARY KEY REFERENCES users(uid) ON DELETE CASCADE,
  password_hash VARCHAR(255) NOT NULL,
  hash_version VARCHAR(30) NOT NULL DEFAULT 'argon2id',
  password_changed_at TIMESTAMPTZ,
  must_rotate BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auth_identities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  provider_key VARCHAR(40) NOT NULL,               -- github/google/microsoft/email
  provider_user_key VARCHAR(255) NOT NULL,
  provider_email VARCHAR(255),
  linked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  unlinked_at TIMESTAMPTZ,
  UNIQUE (provider_key, provider_user_key),
  UNIQUE (user_id, provider_key),
  CHECK (provider_key IN ('github','google','microsoft','email'))
);

CREATE INDEX IF NOT EXISTS ix_auth_identities_user_id ON auth_identities(user_id);

CREATE TABLE IF NOT EXISTS auth_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  session_token_hash VARCHAR(255) NOT NULL UNIQUE,
  refresh_token_hash VARCHAR(255) UNIQUE,
  ip_address INET,
  user_agent_hash VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  last_seen_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_active
ON auth_sessions(user_id, revoked_at, expires_at);

CREATE TABLE IF NOT EXISTS auth_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  token_type VARCHAR(30) NOT NULL,                 -- email_verify/password_reset/account_delete
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (token_type IN ('email_verify','password_reset','account_delete','magic_link'))
);

CREATE INDEX IF NOT EXISTS ix_auth_tokens_user_type
ON auth_tokens(user_id, token_type, expires_at);

CREATE TABLE IF NOT EXISTS login_attempts (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(uid) ON DELETE SET NULL,
  identity_value VARCHAR(255),                     -- email or username
  ip_address INET NOT NULL,
  user_agent_hash VARCHAR(255),
  success_flag BOOLEAN NOT NULL,
  failure_reason VARCHAR(50),
  attempted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_login_attempts_identity_time
ON login_attempts(identity_value, attempted_at DESC);

CREATE INDEX IF NOT EXISTS ix_login_attempts_ip_time
ON login_attempts(ip_address, attempted_at DESC);

CREATE TABLE IF NOT EXISTS auth_security_events (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(uid) ON DELETE SET NULL,
  event_type VARCHAR(50) NOT NULL,                 -- login_success/login_fail/logout/password_changed...
  identity_value VARCHAR(255),
  ip_address INET,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_auth_security_events_user_time
ON auth_security_events(user_id, occurred_at DESC);

COMMIT;
```

```sql
-- =========================
-- Batch 3: profile/settings/subscription/legal/account actions
-- =========================
BEGIN;

CREATE TABLE IF NOT EXISTS user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(uid) ON DELETE CASCADE,
  display_name VARCHAR(120),
  avatar_url TEXT,
  bio TEXT,
  verified_badge BOOLEAN NOT NULL DEFAULT FALSE,
  tier_label VARCHAR(60),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_progression (
  user_id UUID PRIMARY KEY REFERENCES users(uid) ON DELETE CASCADE,
  level INT NOT NULL DEFAULT 1,
  xp_total BIGINT NOT NULL DEFAULT 0,
  current_streak INT NOT NULL DEFAULT 0,
  best_streak INT NOT NULL DEFAULT 0,
  last_activity_date DATE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (level >= 1),
  CHECK (xp_total >= 0),
  CHECK (current_streak >= 0),
  CHECK (best_streak >= 0)
);

CREATE TABLE IF NOT EXISTS user_settings (
  user_id UUID PRIMARY KEY REFERENCES users(uid) ON DELETE CASCADE,
  theme_key VARCHAR(20) NOT NULL DEFAULT 'system',
  language_code VARCHAR(20) NOT NULL DEFAULT 'en',
  sound_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  haptic_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  daily_reminder_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  leaderboard_scope_default VARCHAR(20) NOT NULL DEFAULT 'global',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (theme_key IN ('light','dark','system')),
  CHECK (leaderboard_scope_default IN ('global','friends'))
);

CREATE TABLE IF NOT EXISTS user_model_selection (
  user_id UUID PRIMARY KEY REFERENCES users(uid) ON DELETE CASCADE,
  model_id UUID NOT NULL REFERENCES model_catalog(id),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_user_model_selection_model ON user_model_selection(model_id);

CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES subscription_plans(id),
  status VARCHAR(20) NOT NULL,                     -- trialing/active/past_due/canceled/expired
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
  ended_at TIMESTAMPTZ,
  external_ref VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (external_ref),
  CHECK (status IN ('trialing','active','past_due','canceled','expired'))
);

CREATE INDEX IF NOT EXISTS ix_subscriptions_user_status ON subscriptions(user_id, status);

CREATE TABLE IF NOT EXISTS billing_invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
  invoice_no VARCHAR(80),
  amount NUMERIC(12,2) NOT NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'USD',
  period_start TIMESTAMPTZ,
  period_end TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL,                     -- open/paid/void/failed/refunded
  issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  paid_at TIMESTAMPTZ,
  CHECK (amount >= 0),
  CHECK (status IN ('open','paid','void','failed','refunded'))
);

CREATE INDEX IF NOT EXISTS ix_billing_invoices_sub_time
ON billing_invoices(subscription_id, issued_at DESC);

CREATE TABLE IF NOT EXISTS billing_events (
  id BIGSERIAL PRIMARY KEY,
  subscription_id UUID REFERENCES subscriptions(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL,
  event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_billing_events_sub_time
ON billing_events(subscription_id, event_time DESC);

CREATE TABLE IF NOT EXISTS user_legal_acceptances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  legal_document_id UUID NOT NULL REFERENCES legal_documents(id),
  accepted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ip_address INET,
  user_agent_hash VARCHAR(255),
  UNIQUE (user_id, legal_document_id)
);

CREATE INDEX IF NOT EXISTS ix_user_legal_acceptances_user_time
ON user_legal_acceptances(user_id, accepted_at DESC);

CREATE TABLE IF NOT EXISTS account_actions (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  action_type VARCHAR(30) NOT NULL,                -- clear_game_data/delete_account/logout
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  executed_at TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'requested', -- requested/executed/failed/cancelled
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (action_type IN ('clear_game_data','delete_account','logout')),
  CHECK (status IN ('requested','executed','failed','cancelled'))
);

CREATE INDEX IF NOT EXISTS ix_account_actions_user_time
ON account_actions(user_id, requested_at DESC);

CREATE TABLE IF NOT EXISTS account_deletion_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  scheduled_for TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',   -- pending/cancelled/completed
  reason_code VARCHAR(60),
  UNIQUE (user_id, status) DEFERRABLE INITIALLY IMMEDIATE
);

COMMIT;
```

```sql
-- =========================
-- Batch 4: library + game runs + settlements
-- =========================
BEGIN;

CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  subtitle TEXT,
  format VARCHAR(20) NOT NULL,                     -- pdf/txt/md/epub/docx
  size_label VARCHAR(40),                          -- UI text, eg "12 Pages"
  source_uri TEXT,
  checksum_sha256 CHAR(64),
  ingest_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ,
  CHECK (format IN ('pdf','txt','md','epub','docx')),
  CHECK (ingest_status IN ('pending','processing','ready','failed'))
);

CREATE INDEX IF NOT EXISTS ix_documents_owner_created
ON documents(owner_user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS document_ingestions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  ingest_version INT NOT NULL DEFAULT 1,
  status VARCHAR(20) NOT NULL,                     -- processing/success/failed
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  page_count INT,
  word_count INT,
  error_code VARCHAR(80),
  error_message TEXT,
  UNIQUE (document_id, ingest_version),
  CHECK (status IN ('processing','success','failed'))
);

CREATE INDEX IF NOT EXISTS ix_document_ingestions_doc_time
ON document_ingestions(document_id, started_at DESC);

CREATE TABLE IF NOT EXISTS user_document_progress (
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  progress_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
  progress_label VARCHAR(80),
  action_hint VARCHAR(20) NOT NULL DEFAULT 'begin', -- begin/continue/review
  last_opened_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  mastered BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, document_id),
  CHECK (progress_pct >= 0 AND progress_pct <= 100),
  CHECK (action_hint IN ('begin','continue','review'))
);

CREATE INDEX IF NOT EXISTS ix_user_document_progress_user_recent
ON user_document_progress(user_id, last_opened_at DESC);

CREATE TABLE IF NOT EXISTS game_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
  game_mode_id UUID NOT NULL REFERENCES game_modes(id),
  flow VARCHAR(20) NOT NULL DEFAULT 'begin',       -- begin/review
  status VARCHAR(20) NOT NULL DEFAULT 'running',   -- running/completed/aborted
  score BIGINT NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (flow IN ('begin','review')),
  CHECK (status IN ('running','completed','aborted')),
  CHECK (score >= 0)
);

CREATE INDEX IF NOT EXISTS ix_game_runs_user_mode_start
ON game_runs(user_id, game_mode_id, started_at DESC);

CREATE TABLE IF NOT EXISTS run_endless_details (
  run_id UUID PRIMARY KEY REFERENCES game_runs(id) ON DELETE CASCADE,
  hp_current INT NOT NULL DEFAULT 100,
  hp_max INT NOT NULL DEFAULT 100,
  floor_current INT NOT NULL DEFAULT 1,
  floor_total INT,
  coins_gained_in_run BIGINT NOT NULL DEFAULT 0,
  best_combo INT NOT NULL DEFAULT 0,
  CHECK (hp_current >= 0),
  CHECK (hp_max >= 1),
  CHECK (floor_current >= 1),
  CHECK (coins_gained_in_run >= 0),
  CHECK (best_combo >= 0)
);

CREATE TABLE IF NOT EXISTS run_speed_details (
  run_id UUID PRIMARY KEY REFERENCES game_runs(id) ON DELETE CASCADE,
  time_remaining_sec INT,
  survival_seconds INT,
  combo_count INT NOT NULL DEFAULT 0,
  questions_answered INT NOT NULL DEFAULT 0,
  correct_answers INT NOT NULL DEFAULT 0,
  CHECK (combo_count >= 0),
  CHECK (questions_answered >= 0),
  CHECK (correct_answers >= 0)
);

CREATE TABLE IF NOT EXISTS run_draft_details (
  run_id UUID PRIMARY KEY REFERENCES game_runs(id) ON DELETE CASCADE,
  progress_current INT NOT NULL DEFAULT 0,
  progress_total INT NOT NULL DEFAULT 0,
  slots_filled INT NOT NULL DEFAULT 0,
  CHECK (progress_current >= 0),
  CHECK (progress_total >= 0),
  CHECK (slots_filled >= 0)
);

CREATE TABLE IF NOT EXISTS run_answers (
  id BIGSERIAL PRIMARY KEY,
  run_id UUID NOT NULL REFERENCES game_runs(id) ON DELETE CASCADE,
  question_ref VARCHAR(120),
  answer_value TEXT,
  is_correct BOOLEAN,
  answer_time_ms INT,
  answered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_run_answers_run_time
ON run_answers(run_id, answered_at DESC);

CREATE TABLE IF NOT EXISTS run_settlements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL UNIQUE REFERENCES game_runs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  mode_name VARCHAR(100) NOT NULL,
  xp_gained BIGINT NOT NULL DEFAULT 0,
  coin_reward BIGINT NOT NULL DEFAULT 0,
  perfect_combo INT NOT NULL DEFAULT 0,
  goal_text TEXT,
  goal_progress_pct NUMERIC(5,2),
  league_percentile NUMERIC(6,2),
  settled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (xp_gained >= 0),
  CHECK (coin_reward >= 0),
  CHECK (perfect_combo >= 0)
);

CREATE INDEX IF NOT EXISTS ix_run_settlements_user_time
ON run_settlements(user_id, settled_at DESC);

CREATE TABLE IF NOT EXISTS run_settlement_grants (
  id BIGSERIAL PRIMARY KEY,
  settlement_id UUID NOT NULL REFERENCES run_settlements(id) ON DELETE CASCADE,
  grant_type VARCHAR(20) NOT NULL,                 -- asset/item
  asset_code VARCHAR(40) REFERENCES asset_catalog(asset_code),
  item_id UUID REFERENCES item_catalog(id),
  quantity BIGINT NOT NULL,
  CHECK (grant_type IN ('asset','item')),
  CHECK (quantity > 0),
  CHECK (
    (grant_type='asset' AND asset_code IS NOT NULL AND item_id IS NULL) OR
    (grant_type='item'  AND item_id IS NOT NULL AND asset_code IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS ix_run_settlement_grants_settlement
ON run_settlement_grants(settlement_id);

COMMIT;
```

```sql
-- =========================
-- Batch 5: economy + shop + inventory + quests
-- =========================
BEGIN;

CREATE TABLE IF NOT EXISTS user_balances (
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  asset_code VARCHAR(40) NOT NULL REFERENCES asset_catalog(asset_code),
  balance BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, asset_code),
  CHECK (balance >= 0)
);

CREATE TABLE IF NOT EXISTS economy_ledger_entries (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  asset_code VARCHAR(40) NOT NULL REFERENCES asset_catalog(asset_code),
  delta BIGINT NOT NULL,                           -- +/- amount
  balance_after BIGINT NOT NULL,
  reason_code VARCHAR(60) NOT NULL,                -- run_reward/shop_purchase/quest_claim/adjustment
  source_type VARCHAR(40),                         -- run_settlement/shop_purchase/quest_assignment/...
  source_id UUID,
  idempotency_key VARCHAR(120),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (delta <> 0),
  CHECK (balance_after >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_economy_ledger_idempotency
ON economy_ledger_entries(idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_economy_ledger_user_asset_time
ON economy_ledger_entries(user_id, asset_code, created_at DESC);

CREATE TABLE IF NOT EXISTS shop_offers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offer_code VARCHAR(80) NOT NULL UNIQUE,
  item_id UUID REFERENCES item_catalog(id),
  display_name VARCHAR(120) NOT NULL,
  rarity VARCHAR(20) NOT NULL,
  price_asset_code VARCHAR(40) NOT NULL REFERENCES asset_catalog(asset_code),
  price_amount BIGINT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  active_from TIMESTAMPTZ,
  active_to TIMESTAMPTZ,
  purchase_limit_per_user INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (rarity IN ('common','uncommon','rare','epic','legendary')),
  CHECK (price_amount >= 0)
);

CREATE INDEX IF NOT EXISTS ix_shop_offers_active_time
ON shop_offers(is_active, active_from, active_to);

CREATE TABLE IF NOT EXISTS shop_offer_grants (
  id BIGSERIAL PRIMARY KEY,
  offer_id UUID NOT NULL REFERENCES shop_offers(id) ON DELETE CASCADE,
  grant_type VARCHAR(20) NOT NULL,                 -- asset/item
  asset_code VARCHAR(40) REFERENCES asset_catalog(asset_code),
  item_id UUID REFERENCES item_catalog(id),
  quantity BIGINT NOT NULL,
  CHECK (grant_type IN ('asset','item')),
  CHECK (quantity > 0),
  CHECK (
    (grant_type='asset' AND asset_code IS NOT NULL AND item_id IS NULL) OR
    (grant_type='item'  AND item_id IS NOT NULL AND asset_code IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS ix_shop_offer_grants_offer
ON shop_offer_grants(offer_id);

CREATE TABLE IF NOT EXISTS shop_purchases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  offer_id UUID NOT NULL REFERENCES shop_offers(id),
  price_asset_code VARCHAR(40) NOT NULL REFERENCES asset_catalog(asset_code),
  price_amount BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'completed', -- pending/completed/failed/refunded
  purchased_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  idempotency_key VARCHAR(120),
  CHECK (status IN ('pending','completed','failed','refunded')),
  CHECK (price_amount >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_shop_purchases_idempotency
ON shop_purchases(idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_shop_purchases_user_time
ON shop_purchases(user_id, purchased_at DESC);

CREATE TABLE IF NOT EXISTS inventory_balances (
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  item_id UUID NOT NULL REFERENCES item_catalog(id),
  quantity BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, item_id),
  CHECK (quantity >= 0)
);

CREATE TABLE IF NOT EXISTS inventory_ledger_entries (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  item_id UUID NOT NULL REFERENCES item_catalog(id),
  delta BIGINT NOT NULL,
  balance_after BIGINT NOT NULL,
  reason_code VARCHAR(60) NOT NULL,                -- purchase/reward/consume/adjustment
  source_type VARCHAR(40),
  source_id UUID,
  idempotency_key VARCHAR(120),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (delta <> 0),
  CHECK (balance_after >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory_ledger_idempotency
ON inventory_ledger_entries(idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_inventory_ledger_user_item_time
ON inventory_ledger_entries(user_id, item_id, created_at DESC);

CREATE TABLE IF NOT EXISTS quest_definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  quest_code VARCHAR(80) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  quest_type VARCHAR(20) NOT NULL,                 -- daily/monthly/special
  target_metric VARCHAR(60) NOT NULL,              -- run_count/accuracy/document_upload...
  target_value BIGINT NOT NULL,
  cadence VARCHAR(20) NOT NULL DEFAULT 'daily',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  active_from TIMESTAMPTZ,
  active_to TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (quest_type IN ('daily','monthly','special')),
  CHECK (cadence IN ('daily','weekly','monthly','once')),
  CHECK (target_value > 0)
);

CREATE INDEX IF NOT EXISTS ix_quest_definitions_active
ON quest_definitions(is_active, active_from, active_to);

CREATE TABLE IF NOT EXISTS quest_rewards (
  id BIGSERIAL PRIMARY KEY,
  quest_definition_id UUID NOT NULL REFERENCES quest_definitions(id) ON DELETE CASCADE,
  reward_type VARCHAR(20) NOT NULL,                -- asset/item/badge
  asset_code VARCHAR(40) REFERENCES asset_catalog(asset_code),
  item_id UUID REFERENCES item_catalog(id),
  badge_code VARCHAR(80),
  quantity BIGINT NOT NULL DEFAULT 1,
  CHECK (reward_type IN ('asset','item','badge')),
  CHECK (quantity > 0)
);

CREATE INDEX IF NOT EXISTS ix_quest_rewards_def
ON quest_rewards(quest_definition_id);

CREATE TABLE IF NOT EXISTS user_quest_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  quest_definition_id UUID NOT NULL REFERENCES quest_definitions(id),
  cycle_key VARCHAR(40) NOT NULL,                  -- e.g. 2026-03-14 / 2026-03
  progress_value BIGINT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'in_progress', -- in_progress/completed/claimed/expired
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  claimed_at TIMESTAMPTZ,
  UNIQUE (user_id, quest_definition_id, cycle_key),
  CHECK (status IN ('in_progress','completed','claimed','expired')),
  CHECK (progress_value >= 0)
);

CREATE INDEX IF NOT EXISTS ix_user_quest_assignments_user_status
ON user_quest_assignments(user_id, status, expires_at);

COMMIT;
```

```sql
-- =========================
-- Batch 6: leaderboard + audit
-- =========================
BEGIN;

CREATE TABLE IF NOT EXISTS leaderboard_definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  leaderboard_code VARCHAR(80) NOT NULL UNIQUE,
  display_name VARCHAR(120) NOT NULL,
  game_mode_id UUID REFERENCES game_modes(id),
  scope VARCHAR(20) NOT NULL DEFAULT 'global',     -- global/friends
  ranking_method VARCHAR(30) NOT NULL DEFAULT 'score_desc',
  snapshot_cadence VARCHAR(20) NOT NULL DEFAULT 'weekly',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  CHECK (scope IN ('global','friends')),
  CHECK (snapshot_cadence IN ('hourly','daily','weekly','monthly'))
);

CREATE TABLE IF NOT EXISTS leaderboard_seasons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  leaderboard_definition_id UUID NOT NULL REFERENCES leaderboard_definitions(id) ON DELETE CASCADE,
  season_no INT NOT NULL,
  starts_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',    -- active/closed/archived
  UNIQUE (leaderboard_definition_id, season_no),
  CHECK (status IN ('active','closed','archived')),
  CHECK (ends_at > starts_at)
);

CREATE INDEX IF NOT EXISTS ix_leaderboard_seasons_def_time
ON leaderboard_seasons(leaderboard_definition_id, starts_at, ends_at);

CREATE TABLE IF NOT EXISTS user_league_memberships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  league_id UUID NOT NULL REFERENCES leagues(id),
  season_id UUID REFERENCES leaderboard_seasons(id) ON DELETE SET NULL,
  starts_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ends_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_user_league_memberships_user_time
ON user_league_memberships(user_id, ends_at);

CREATE TABLE IF NOT EXISTS leaderboard_entries_current (
  season_id UUID NOT NULL REFERENCES leaderboard_seasons(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  league_id UUID REFERENCES leagues(id),
  score BIGINT NOT NULL DEFAULT 0,
  tie_break_value BIGINT,
  source_run_id UUID REFERENCES game_runs(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (season_id, user_id),
  CHECK (score >= 0)
);

CREATE INDEX IF NOT EXISTS ix_leaderboard_entries_current_rank
ON leaderboard_entries_current(season_id, league_id, score DESC, tie_break_value ASC);

CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  season_id UUID NOT NULL REFERENCES leaderboard_seasons(id) ON DELETE CASCADE,
  snapshot_type VARCHAR(20) NOT NULL DEFAULT 'periodic', -- periodic/final
  snapshot_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_final BOOLEAN NOT NULL DEFAULT FALSE,
  CHECK (snapshot_type IN ('periodic','final'))
);

CREATE INDEX IF NOT EXISTS ix_leaderboard_snapshots_season_time
ON leaderboard_snapshots(season_id, snapshot_at DESC);

CREATE TABLE IF NOT EXISTS leaderboard_snapshot_entries (
  snapshot_id UUID NOT NULL REFERENCES leaderboard_snapshots(id) ON DELETE CASCADE,
  rank INT NOT NULL,
  user_id UUID NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
  league_id UUID REFERENCES leagues(id),
  score BIGINT NOT NULL,
  tie_break_value BIGINT,
  PRIMARY KEY (snapshot_id, rank),
  UNIQUE (snapshot_id, user_id),
  CHECK (rank >= 1),
  CHECK (score >= 0)
);

CREATE INDEX IF NOT EXISTS ix_leaderboard_snapshot_entries_user
ON leaderboard_snapshot_entries(user_id);

CREATE TABLE IF NOT EXISTS audit_events (
  id BIGSERIAL PRIMARY KEY,
  actor_user_id UUID REFERENCES users(uid) ON DELETE SET NULL,
  entity_table VARCHAR(80) NOT NULL,
  entity_pk VARCHAR(120) NOT NULL,
  action_type VARCHAR(30) NOT NULL,                -- insert/update/delete/soft_delete/link/unlink/claim...
  request_id VARCHAR(120),
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_audit_events_entity_time
ON audit_events(entity_table, entity_pk, occurred_at DESC);

CREATE INDEX IF NOT EXISTS ix_audit_events_actor_time
ON audit_events(actor_user_id, occurred_at DESC);

COMMIT;
```

**建议你执行后的快速验收**
- `\dt` 看表数量是否完整。
- 随机插入 1 个用户、1 个文档、1 条 run、1 条 settlement、1 条 ledger，验证 FK 连通。
- 如果你愿意，我下一条可以给你一份 **seed.sql（最小演示数据）**，插入后前后端联调会更快。