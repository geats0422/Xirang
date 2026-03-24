# 实施计划：注册链路恢复与防回归加固

## 概述
当前注册失败由两个问题叠加导致：前端开发链路请求错误落到 `localhost:5173`（404），以及后端 auth 依赖未接线（500）。
本计划采用分阶段方案：先恢复前后端联通，再修复后端真实 auth wiring，最后补齐回归测试与可观测性，确保问题不再复发。

## 需求
- 修复 `/sign-up` 注册链路，确保可创建账号
- 修复 `/login` 登录链路，确保新账号可登录并持久化会话
- 用测试账号执行完整回归：`test1` / `briannr.an.g.el.286@gmail.com`
- 输出防回归方案：补测试、启动检查、日志告警
- 实施阶段按用户要求使用 `/execute`

## 架构更改
- `frontend/vite.config.ts`：增加开发代理，转发 `/api` 到后端
- `backend/app/api/v1/auth.py`：实现 `get_auth_service` 的真实依赖注入
- `backend/app/repositories/auth_repository.py`：实现 `AuthService` 所需仓储方法
- `backend/tests/api/`：新增无 `dependency_overrides` 的真实 wiring 集成测试
- `frontend/src/api/http.ts` 与相关测试：细化网络错误与业务错误区分

## 实施步骤

### 阶段 1：链路止血（清除 404）
1. **恢复前端 API 代理** (文件: `frontend/vite.config.ts`)
   - 操作：为 `/api`（可选 `/health`）配置 `server.proxy`，目标读取 `VITE_API_PROXY_TARGET`，默认 `http://localhost:8000`
   - 原因：当前相对路径请求被发往 `5173`，导致 `POST /api/v1/auth/register` 404
   - 依赖：无
   - 风险：低

2. **补开发配置说明** (文件: `frontend/.env.example`、相关 README)
   - 操作：明确 `VITE_API_BASE_URL` 与 `VITE_API_PROXY_TARGET` 的优先级与用途
   - 原因：避免多人开发环境误配
   - 依赖：步骤 1
   - 风险：低

### 阶段 2：后端 auth 真实接线（清除 500）
3. **实现 auth service 工厂依赖** (文件: `backend/app/api/v1/auth.py`)
   - 操作：将 `get_auth_service` 改为 `Depends(get_db_session)` 构建 `AuthService`
   - 原因：当前 `NotImplementedError("AuthService dependency must be overridden")` 直接导致 500
   - 依赖：无
   - 风险：中

4. **实现 AuthRepository 核心能力** (文件: `backend/app/repositories/auth_repository.py`)
   - 操作：按 `AuthRepositoryProtocol` 实现注册/登录必需方法：查用户、建用户、建凭证、建 profile/settings/wallet、会话管理、提交回滚
   - 原因：`AuthService` 运行依赖仓储实现，当前文件为空
   - 依赖：步骤 3（可并行）
   - 风险：中

5. **补事务与异常兜底** (文件: `backend/app/services/auth/service.py`)
   - 操作：关键流程异常路径确保 rollback；必要时将唯一约束冲突映射为 409
   - 原因：减少并发或脏数据情况下 500 泄漏
   - 依赖：步骤 4
   - 风险：中

### 阶段 3：修复后验证（指定测试账号）
6. **执行手工回归：注册 + 登录** (文件: N/A)
   - 操作：在 `/sign-up` 使用 `test1 / briannr.an.g.el.286@gmail.com` 注册，再到 `/login` 登录验证
   - 原因：验证真实用户路径闭环
   - 依赖：阶段 1、2
   - 风险：低

7. **执行命令级回归** (文件: N/A)
   - 操作：
     - 前端：`npm run lint && npm run typecheck && npm run test && npm run build`
     - 后端：`uv run pytest`（至少 auth 相关与新增 wiring 集成测试）
   - 原因：确认无回归
   - 依赖：步骤 6
   - 风险：低

### 阶段 4：防回归加固
8. **新增无 override 的 auth 集成测试** (文件: `backend/tests/api/test_auth_wiring_integration.py` 建议新建)
   - 操作：真实 app + test db，覆盖 `register -> login -> refresh -> logout -> me`
   - 原因：防止"测试全绿、运行 500"再次发生
   - 依赖：阶段 2
   - 风险：中

9. **前端错误分类测试** (文件: `frontend/src/api/http.ts` 与相应 spec)
   - 操作：区分网络/代理失败与 4xx 业务错误文案
   - 原因：排障速度更快，用户提示更准确
   - 依赖：阶段 1
   - 风险：低

10. **启动检查与日志告警** (文件: backend 启动与日志配置)
   - 操作：补启动后关键端点检查，增加 auth 结构化日志字段 `endpoint`、`status_code`、`latency_ms`、`failure_reason`、`request_id`
   - 原因：尽早识别代理错误、依赖缺失、凭证错误、数据库冲突
   - 依赖：阶段 2
   - 风险：低

## 测试策略
- 单元测试：
  - 前端 `http.ts` 的 URL 解析与错误归类
  - 后端 `AuthRepository` 方法与异常映射
- 集成测试：
  - 后端真实 wiring：`register/login/refresh/logout/me`
- E2E 测试：
  - `/sign-up` 注册（`test1 / briannr.an.g.el.286@gmail.com`）-> `/login` 登录 -> 受保护页面访问

## 风险与缓解
- **风险**：代理修复后暴露后端 500
  - 缓解：优先执行阶段 2，先打通 auth service DI 与 repository
- **风险**：并发注册触发唯一约束报错
  - 缓解：捕获并映射为 409，避免 500
- **风险**：登录后访问受保护路由仍 401（`X-User-Id` 依赖）
  - 缓解：列为后续任务，逐步收敛到 JWT 解 user 的单一路径
- **风险**：测试继续依赖 fake override 掩盖运行时问题
  - 缓解：将"无 override 的 wiring 集成测试"纳入必跑

## 成功标准
- [ ] `/sign-up` 注册不再出现 404/500
- [ ] 测试账号 `test1 / briannr.an.g.el.286@gmail.com` 完成注册并可登录
- [ ] 前端 `lint/typecheck/test/build` 全通过
- [ ] 后端 auth 相关测试全通过，且包含无 override 的 wiring 集成测试
- [ ] 启动检查与 auth 日志能够定位失败原因

## 执行顺序（/execute）
1. `/execute phase-1`：前端代理与配置说明（清除 404）
2. `/execute phase-2`：后端 auth DI + repository + 事务兜底（清除 500）
3. `/execute phase-3`：指定账号注册登录回归
4. `/execute phase-4`：防回归测试、启动检查、日志告警
