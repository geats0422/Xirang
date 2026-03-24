# AGENTS.md

> 基于 `everything-claude-code` 系统化理念与 `oh-my-opencode` 工作流，构建的**可扩展、可维护、可调试**的 AI Coding 配置。
>
> 本配置整合了 12 个专用智能体、24 个高频命令、50+ 可复用技能、11 个自动化插件与 7 个自定义工具。

---

## 1. 核心原则

### 1.1 清晰优先

未被清晰定义的流程，不自动化。涉及架构取舍、破坏性修改、安全风险、上线决策时，必须交由人类确认。

### 1.2 小步快跑

优先选择小步推进、可验证中间产物，而不是大包大揽的一次性生成。

### 1.3 明确边界

command、skill、plugin、sub-agent 各自解决不同层级问题，不混用。

### 1.4 验证为证

任何实现、重构、修复，都优先要求证据链：代码、测试、日志、diff、文档更新。

### 1.5 项目上下文优先

所有行动优先遵循当前仓库的 README、docs、现有代码风格、lint/test/build 约束。

### 1.6 不可变性

始终创建新对象，永不修改现有对象。不可变数据防止隐藏副作用，使调试更容易，并支持安全并发。

---

## 2. 智能体编排

本配置采用"主智能体 + 专项子智能体"的结构。

### 2.1 可用智能体

位于 `.opencode/agents/`：

#### 主智能体

| 智能体 | 用途 | 使用场景 |
|--------|------|----------|
| build | 主开发 Agent | 处理大多数开发任务 |
| planner | 任务规划 | 复杂功能、重构 |
| architect | 系统设计 | 架构决策 |
| code-reviewer | 代码审查 | 代码编写后 |
| security-reviewer | 安全分析 | 提交前 |

#### 子智能体

| 智能体 | 用途 | 使用场景 |
|--------|------|----------|
| tdd-guide | 测试驱动开发 | 新功能、Bug 修复 |
| build-error-resolver | 修复构建错误 | 构建失败时 |
| e2e-runner | 端到端测试 | 关键用户流程 |
| refactor-cleaner | 死代码清理 | 代码维护 |
| doc-updater | 文档更新 | 更新文档 |
| python-reviewer | Python 代码审查 | Python 代码编写后 |
| python-build-resolver | 修复 Python 构建错误 | Python 构建失败时 |
| database-reviewer | 数据库审查 | 数据库相关审查 |

### 2.2 智能体调用规则

无需用户提示，主动使用智能体：

| 场景 | 智能体 |
|------|--------|
| 复杂功能请求 | **planner** |
| 代码编写/修改后 | **code-reviewer** |
| Bug 修复或新功能 | **tdd-guide** |
| 架构决策 | **architect** |
| Python 代码审查 | **python-reviewer** |
| Python 构建错误 | **python-build-resolver** |
| 构建失败 | **build-error-resolver** |
| 端到端测试 | **e2e-runner** |
| 代码清理 | **refactor-cleaner** |
| 文档更新 | **doc-updater** |
| 安全审查 | **security-reviewer** |
| 数据库审查 | **database-reviewer** |

### 2.3 并行执行

对于独立操作，始终并行执行：

```markdown
# 推荐：并行执行
并行启动 3 个智能体：
1. 智能体 1：认证模块安全分析
2. 智能体 2：缓存系统性能审查
3. 智能体 3：工具类型检查
```

### 2.4 多视角分析

对于复杂问题，使用角色分离的子智能体：
- 事实审查员
- 高级工程师
- 安全专家
- 一致性审查员
- 冗余检查器

---

## 3. 命令层

command 是用户高频入口，应该短、小、明确。

### 3.1 可用命令

位于 `.opencode/commands/`：

