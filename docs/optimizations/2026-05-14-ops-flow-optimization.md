# 优化规格文档

**日期**: 2026-05-14
**基于报告**: `docs/insights/2026-05-14-insights.md`
**优化范围**: 配置稳定性、回归防线、流程可追踪性

---

## 优先级矩阵

| 优先级 | 优化项 | 影响 | 成本 | 影响/成本 | 选择 |
|---|---|---:|---:|---:|---|
| P0 | 登录与路由关键回归测试补齐 | 9 | 3 | 9.0 | 本次 |
| P0 | 部署配置检查清单与摩擦日志制度化 | 8 | 2 | 12.0 | 本次 |
| P1 | commands 文件化并增加存在性校验 | 7 | 2 | 10.5 | 本次 |
| P2 | learnings 周期化沉淀（/learn-status + /learn-evolve） | 6 | 3 | 6.0 | 下次 |

---

## 优化项 1: 登录与路由关键回归测试补齐 [P0]

### 问题描述
- 过去 30 天 fix 占比 66.7%，登录链路与前端路由是高频摩擦点。

### 优化方案
1. 针对 `resolveUrl` 的 baseUrl/path 组合增加边界测试。
2. 针对登录成功后路由跳转补充行为测试（含懒加载页面进入路径）。
3. 涉及认证、路由、i18n 变更时要求同步更新测试。

### 预期效果
| 指标 | Before | After | 改善 |
|---|---:|---:|---:|
| 登录链路相关修复提交占比 | 66.7% | < 40% | -40%+ |
| 认证路径拼接回归问题 | 偶发 | 0 | -100% |

### 验证
- 前端执行: `npm run lint && npm run typecheck && npm run test -- src/api/http.spec.ts`

---

## 优化项 2: 部署配置检查清单与摩擦日志制度化 [P0]

### 问题描述
- 部署环境变量和域名切换导致线上/本地表现不一致。
- 缺少结构化摩擦日志，复盘成本高。

### 优化方案
1. 建立 `docs/friction-log.md`，每次返工/阻塞强制记录。
2. 增加部署变更检查清单：域名、rewrite、CORS、OAuth 回调、缓存策略。
3. 每周运行一次 `/insights`，引用该日志形成趋势分析。

### 预期效果
| 指标 | Before | After | 改善 |
|---|---:|---:|---:|
| 环境类问题定位时长 | 高且波动 | 稳定可追踪 | 明显下降 |
| 非代码摩擦可检索性 | 无 | 有统一记录 | +100% |

### 验证
- 检查 `docs/friction-log.md` 是否存在并包含当周条目。

---

## 优化项 3: commands 文件化并增加存在性校验 [P1]

### 问题描述
- command 仅集中在 `opencode.json`，缺少可审阅的文件化索引。
- `/sync-config` 和 `create-project` 缺少对 commands 元数据存在性的显式检查。

### 优化方案
1. 新增 `.opencode/commands/manifest.json` 作为命令元数据索引。
2. 为关键命令新增文档：`sync-config.md`、`create-project.md`。
3. 在命令模板中加入前置检查：缺失 manifest 或关键命令条目时中止。

### 预期效果
| 指标 | Before | After | 改善 |
|---|---:|---:|---:|
| 命令可审阅性 | 低 | 高 | +100% |
| 命令同步遗漏风险 | 中 | 低 | 明显下降 |

### 验证
- 检查以下文件存在：
  - `.opencode/commands/manifest.json`
  - `.opencode/commands/sync-config.md`
  - `.opencode/commands/create-project.md`
- 运行 `/sync-config` 与 `create-project` 时应先执行 commands 存在性检查。

---

## 风险与回滚
- 风险: command 模板文本变长，执行成本略增。
- 回滚: 仅回退 `.opencode/commands/*` 与 `opencode.json` command 片段，不影响业务代码。

## 下一步
1. 运行 `/plan` 把本优化 spec 拆为 2-5 分钟任务。
2. 按 `/execute` 实施并在 `/finish` 前再次验证线上登录链路。
