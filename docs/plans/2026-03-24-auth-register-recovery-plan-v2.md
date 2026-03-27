# 实施计划：注册链路恢复与安全防回归加固（V2）

> **For agentic workers:** 本计划按 `/execute` 分阶段执行；先完成 P0 安全收口，再做回归防线。

## Goal
在不破坏现有登录注册可用性的前提下，完成认证边界收敛与防回归加固，确保：
- `/sign-up`、`/login` 持续可用；
- 受保护接口身份来源可信（JWT claims 为单一真相源）；
- `register -> login -> refresh -> logout -> me` 全链路有“无 override”真实集成测试护栏；
- 前端网络错误与业务错误可区分，可快速定位代理/后端问题。

## Baseline（基线）
经审查，V1 计划中的部分工作已完成：
- ✅ 前端开发代理已配置：`frontend/vite.config.ts`
- ✅ 后端 auth DI 已接线：`backend/app/api/v1/auth.py#get_auth_service`
- ✅ `AuthRepository` 核心方法已实现：`backend/app/repositories/auth_repository.py`
- ✅ auth 结构化日志字段已落地（`endpoint/status_code/latency_ms/request_id/failure_reason`）

仍存在关键缺口：
- ❗ `get_current_user_id` 仍依赖并信任 `X-User-Id`，不是仅以 JWT claims 为身份来源（P0）
- ❗ 缺少无 `dependency_overrides` 的 auth 全链路集成测试（P1）
- ❗ 缺少 `frontend/src/api/http.ts` 错误分类测试（P1）

## Scope
### In Scope
- 认证身份来源统一（JWT claims）
- refresh/logout 语义闭合与会话撤销校验
- 后端真实 wiring 集成测试（无 override）
- 前端 http 错误分类与测试
- readiness/smoke 与文档更新

### Out of Scope
- OAuth 社交登录实现
- 全站权限模型重构（RBAC/ABAC）
- 跨服务 SSO

---

## Task List

### Phase P0：认证边界收口（最高优先级）

**目标：** 修复身份伪造风险，保证服务端只信任 JWT token 中的用户身份。

**Files (expected):**
- Modify: `backend/app/api/dependencies/auth.py`
- Modify: `backend/app/api/v1/runs.py`
- Modify: `backend/app/api/v1/shop.py`
- Modify: `backend/app/api/v1/settings.py`
- Modify: `backend/app/api/v1/profile.py`
- Modify: `backend/app/api/v1/review.py`
- Modify: `backend/app/api/v1/feedback.py`
- Modify: `frontend/src/api/authHeaders.ts`（兼容期可保留，但不再要求 `X-User-Id`）

- [ ] **Step 1: Write failing tests (RED)**
  - 后端：新增/更新依赖测试，断言“无 `X-User-Id` 但携带有效 Bearer token”可通过；“伪造 `X-User-Id` 不影响服务端识别”。
  - 后端：补 `logout -> refresh` 必须失败（401）的失败用例。

- [ ] **Step 2: Implement minimal fix (GREEN)**
  - 在 `get_current_user_id` 中从 Bearer token 解 user_id（验签+校验 token type/access）。
  - 逐步移除对请求头 `X-User-Id` 的强依赖；如需兼容，最多作为观测字段，不作为授权依据。
  - 在 `AuthService.refresh` 中增加 `revoked_at/expires_at` 校验，阻断被撤销会话续期。

- [ ] **Step 3: Run targeted tests**
  - `uv run pytest backend/tests/services/test_auth_service.py -q`
  - `uv run pytest backend/tests/api/test_auth_wiring.py -q`

- [ ] **Step 4: Commit**
  - `feat(auth): trust jwt claims over X-User-Id and close refresh-after-logout gap`

---

### Phase P1：真实 wiring 回归防线

**目标：** 防止“测试全绿但运行态炸掉”的问题再次出现。

**Files (expected):**
- Create: `backend/tests/api/test_auth_wiring_integration.py`
- Modify: `backend/tests/api/test_auth_api.py`（保留 fake contract 测试，但标注定位）

- [ ] **Step 1: Write integration tests (RED)**
  - 使用真实 app + test DB，不设置 `app.dependency_overrides[get_auth_service]`。
  - 覆盖流程：`register -> login -> refresh -> logout -> me`
  - 必测断言：
    - 注册成功返回 201；重复注册返回 409（非 500）
    - 登录成功返回 token
    - refresh 成功轮换 token
    - logout 后 refresh 返回 401
    - me 仅在有效 access token 下可访问