| 命令 | 描述 | Agent |
|------|------|-------|
| plan | 使用 planner agent 规划复杂任务 | planner |
| tdd | 测试驱动开发 - 先写测试，再写实现 | tdd-guide |
| code-review | 代码审查 | code-reviewer |
| e2e | 端到端测试 | e2e-runner |
| refactor-clean | 死代码清理 | refactor-cleaner |
| security | 安全审查 | security-reviewer |
| verify | 验证实现 | build |
| build-fix | 修复构建错误 | build-error-resolver |
| test-coverage | 检查测试覆盖率 | build |
| update-docs | 更新文档 | doc-updater |
| update-codemaps | 更新代码地图 | doc-updater |
| python-build | Python 项目构建 | build |
| python-review | Python 代码审查 | python-reviewer |
| python-test | Python 项目测试 | build |
| skill-create | 创建新技能 | build |
| orchestrate | 多智能体编排 | build |
| evolve | 演进优化 | build |
| checkpoint | 创建检查点 | build |
| eval | 评估验证 | build |
| learn | 学习模式 | build |
| setup-pm | 配置包管理器 | build |
| instinct-export | 导出本能 | build |
| instinct-import | 导入本能 | build |
| instinct-status | 本能状态 | build |
| brainstorm | 设计探索流程 | build |
| execute | 执行任务+两阶段审查 | build |
| finish | 完成开发分支 | build |
| quality | 代码质量评估 | code-quality-evaluator |

### 3.2 命令设计原则

- 一个命令只做一类事
- 命令名称尽量动词化
- 命令可以编排 skill，但不要直接承载复杂业务逻辑
- 命令输出要保持固定结构

---

## 4. 技能层

skill 用于封装可复用流程，而不是封装一切动作。

### 4.1 已配置技能

位于 `.opencode/skills/`：

#### 核心开发技能

| 技能 | 用途 |
|------|------|
| tdd-workflow | TDD 开发工作流 |
| verification-loop | 验证循环 |
| search-first | 搜索优先 |
| coding-standards | 编码标准 |
| brainstorming | 设计探索流程 |
| planning | 实现计划生成 |
| task-execution | 任务执行+两阶段审查 |
| systematic-debugging | 系统化调试 |
| finishing-a-development-branch | 完成开发分支 |
| code-quality-evaluation | 代码质量评估 |

#### Python 相关技能

| 技能 | 用途 |
|------|------|
| python-patterns | Python 设计模式 |
| python-testing | Python 测试实践 |

#### 数据库相关技能

| 技能 | 用途 |
|------|------|
| postgres-patterns | PostgreSQL 模式 |
| database-migrations | 数据库迁移 |
| clickhouse-io | ClickHouse IO |

#### 前端相关技能

| 技能 | 用途 |
|------|------|
| frontend-patterns | 前端模式 |
| frontend-slides | 前端幻灯片 |
| api-design | API 设计 |

#### 基础设施技能

| 技能 | 用途 |
|------|------|
| docker-patterns | Docker 模式 |
| deployment-patterns | 部署模式 |

#### 安全与测试技能

| 技能 | 用途 |
|------|------|
| security-review | 安全审查 |
| security-scan | 安全扫描 |
| e2e-testing | 端到端测试 |

#### 学习与优化技能

| 技能 | 用途 |
|------|------|
| continuous-learning | 持续学习 |
| cost-aware-llm-pipeline | LLM 成本优化 |
| iterative-retrieval | 迭代检索 |
| strategic-compact | 策略精简 |

### 4.2 反模式

以下内容不建议封装为 skill：

- 纯一次性个人偏好的 prompt
- 没有固定输入输出边界的闲聊流程
- 高度依赖当前单个项目上下文且不可复用的逻辑
- 包含多个独立职责的大而全 mega-skill

---

## 5. 插件层

plugin 只自动处理**高确定性、低歧义、低破坏性**动作。

### 5.1 可用插件

位于 `.opencode/plugins/`：

| 插件 | 功能 |
|------|------|
| auto-lsp | 自动检测项目语言并配置 LSP |
| auto-format | 自动格式化代码 |
| typescript-check | TypeScript 类型检查 |
| console-log-warning | 控制台日志警告 |
| dev-server-blocker | 阻止开发服务器冲突 |
| git-push-reminder | Git 推送提醒 |
| tmux-reminder | Tmux 会话提醒 |
| doc-file-warning | 文档文件警告 |
| strategic-compact | 策略精简提示 |
| session-manager | 会话管理 |

### 5.2 适合自动化的场景

- 在开始实现前提醒读取 README / package.json / pyproject.toml
- 在生成代码后提醒运行 lint / test / type-check
- 在修改公共 API 后提醒检查文档与示例
- 在检测到测试文件缺失时提醒补测试
- 在修改配置文件时提醒检查环境变量与样例配置
- 自动检测项目语言并配置 LSP

