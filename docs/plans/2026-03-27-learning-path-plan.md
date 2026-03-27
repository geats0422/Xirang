# 实施计划：文档驱动学习路径（对齐版，基于 Design Document/方案.md）

> **For agentic workers:** 本计划替代 auth-register-recovery 两份计划作为当前主执行路线；按 `/execute` 单任务推进。

## Goal
以 `Design Document/方案.md` 为唯一基准，落地“文档+模式可版本化学习路径”体系：懒生成、版本并存、进度隔离、路径重生限流、奖励风控（传奇递减/旧版70%/免费封顶/订阅不封顶）、多格式统一 Markdown 解析。

## 对齐结论（与两份 auth 计划差异）
- `2026-03-24-auth-register-recovery-plan*.md` 聚焦认证修复与回归防线，**不覆盖**路径版本化能力。
- 当前缺口与 `方案.md` 的主差异在于：
  1. 缺失学习路径域数据模型（versions/nodes/progress/regeneration/subscription/cap）。
  2. `runs/path-options` 仍是硬编码，不识别 document_id，也无 200/202/409 语义。
  3. `create_run` 未绑定 `path_version_id/path_node_id`。
  4. 结算未接入传奇递减、旧版70%、免费封顶、订阅判定。
  5. 前端 Level Path 未实现生成中/超时/重试/版本切换。
  6. 未接入 MinerU 统一标准化 Markdown 管线。

## Task List

### Task 1: 学习路径数据模型与迁移（后端）
**Files:**
- Create: `backend/app/db/models/learning_paths.py`
- Create: `backend/app/db/models/subscriptions.py`
- Modify: `backend/app/db/models/economy.py`
- Modify: `backend/app/db/models/runs.py`
- Modify: `backend/app/db/models/__init__.py`
- Create: `backend/alembic/versions/*_learning_paths_and_subscriptions.py`

- [x] RED: 新增模型存在性与字段级测试（schema smoke）
- [x] GREEN: 创建模型与迁移
- [x] VERIFY: `uv run alembic upgrade head` + `uv run pytest tests/test_project_layout.py -q`
- [ ] COMMIT: `feat(paths): add versioned learning path and subscription schema`

### Task 2: 路径域仓储/服务 + path-options / regeneration API（后端）
**Files:**
- Create: `backend/app/repositories/learning_path_repository.py`
- Create: `backend/app/services/learning_paths/service.py`
- Create: `backend/app/services/learning_paths/generator.py`
- Modify: `backend/app/api/v1/runs.py`
- Modify: `backend/tests/api/test_runs_api.py`
- Create: `backend/tests/api/test_learning_path_api.py`

- [x] RED: 写 200/202/409、24h 3次限流失败用例
- [x] GREEN: 实现 `GET /runs/path-options`（支持 document_id+mode）与 `POST /runs/path-regenerations`
- [x] VERIFY: `uv run pytest tests/api/test_learning_path_api.py tests/api/test_runs_api.py -q --tb=short`
- [ ] COMMIT: `feat(paths): add lazy generation and regeneration endpoints`

### Task 3: run 绑定路径节点 + 进度写入（后端）
**Files:**
- Modify: `backend/app/services/runs/service.py`
- Modify: `backend/app/repositories/run_repository.py`
- Modify: `backend/app/api/v1/runs.py`
- Update tests: `backend/tests/api/test_runs_api.py`, `backend/tests/services/test_runs_service.py`(if exists/create)

- [x] RED: create_run 接收 path_version_id/path_node_id 用例
- [x] GREEN: run 绑定 `source_path_version_id/source_level_node_id`，提交后更新 progress
- [x] VERIFY: 定向 pytest
- [ ] COMMIT: `feat(runs): bind runs to path version and level node`

### Task 4: 奖励风控策略（后端）
**Files:**
- Create: `backend/app/services/learning_paths/reward_policy.py`
- Modify: `backend/app/services/runs/service.py`
- Modify: `backend/app/repositories/*`（cap/subscription 读取）
- Create tests: `backend/tests/services/test_reward_policy.py`

- [x] RED: 传奇倍率、旧版70%、免费封顶、订阅不封顶用例
- [x] GREEN: 统一 RewardPolicy 结算
- [x] VERIFY: pytest + 账本幂等检查
- [ ] COMMIT: `feat(reward): enforce legend decay, version discount and daily cap`

### Task 5: 前端 Level Path 状态化与 run 参数升级
**Files:**
- Modify: `frontend/src/api/runs.ts`
- Modify: `frontend/src/pages/DungeonScholarLevelPathPage.vue`
- Modify: 三模式页面（endless/speed/draft）
- Update tests: `frontend/src/pages/DungeonScholarLevelPathPage.spec.ts`

- [x] RED: generating/failed/timeout/retry/regen UI 测试
- [x] GREEN: 实现轮询与重试、版本上下文透传 createRun
- [x] VERIFY: `npm run lint && npm run typecheck && npm run test -- src/pages/DungeonScholarLevelPathPage.spec.ts`
- [ ] COMMIT: `feat(frontend): add path generation states and regeneration flow`

### Task 6: MinerU 统一解析管线 + 清理任务
**Files:**
- Create: `backend/app/integrations/mineru/client.py`
- Create: `backend/app/services/documents/normalizer.py`
- Modify: `backend/app/workers/main.py`
- Create/Modify cleanup job scripts/tests

- [ ] RED: 多格式输入统一到标准化 Markdown 的测试
- [ ] GREEN: 接入 MinerU + failed 7天清理
- [ ] VERIFY: worker tests + ingestion integration
- [ ] COMMIT: `feat(ingestion): unify markdown normalization and failed cleanup`

## Dependencies
- Task1 → Task2 → Task3 → Task4 → Task5
- Task6 可在 Task2 后并行，但发布前必须与 Task5 一起验收。

## 验收命令
- Backend: `uv run ruff check app tests && uv run mypy app && uv run pytest tests -q --tb=short`
- Frontend: `npm run lint && npm run typecheck && npm run test && npm run build`
