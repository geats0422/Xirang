# 息壤后端 V1 设计规格

## 1. 背景与目标

前端应用已完成第一轮 PRD 对齐，当前仓库缺少与之配套的后端系统。V1 后端需要基于既有数据库设计、FastAPI、SQLAlchemy、OpenAI Agents SDK、自部署 PageIndex 和 pgvector，打通从文档上传到游戏化学习、结算、错题解析、站内购买与用户反馈学习的完整闭环。

本产品按两个开发阶段完成同一个 V1：第一阶段优先完成核心闭环并联调测试；第二阶段补齐支付、复杂赛季、运营后台和 OAuth 等扩展能力。系统同时支持开源版与闭源版，两者共享业务架构，仅在模型接入策略、部署方式和可配置能力上分化。

### 1.1 V1 第一阶段核心闭环

第一阶段必须打通以下链路：

1. 用户注册 / 登录 / refresh / 登出
2. 上传文档后立即在书库可见，状态为 `processing`
3. 后台完成解析、PageIndex 建索引、基础题库预生成
4. 文档进入 `ready` 后进入三种模式之一
5. 完成答题并返回规则化 settlement
6. settlement 更新钱包账本并驱动商店站内购买能力
7. 用户可查看错题解析、提交“这题有误”反馈
8. 后台通过自学习智能体总结反馈并写入待审核规则库

### 1.2 V1 第二阶段补齐能力

第二阶段在不推翻第一阶段架构的前提下补齐：

- Google / GitHub / Microsoft OAuth
- 完整商店支付
- 订阅计费
- 周赛季、段位晋升与排行榜扩展
- quest 发奖运营后台
- 开源版多模型切换与 Ollama
- 闭源版模型池切换能力
- 填空题生成、判分与玩法接入
- 账户删除 / 注销
- 问答范围从当前文档扩展到“当前文档 + 历史错题”

## 2. 设计原则

- 单一后端代码库，避免为不同阶段和发行形态拆成多套系统。
- 第一阶段优先保证核心链路稳定，而不是一次性做完整运营系统。
- 文档主检索采用自部署 PageIndex，错题增强采用 pgvector，职责清晰分离。
- 题库采用“上传后预生成基础题库 + 运行时动态组题”的混合模式。
- 业务层不直接耦合具体模型厂商，通过 provider adapter 和 model registry 扩展。
- 第一阶段暴露最小必要接口，但从数据模型层面预留第二阶段扩展位。
- 所有长耗时流程都通过 job + worker 模式异步执行，不阻塞请求线程。
- 奖励、结算、扣费等核心数值必须规则化、可测试、可审计，不能交给 AI 决定。
- 用户反馈必须沉淀为可复查、可演进的知识资产，而不是只做一次性日志。

## 3. 产品范围

### 3.1 第一阶段

- 邮箱密码注册登录
- JWT access token + refresh token
- 文档上传、解析、处理状态查询、失败重试
- 自部署 PageIndex 树索引生成与当前文档问答检索
- 基础题库预生成
- 三种游戏模式统一 run 流程
- 统一 settlement 结算
- 错题记录、错题向量化、错题增强解析
- 用户反馈收集与自学习总结
- 基础学习推荐
- 基础 profile / settings
- 钱包余额视图 + 钱包账本
- 最小可用商店：coins 扣减、道具购买、库存增加
- 全局累计 leaderboard 只读接口

### 3.2 第二阶段

- Google / GitHub / Microsoft OAuth
- 完整商店支付
- 订阅计费
- 复杂排行榜赛季系统
- quest 发奖运营后台
- 开源版多模型切换与 Ollama
- 闭源版模型池切换能力
- 填空题能力
- 账户删除 / 注销

### 3.3 发行形态

- 开源版：支持自部署、后续支持 Ollama 和用户可选模型。
- 闭源版：仅开放系统配置的模型供应池，用户只能在可见模型列表中切换。

## 4. 关键决策

### 4.1 开发与部署策略