- [ ] **Step 2: Fix wiring/transaction issues (GREEN)**
  - 若出现并发唯一约束导致 500：在 service/repository 层补异常映射到 409。
  - 关键路径异常时执行 rollback。

- [ ] **Step 3: Run tests**
  - `uv run pytest backend/tests/api/test_auth_wiring_integration.py -q --tb=short`
  - `uv run pytest backend/tests/api/test_auth_api.py -q --tb=short`

- [ ] **Step 4: Commit**
  - `test(auth): add no-override wiring integration regression suite`

---

### Phase P1.5：前端错误分类与诊断能力

**目标：** 快速区分“代理/网络故障”与“业务 4xx/5xx”。

**Files (expected):**
- Modify: `frontend/src/api/http.ts`
- Create: `frontend/src/api/http.spec.ts`
- Modify: `frontend/src/api/auth.ts`（必要时优化错误映射）

- [ ] **Step 1: Write failing tests (RED)**
  - URL 解析：`VITE_API_BASE_URL` 为空/非空两条路径
  - 网络错误：fetch reject 时错误类型与文案
  - 超时错误：408 映射
  - 业务错误：4xx/5xx `ApiError` 结构一致

- [ ] **Step 2: Implement minimal fix (GREEN)**
  - 统一 `apiRequest` 对网络异常/超时/业务异常的分类输出。
  - 保持调用方（登录页）可直接给出用户可读提示。

- [ ] **Step 3: Run tests**
  - `npm run test -- src/api/http.spec.ts`
  - `npm run test -- src/pages/DungeonScholarLoginPage.spec.ts`

- [ ] **Step 4: Commit**
  - `feat(frontend): classify api network and business errors for auth flows`

---

### Phase P2：运维与文档收口

**目标：** 增强上线前可观测性，消除文档与事实偏差。

**Files (expected):**
- Modify: `README.md`（代理与环境变量说明统一）
- Modify: `docs/plans/2026-03-24-auth-register-recovery-plan.md`（标注已完成项/迁移到 V2）
- Optional: 新增启动 smoke 脚本（如 `backend/scripts/smoke_auth.sh` 或等价）

- [ ] **Step 1: Add readiness/smoke checks**
  - 至少覆盖：后端可启动、DB 可连接、auth 关键端点可访问。

- [ ] **Step 2: Doc alignment**
  - 统一 `localhost:8000` 与 `127.0.0.1:8000` 文档表述（二者等价但需一致）。
  - 明确 `VITE_API_BASE_URL` 与 `VITE_API_PROXY_TARGET` 优先级。

- [ ] **Step 3: Commit**
  - `docs(auth): align recovery plan with implemented state and v2 priorities`

---

## Verification Checklist（必须通过）

### Backend
- [ ] `uv run ruff check app tests`
- [ ] `uv run mypy app`
- [ ] `uv run pytest tests/api/test_auth_api.py tests/api/test_auth_wiring.py tests/api/test_auth_wiring_integration.py -q --tb=short`

### Frontend
- [ ] `npm run lint`
- [ ] `npm run typecheck`
- [ ] `npm run test -- src/api/http.spec.ts src/pages/DungeonScholarLoginPage.spec.ts`
- [ ] `npm run build`

## Success Criteria（验收标准）
- [ ] `/sign-up`、`/login` 在开发环境与本地联调环境稳定可用
- [ ] 服务端不再以 `X-User-Id` 作为授权依据
- [ ] `logout` 后 `refresh` 返回 401
- [ ] 重复注册在并发场景返回 409（非 500）
- [ ] 存在无 override 的 auth 全链路集成测试并纳入必跑
- [ ] 前端能区分网络/代理错误与业务错误

## Risks & Mitigations
- **风险：** 切换身份来源影响现有接口兼容
  - **缓解：** 先后端兼容读取，先验 JWT claims，逐步移除 `X-User-Id` 依赖
- **风险：** 事务处理不一致导致偶发 500
  - **缓解：** service 层统一 rollback；唯一约束异常统一映射 409
- **风险：** 开发环境误配导致“偶发 5173”问题
  - **缓解：** 文档与启动日志提示当前 API 目标地址

## Execute Order
1. `/execute phase-p0`：认证边界收口（JWT claims 单一身份源 + refresh 语义）
2. `/execute phase-p1`：无 override wiring 集成测试
3. `/execute phase-p1-frontend`：前端 http 错误分类 + 测试
4. `/execute phase-p2`：readiness/smoke + 文档收口