### 5.3 不适合自动化的场景

- 自动大规模重构
- 自动删除文件
- 自动安装/升级依赖
- 自动提交 git
- 自动修改 CI/CD 配置

### 5.4 插件原则

> 插件的价值在于"提醒与守门"，不是"替代判断"。

---

## 6. 工具层

自定义工具位于 `.opencode/tools/`：

| 工具 | 用途 |
|------|------|
| lint-check | 多语言 lint 检查 |
| format-code | 代码格式化 |
| check-coverage | 测试覆盖率检查 |
| run-tests | 运行测试套件 |
| security-audit | 安全审计 |
| git-summary | Git 状态摘要 |
| auto-lsp | LSP 自动配置 |

---

## 7. 开发工作流

### 7.1 功能实现工作流

1. **先规划**
   - 使用 **planner** 智能体创建实施计划
   - 识别依赖关系和风险
   - 分解为多个阶段

2. **TDD 方法**
   - 使用 **tdd-guide** 智能体
   - 先写测试（红色）
   - 实现以通过测试（绿色）
   - 重构（改进）
   - 验证覆盖率 80%+

3. **代码审查**
   - 编写代码后立即使用 **code-reviewer** 智能体
   - 解决 CRITICAL 和 HIGH 问题
   - 尽可能修复 MEDIUM 问题

4. **提交与推送**
   - 详细的提交信息
   - 遵循 conventional commits 格式

### 7.2 默认工作流

1. Understand context - 理解上下文
2. Restate task in operational terms - 将任务重新表述为可操作术语
3. Identify constraints and risks - 识别约束和风险
4. Propose plan - 提出计划
5. Execute in small increments - 小步执行
6. Verify results - 验证结果
7. Summarize changes and next steps - 总结变更和后续步骤

### 7.3 升级条件

以下情况必须暂停并请求人工确认：

- 需要删除大量代码 / 文件
- 需要修改数据库 schema / API contract
- 需要变更鉴权、权限、安全策略
- 需要引入新基础依赖或替换核心框架
- 需要执行不可逆迁移
- 需求本身存在多个同样合理但影响不同的方向

---

## 8. 验证策略

任何任务完成时，默认给出以下验证结构：

### 8.1 必需验证输出

- **Implemented:** 做了哪些变更
- **Checked:** 验证了哪些内容
- **Not Verified:** 哪些还没验证
- **Risks:** 剩余风险
- **Next Step:** 建议的下一步动作

### 8.2 优先证据

1. 自动化测试通过
2. 静态检查通过
3. 本地运行结果 / 日志
4. 关键 diff 对照
5. 手工推断

---

## 9. 代码质量清单

在标记工作完成前：

- [ ] 代码可读且命名良好
- [ ] 函数短小（<50 行）
- [ ] 文件聚焦（<800 行）
- [ ] 无深层嵌套（>4 层）
- [ ] 适当的错误处理
- [ ] 无硬编码值（使用常量或配置）
- [ ] 无突变（使用不可变模式）

---

## 10. 最小示例交互契约

### 当用户要求"修一个 bug"时

默认顺序：

1. 使用 **planner** 明确 bug 表现、期望行为、复现路径
2. 使用 **explorer** 找到相关模块
3. 使用 **tdd-guide** 做最小修复
4. 使用 **code-reviewer** 验证修复与回归风险
5. 使用 **doc-updater**（如有必要）更新说明

### 当用户要求"新增功能"时

默认顺序：

1. **planner** 规划
2. **tdd-guide** 驱动开发
3. **code-reviewer** 审查
4. **security-reviewer** 安全检查
5. **doc-updater** 更新文档

---

## 13. Superpowers 融合规则（设计先行工作流）

> 融合 Superpowers 的核心工作流理念，形成统一的设计→计划→执行流程。

### 13.1 核心原则

#### 原则 1: 设计先行 (Design-First)
- **任何创造性工作必须经过设计 → 计划 → 执行三阶段**
- 设计未获批，禁止进入计划阶段
- 没有例外，无论任务多小
- "简单"项目的设计可以很短（几句话），但必须有