- 默认开发 / 验收环境为本地单机环境。
- 本地开发数据库为本机安装的 PostgreSQL。
- 本地文件上传默认保存到本地文件系统。
- 前端部署目标：Vercel。
- 后端部署目标：Render。
- 线上数据库目标：Supabase。
- 线上文件存储目标：对象存储（S3 兼容或等价方案）。

### 4.2 认证策略

- 第一阶段仅启用邮箱密码登录。
- access token 用于接口鉴权，refresh token 用于续期。
- refresh token 采用服务端会话管理和可吊销策略，不做纯无状态刷新。
- 从第一阶段起保留 `auth_identities` 相关扩展位，以兼容第二阶段 OAuth。
- 账户删除 / 注销第一阶段不做，但数据模型需兼容软删除或注销能力。

### 4.3 存储策略

- 文件存储采用双模式：
  - 本地开发使用本地文件系统
  - 部署环境切换到对象存储
- 文件存储必须通过抽象层访问，不能在业务逻辑里写死具体实现。
- 上传成功后文档需立即出现在书库中，状态先显示为 `processing`。
- 解析失败后文档保留在列表中，状态为 `failed`，并允许重试。

### 4.4 文档与接入策略

- 第一阶段支持格式：PDF、DOCX、TXT、Markdown。
- 文档 `ready` 的定义不是“文件上传成功”，而是：
  - 文本解析完成
  - PageIndex 建索引完成
  - 基础题库生成完成
- 文件处理失败不自动删除记录。

### 4.5 检索与知识层策略

- 文档主检索、自主问答、章节定位使用自部署 PageIndex。
- pgvector 仅负责错题 embedding、相似错题召回、相似知识点增强解释。
- 不将整套文档主检索建立在向量库之上，避免两套检索职责混乱。
- 第一阶段问答范围严格限制为当前文档。
- 第二阶段再扩展到“当前文档 + 历史错题”联合问答。

### 4.6 题目生成与题型策略

- 用户上传文档后，后台异步完成解析、索引和基础题库生成。
- 用户进入具体模式时，再基于模式规则从基础题库中动态组题。
- 三种模式共享底层题库，但采用不同的组题和计分规则。
- 第一阶段题型范围：单选、多选、判断。
- 填空题放到第二阶段实现。
- 基础题库必须在文档 `ready` 前完整生成，不采用“先部分生成、后续补齐”的策略。

### 4.7 模型与智能体策略

- 第一阶段固定单模型运行，用于题库生成、问答、错题解析和学习推荐。
- 业务层通过 provider adapter 抽象模型调用。
- 后续开源版支持 Ollama 和用户自选模型；闭源版支持平台配置模型池。
- 第一阶段不开放真实多模型切换给最终用户。

### 4.8 学习推荐策略

- 第一阶段学习推荐输出结构化结果：
  - 推荐章节或知识点
  - 推荐原因
  - 下一步建议
- 第一阶段不做完整个性化多步学习路径。

### 4.9 结算与经济系统策略

- settlement 的 XP、coins、combo、倍率等核心奖励完全通过规则公式计算。
- AI 不参与奖励数值的决定。
- 钱包系统第一阶段必须使用真实账本（ledger）落库，不允许只维护一个余额字段。
- 第一阶段商店需要最小可用购买闭环：
  - 使用站内 coins 购买道具
  - 扣减余额
  - 写入账本
  - 增加库存
- 完整支付能力放到第二阶段。

### 4.10 排行榜与赛季策略

- 第一阶段仅实现全局累计排行榜。
- 本周榜、周赛季、段位晋升逻辑全部放到第二阶段。
- 一个赛季固定为一周。
- 赛季起止：周一开始，周日结束。
- 每个赛季前 5 名晋升到下一个段位。
- 建议默认使用 `Asia/Shanghai` 时区；若部署环境有不同要求，可通过配置覆盖。

### 4.11 用户反馈与自学习策略

- “这题有误”反馈必须持久化到独立反馈域。
- 反馈数据不能只作为日志存在，必须可检索、可聚合、可追踪来源题目与文档。
- 后台需调用基于 OpenAI Agents SDK 的自学习智能体，对反馈进行总结、归类和改进建议生成。
- 第一阶段自学习智能体只生成建议，并写入待审核规则库。
- 第一阶段不允许自学习智能体直接修改线上题库、提示词或规则。

### 4.12 后台任务策略

- 第一阶段采用“独立 worker 进程 + job 表驱动”的模式。
- 第一阶段不引入 Celery / Redis 等更重型队列系统。
- 第二阶段可以升级到 Celery / Redis 或等价独立队列方案。

## 5. 架构设计

### 5.1 总体架构

```text
Vue Frontend
    |
    v
FastAPI API Layer
    |
    +-- Auth Service
    +-- Document Service
    +-- Question Bank Service
    +-- Run / Settlement Service
    +-- Mistake Review Service
    +-- Feedback Learning Service
    +-- Profile / Settings Service
    +-- Wallet / Shop / Leaderboard Service
    |
    +-- AI Orchestrator (OpenAI Agents SDK)
    |      +-- Retrieval Adapter
    |      |      +-- Self-hosted PageIndex
    |      |      +-- pgvector mistake recall
    |      +-- LLM Provider Adapter
    |      +-- Feedback Self-Learning Agent
    |
    +-- Separate Worker Process
    |      +-- Document Processing Jobs
    |      +-- Question Generation Jobs
    |      +-- Embedding Jobs
    |      +-- Feedback Learning Jobs
    |
    +-- SQLAlchemy + PostgreSQL + pgvector
```

### 5.2 推荐目录结构

```text
backend/
  app/
    api/
      v1/
    core/
    db/
      models/
    schemas/
    repositories/
    services/
      auth/
      documents/
      questions/
      runs/
      review/
      feedback/
      settings/
      leaderboard/
      wallet/
      shop/
      llm/
      retrieval/
    workers/
    integrations/
      pageindex/
      agents/
      storage/
  tests/
scripts/
```

### 5.3 分层职责

- API 层：参数校验、认证依赖、响应模型、错误映射。
- Service 层：业务编排、事务边界、领域规则、任务调度入口。
- Repository 层：SQLAlchemy 数据访问、查询封装。
- Integration 层：PageIndex、LLM provider、OpenAI Agents SDK、对象存储与向量化适配。
- Worker 层：处理长耗时异步任务和重试策略。

## 6. 核心领域模块

### 6.1 Auth

- 用户注册、登录、刷新、退出、当前会话查询。
- 密码哈希和 refresh token rotation。
- 第二阶段扩展 OAuth provider link/unlink。

### 6.2 Profile / Settings

- 用户基础资料、昵称、头像、偏好设置。
- 设置项包括主题、语言、交互偏好和 AI 设置占位。
- 第一阶段模型设置保存为平台级或用户级占位，不启用真实多模型切换。

### 6.3 Documents / Ingestion

- 文件上传后创建 `document` 和 `ingestion_job`。
- 文档状态：`uploaded / processing / ready / failed`。
- 上传成功后文档必须立即可见。
- 失败状态必须支持重试。
- 后台处理：文本提取、章节结构抽取、PageIndex 树索引生成、基础题库预生成。

### 6.4 Retrieval

- `pageindex_backend` 负责文档树检索、文档问答、章节定位。
- `vector_review_backend` 负责错题相似项召回。
- 两者对上游提供统一领域方法，但内部实现保持分离。
- 第一阶段问答严格限制为当前文档。

### 6.5 Question Bank

- 一个文档对应一套基础题库。
- 题目维度包括：知识点、题型、难度、来源章节、解析草稿。
- 第一阶段题型仅为单选、多选、判断。
- 运行时根据模式选题，不直接在模式里生成原始题目。

### 6.6 Run / Settlement

- 所有模式共享 `run` 实体。
- `run_answers` 记录每次作答。
- `settlement` 统一返回 XP、coins、combo、goal progress、奖励倍率和错题摘要。
- settlement 的核心奖励全部由规则层计算，不依赖 AI。
- 提交答案接口必须具备幂等保护。

### 6.7 Mistake Review

- 错题入库时保存题目、用户答案、正确答案、来源文档和章节。
- 后台生成 embedding。
- 解析时结合原题、文档上下文、PageIndex 章节信息和相似错题生成增强解释。