#### 原则 2: 技能优先 (Skill-First)
- **1% 可能适用技能，就必须检查技能**
- 技能检查优先于任何其他动作
- 包括澄清问题、探索代码、搜索文档之前
- 禁止凭记忆执行流程，必须调用 skill

#### 原则 3: 上下文隔离 (Context Isolation)
- 每个 subagent 只获得任务所需的精确上下文
- 禁止自动继承完整会话历史
- 协调者负责构造和传递上下文

#### 原则 4: 两阶段审查 (Two-Stage Review)
- 每个任务完成后必须经过两次审查
- 阶段A: 规格合规审查（是否符合设计？）
- 阶段B: 代码质量审查（代码是否达标？）
- 两次审查必须使用不同的 agent

### 13.2 工作流命令

| 命令 | 阶段 | 说明 |
|------|------|------|
| `/brainstorm` | 设计 | 完整设计探索流程 |
| `/plan` | 计划 | 基于设计生成实现计划 |
| `/execute` | 执行 | 执行任务 + 两阶段审查 |
| `/finish` | 完成 | 分支完成选项 |

### 13.3 工作流流程

```
用户请求
    ↓
/brainstorm → 澄清问题 → 方案对比 → 设计文档化 → 用户批准
                                    ↓
/plan → 任务分解 → 计划文档化 → 用户确认
                                    ↓
/execute 1 → 实现 → 规格合规审查 → 代码质量审查 → 任务完成
    ↓
/execute 2 → ...
    ↓
/finish → 验证测试 → 合并/PR/清理
```

### 13.4 智能体职责

| Agent | 职责 | 调用时机 |
|-------|------|----------|
| build | 主执行 | 大多数任务 |
| planner | 计划生成 | `/plan` 的 Phase 2 |
| architect | 架构设计 | 复杂架构决策 |
| tdd-guide | TDD 执行 | `/tdd` 命令 |
| code-reviewer | 代码质量审查 | 阶段B审查 |
| spec-compliance-reviewer | 规格合规审查 | 阶段A审查（新增） |
| security-reviewer | 安全审查 | 安全相关 |
| python-reviewer | Python 专项审查 | Python 代码 |
| build-error-resolver | 构建错误修复 | 构建失败 |

### 13.5 禁止的反模式

| 反模式 | 检测方式 | 后果 |
|--------|----------|------|
| 直接写代码未经设计 | 检查是否存在已批准的设计文档 | 停止，返回设计阶段 |
| 跳过审查 | 检查是否有审查记录 | 补充审查 |
| 大上下文派发给子 agent | 检查上下文大小 | 重构上下文 |
| 凭记忆执行流程 | 检查是否调用了 skill | 调用 skill 重来 |
| 多任务同时执行（应串行） | 检查任务依赖关系 | 重新规划 |

### 13.6 触发词 → 命令映射

| 用户输入 | 触发命令 | 说明 |
|----------|----------|------|
| "实现..." | `/brainstorm` | 任何实现请求都先设计 |
| "帮我..." | `/brainstorm` | 任何新需求先设计 |
| "修复bug" | `/brainstorm` | bug 也要设计修复方案 |
| "添加功能" | `/brainstorm` | 新功能完整流程 |
| "重构" | `/brainstorm` | 重构需要设计 |
| "测试" | `/tdd` | 强制 TDD |
| "审查" | `/review` | 直接审查 |
| "执行计划" | `/execute` | 从 Todo 选择任务执行 |
| "完成" | `/finish` | 分支收尾 |

---

## 14. 配置参考

- 智能体配置：`.opencode/agents/`
- 命令配置：`.opencode/commands/`
- 技能配置：`.opencode/skills/`
- 插件配置：`.opencode/plugins/`
- 工具配置：`.opencode/tools/`
- 约束配置：`.opencode/instructions/`

---

## 12. 持续演进

这个 AGENTS.md 的目标不是制造"看起来很强"的配置系统，而是：

- 让 AI agent 的行为更稳定
- 让任务拆分更清晰
- 让验证路径更明确
- 让你能逐步把经验沉淀成结构

当某条规则开始妨碍效率时，不要崇拜规则本身。先检查：它究竟在防什么错，值不值得继续保留。