### 6.8 Feedback Learning

- 用户对题目提交“这题有误”反馈后，系统创建独立反馈记录。
- 反馈记录必须能关联用户、题目、文档、run、时间和反馈内容。
- 后台通过自学习智能体对反馈进行分类、总结和建议生成。
- 输出写入待审核规则库，供后续人工审查与策略迭代。
- 第一阶段不允许自动把建议直接应用到生产题库与提示词。

### 6.9 Wallet / Shop / Inventory / Leaderboard

- 钱包需要余额投影与真实账本并存。
- 第一阶段商店必须支持 coins 扣减购买与库存更新。
- 第一阶段排行榜只提供全局累计榜只读能力。
- 第二阶段扩展周赛季、晋升、完整支付和运营规则。

## 7. 核心数据流

### 7.1 文档上传与处理

```text
上传文档
  -> 创建 document / ingestion_job
  -> 文档立即出现在书库中，状态 processing
  -> worker 解析文件
  -> 自部署 PageIndex 生成树索引
  -> 生成基础题库
  -> 成功则 document 进入 ready
  -> 失败则进入 failed，可发起 retry
```

### 7.2 游戏运行

```text
选择文档和模式
  -> 创建 run
  -> 基于题库动态组题
  -> 返回第一题和运行态
  -> 用户提交答案
  -> 更新 run / answer / score / state
  -> 重复直到结束
  -> 生成 settlement
  -> settlement 更新钱包账本和进度视图
```

### 7.3 错题复习

```text
生成错题记录
  -> 后台向量化
  -> 用户请求错题解释
  -> 结合 PageIndex 文档上下文和 pgvector 相似错题
  -> 返回增强解析与复习建议
```

### 7.4 用户反馈与自学习

```text
用户点击“这题有误”
  -> 创建 feedback record
  -> worker 收集反馈上下文
  -> 自学习智能体总结问题类型与改进建议
  -> 写入待审核规则库
  -> 供后续人工确认后进入第二阶段更强闭环
```

### 7.5 商店购买

```text
用户选择商品
  -> 校验余额
  -> 扣减 wallet coins
  -> 写入 wallet_ledger
  -> 增加 inventory
  -> 返回最新余额与购买结果
```

## 8. API 设计

统一前缀使用 `/api/v1`。

### 8.1 Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### 8.2 Documents

- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/status`
- `POST /api/v1/documents/{document_id}/retry`
- `GET /api/v1/documents/{document_id}/questions/summary`

### 8.3 Document AI

- `POST /api/v1/documents/{document_id}/ask`
- `GET /api/v1/documents/{document_id}/study-recommendation`

### 8.4 Runs

- `POST /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/answers`
- `POST /api/v1/runs/{run_id}/feedback`
- `GET /api/v1/runs/{run_id}/settlement`

### 8.5 Review / Feedback

- `GET /api/v1/review/mistakes`
- `GET /api/v1/review/mistakes/{mistake_id}`
- `POST /api/v1/review/mistakes/{mistake_id}/explain`
- `POST /api/v1/feedback/questions/{question_id}`

### 8.6 Profile / Settings

- `GET /api/v1/profile`
- `PATCH /api/v1/profile`
- `GET /api/v1/settings`
- `PATCH /api/v1/settings`

### 8.7 Wallet / Shop / Leaderboard

- `GET /api/v1/wallet`
- `GET /api/v1/wallet/ledger`
- `GET /api/v1/shop/items`
- `POST /api/v1/shop/purchase`
- `GET /api/v1/leaderboard/global`

### 8.8 Jobs

- `GET /api/v1/jobs/{job_id}`

用于轮询文档摄入、题库生成、向量化和反馈学习等后台任务状态。

## 9. 后台任务边界

### 9.1 异步任务

- 文件解析
- PageIndex 树索引生成
- 基础题库预生成
- 错题 embedding 生成
- 反馈学习总结与规则写入
- 推荐与统计更新

### 9.2 同步请求

- 注册、登录、刷新、退出
- 获取文档列表和详情
- 创建 run
- 提交答案
- 获取 settlement
- 保存 profile / settings
- 发起商店购买
- 提交题目反馈

### 9.3 Worker 模型

- 第一阶段采用独立 worker 进程运行。
- Worker 通过 job 表拉取待处理任务。
- 默认重试策略为 3 次指数退避。
- 第一阶段不引入 Celery / Redis。
- 第二阶段可升级为更重型独立队列系统。

## 10. 数据模型建议

以下为第一阶段建议优先落地的核心领域表：

- `users`
- `auth_credentials`
- `auth_sessions`
- `auth_identities`（第一阶段预留）
- `profiles`
- `user_settings`
- `documents`
- `document_ingestion_jobs`
- `document_pageindex_trees`
- `document_question_sets`
- `questions`
- `question_options`
- `runs`
- `run_questions`
- `run_answers`
- `settlements`
- `mistakes`
- `mistake_embeddings`
- `question_feedback`
- `feedback_learning_jobs`
- `review_rule_candidates`
- `wallets`
- `wallet_ledger`
- `inventories`
- `purchase_records`
- `leaderboard_snapshots`（第一阶段仅全局累计）
- `jobs`
- `audit_logs`

第二阶段补齐：

- `oauth_states`
- `subscriptions`
- `billing_orders`
- `payment_transactions`
- `league_tiers`
- `seasons`
- `season_participations`
- `season_results`
- `promotion_records`
- `quest_templates`
- `quest_assignments`
- `quest_reward_logs`
- `admin_operation_logs`

## 11. 默认值与运行约束

- 本地上传默认目录：`backend/.data/uploads/`
- 文件大小默认硬限制：`50MB`
- 推荐文档大小：`20MB` 及以下
- 文档处理与反馈学习任务默认重试：3 次 + 指数退避
- 第一阶段问答严格限制为当前文档
- 第一阶段不开放填空题
- 第一阶段不开放真实支付
- 第一阶段不开放周赛季与晋升逻辑

## 12. 错误处理策略

统一错误结构：

```json
{
  "code": "DOCUMENT_PROCESSING_FAILED",
  "message": "Document processing failed",
  "details": {},
  "request_id": "req_xxx"
}
```

### 12.1 错误分类

- 认证类：token 失效、refresh 失效、密码错误、用户不存在。
- 文档类：文件类型不支持、文件超限、解析失败、PageIndex 调用失败、题库生成失败、重试失败。
- 运行类：run 不存在、run 已结束、重复提交、题目与 run 不匹配、余额不足。
- AI 类：模型不可用、超时、结构化输出解析失败、反馈学习失败。
- 系统类：数据库错误、任务执行失败、外部服务不可用。

### 12.2 处理原则

- 文档处理失败后保留失败状态和错误信息，不直接删除文档记录。
- 提交答案接口需支持幂等，避免重复点击造成重复结算。
- AI 能力失败时优先返回降级结果，而不是直接中断主链路。
- 反馈学习失败不影响用户主链路，只影响规则沉淀质量。
- 商店购买失败时必须保持账本和库存一致性。

## 13. 测试策略

### 13.1 总体要求

- 第一阶段测试覆盖必须包含：单元测试、集成测试、完整关键路径 E2E。
- 所有核心任务采用 TDD 思路：RED -> GREEN -> REFACTOR。
- 核心验证框架：pytest + httpx。

### 13.2 单元测试

- 认证：密码哈希、JWT、refresh rotation、会话吊销。
- 文档：上传校验、状态机、任务创建、失败重试。
- PageIndex 适配：索引调用、检索结果标准化、故障降级。
- 题库：结构化输出校验、题型过滤、难度分层、章节归属。
- run：组题器、计分器、结算器。
- 钱包与商店：余额校验、ledger 写入、库存增加。
- 错题与反馈：反馈记录、向量化任务触发、相似错题召回、规则候选生成。
- provider adapter：默认模型调用和异常兜底。

### 13.3 集成测试

- 注册 -> 登录 -> refresh -> logout。
- 上传文档 -> 后台处理 -> ready / failed / retry。
- 文档 ready 后创建 run。
- 提交答案 -> 更新状态 -> 获取 settlement。
- 商店购买 -> 扣减 coins -> 写入 ledger -> 增加库存。
- 错题解释返回增强结果。
- 题目反馈进入自学习闭环。
- settings / profile 持久化。

### 13.4 端到端测试

- 第一阶段完整主闭环：
  - 注册 / 登录
  - 上传文档
  - 等待处理完成
  - 进入任一模式
  - 完成一局
  - 查看结算
  - 发起商店购买
  - 查看错题解释
  - 提交“这题有误”反馈
- 第二阶段补充验证：
  - 周赛季结算
  - Top 5 晋升
  - OAuth
  - 支付 / 订阅
  - 填空题能力

## 14. 部署与配置策略

### 14.1 本地开发

- 前端本地开发保持现有 Vue/Vite 流程。
- 后端本地开发运行在 `backend/`。
- 本地数据库使用本机安装的 PostgreSQL。
- 本地文件存储使用本地磁盘目录。

### 14.2 生产部署

- 前端部署到 Vercel。
- 后端部署到 Render。
- 数据库部署使用 Supabase。
- 文件存储切换到对象存储。

### 14.3 配置抽象

- 数据库连接、文件存储、PageIndex 地址、LLM provider、worker 轮询参数都必须通过配置注入。
- 业务层不能写死本地路径、本地 URL 或具体模型供应商。

## 15. 风险与缓解

- **自部署 PageIndex 集成复杂**
  - 缓解：封装 retrieval adapter，优先建立健康检查、最小链路和 smoke test。
- **大模型输出不稳定导致题目质量波动**
  - 缓解：题目生成一律使用结构化输出和入库前校验。
- **文档处理链路过长影响体验**
  - 缓解：全部走后台任务，前端轮询 job status。
- **模式逻辑分叉后难维护**
  - 缓解：统一 run 领域模型，仅规则层分叉。
- **开源版与闭源版分叉演变为两套系统**
  - 缓解：统一 provider adapter 和 model registry，差异通过配置和可见模型列表控制。
- **第二阶段赛季返工风险**
  - 缓解：第一阶段提前预留相关表和服务边界。
- **pgvector 索引维护成本上升**
  - 缓解：第一阶段仅向量化错题和复习相关样本，不承担主文档检索。
- **自学习智能体误判风险**
  - 缓解：第一阶段只写待审核规则库，不允许自动生效。
- **账本与库存不一致风险**
  - 缓解：购买流程必须具备事务边界与一致性校验。

## 16. 非目标

第一阶段不追求以下能力完整上线：

- 全量 OAuth 登录
- 完整支付闭环
- 完整订阅计费管理
- 复杂排行榜赛季规则
- quest 发奖运营后台
- 面向最终用户的多模型切换
- 填空题生成与判分
- 账户删除 / 注销
- 跨文档自由问答
- 自学习规则自动生效
- Celery / Redis 队列体系

## 17. 验收标准

- 用户可以完成注册、登录、refresh 和退出。
- 用户可以上传 PDF / DOCX / TXT / Markdown，并立即看到 `processing` 状态。
- 文档处理失败后可见且可重试。
- 文档处理完成后必须已生成基础题库，才能进入可学习状态。
- 三种游戏模式都能基于统一题库创建 run 并完成答题。
- run 结束后可以返回规则化 settlement。
- 钱包账本与商店购买闭环可用。
- 错题可以被记录，并生成增强解释。
- 用户反馈可以被记录，并沉淀为待审核规则建议。
- 基础问答与学习推荐可以围绕当前文档工作。
- profile / settings 可以持久化。
- 全局累计排行榜可读。
- 第一阶段闭环可完成联调测试。
- 第二阶段可以在不推翻第一阶段架构的前提下补齐 OAuth、支付、赛季、运营后台、填空题与高级模型能力。

## 18. 后续动作

- 本设计已根据 20 轮澄清结果补全。
- 后续应以本设计作为计划与执行的权威来源。
- 下一步进入实现执行时，应使用 `build` 会话而不是 `planner` 会话。
