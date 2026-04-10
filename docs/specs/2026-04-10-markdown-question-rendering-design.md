# 题目内容 Markdown 渲染优化设计规格

## 1. 背景与目标

当前题目生成链路已支持：
- Markdown 文档直接生成题目
- PDF/PPT/Word 经 MinerU 解析为 Markdown 后生成题目

但前端题目展示层仍是纯文本插值渲染，导致以下 Markdown 语法无法正确呈现：
- 行内代码（`` `code` ``）
- 粗体/斜体（`**bold**` / `*italic*`）
- fenced code block（``` ... ```）
- 列表、表格、链接、删除线等

本设计目标：
- 在不改后端存储结构的前提下，实现前端题目内容的 Markdown 实时渲染
- 代码块支持语法高亮
- 保证渲染安全（防 XSS）
- 不破坏现有答题、判题、结算与反馈流程

## 2. 现状与约束

### 2.1 后端链路现状

- 文档上传后由 worker 执行解析、规范化、索引、出题、入库。
- MinerU 产物与 Markdown 直传内容最终都作为文本进入题目生成。
- 题目字段（题干、选项、解析）存储为文本字符串，不是 HTML。

### 2.2 前端渲染现状

- 题目页以 `{{ }}` 插值渲染题干、选项、解析。
- 无 `v-html` 渲染路径。
- 无 Markdown 渲染库与代码高亮库依赖。

### 2.3 设计约束

- 渲染策略固定为“前端实时渲染”。
- 需要支持扩展语法，不仅限于基础 Markdown。
- 代码块必须支持语法高亮。
- 必须做安全清洗，禁止执行不可信 HTML/脚本。

## 3. 方案对比与结论

### 3.1 备选方案

1. 前端统一渲染组件（推荐）
2. 后端预渲染 HTML
3. 结构化内容（AST/Token）渲染

### 3.2 选型结论

采用方案 1：前端统一渲染组件。

原因：
- 与当前架构耦合最小
- 不改后端数据结构
- 能快速覆盖 4 个题目页面
- 可复用性高，后续页面可直接接入

## 4. 技术方案

### 4.1 新增统一渲染组件

新增组件：`frontend/src/components/ui/MarkdownRichText.vue`

职责：
- 接收文本内容
- Markdown 解析
- HTML 安全清洗
- 代码块高亮
- 输出受控渲染结果

建议 props：
- `content: string`
- `inline?: boolean`（行内模式，如选项）
- `className?: string`

### 4.2 依赖建议

- Markdown 解析：`markdown-it`
- 代码高亮：`highlight.js`
- 安全清洗：`dompurify`

说明：
- `highlight.js` 仅注册常见语言，控制包体。
- 不启用“直接信任原始 HTML”的路径。

### 4.3 渲染语法范围

支持（本期）：
- 行内代码
- 粗体、斜体、粗斜体
- 删除线
- 列表（有序/无序）
- 链接
- 表格
- fenced code block（含语言标记）

非目标（本期不做）：
- Mermaid
- 数学公式
- 任意嵌入 HTML 的完整支持

### 4.4 页面接入范围

对以下页面进行渲染层替换：
- `frontend/src/pages/DungeonScholarReviewPage.vue`
- `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue`
- `frontend/src/pages/DungeonScholarEndlessAbyssPage.vue`
- `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue`

接入点：
- 题干文本
- 选项文本（按需行内模式）
- 反馈解析文本

Knowledge Draft 特殊规则：
- 保留 blank 槽位逻辑
- 仅 text segment 进入 Markdown 渲染
- blank button/拖拽行为保持现状

### 4.5 样式策略

新增样式文件：`frontend/src/styles/markdown.css`（或组件内受控样式）

样式覆盖：
- `.markdown-rich-text pre code`
- `.markdown-rich-text code`
- `.markdown-rich-text table`
- `.markdown-rich-text ul, ol, li`
- `.markdown-rich-text a`

要求：
- 代码块可横向滚动
- 表格在窄屏可滚动
- 使用现有 token，不破坏整体主题

## 5. 安全设计

### 5.1 清洗策略

所有 Markdown 渲染结果必须经过 DOMPurify 清洗：
- 禁止 `script/style/iframe` 等危险标签
- 去除 `on*` 事件属性
- 限制 URL 协议（`http/https/mailto`）

### 5.2 链接安全

所有外链追加：
- `target="_blank"`
- `rel="noopener noreferrer nofollow"`

## 6. 错误处理与降级

- Markdown 解析失败：回退纯文本展示
- 高亮失败：保留代码块纯样式展示
- 内容为空：展示为空字符串，不抛异常
- 超长代码块：限制高度 + 滚动

## 7. 测试策略

### 7.1 单元测试

新增组件测试覆盖：
- 行内代码、粗体、代码块、表格、链接渲染
- 危险标签与事件属性被清洗
- 异常输入降级

### 7.2 页面回归测试

对 4 个题目页面做关键断言：
- 题干 markdown 可见
- 选项 markdown 可见（不破坏点击/提交）
- 解析 markdown 可见
- 交互流程不受影响

### 7.3 手动验证样例

验证内容集：
- `这里有 **粗体** 和 *斜体*`
- ``行内代码: `const a = 1` ``
- 带语言代码块（js/python）
- 表格和列表
- 含恶意 payload 的字符串（验证被清洗）

## 8. 风险与缓解

### 风险 1：包体积增加
- 缓解：高亮语言按需注册；后续可切分懒加载。

### 风险 2：样式冲突
- 缓解：样式命名空间隔离在 `.markdown-rich-text`。

### 风险 3：历史题面格式不规范
- 缓解：解析失败回退纯文本，保障可答题。

### 风险 4：XSS 安全风险
- 缓解：统一 DOMPurify 清洗，禁止绕过组件直出 HTML。

## 9. 验收标准

满足以下全部条件即验收通过：
- 4 个题目页面均支持扩展 Markdown 渲染。
- `` `code` ``、`**bold**`、``` ``` 代码块等可正确显示。
- 代码块高亮生效。
- 恶意脚本无法执行。
- 题目作答、判分、反馈、结算流程无回归问题。

## 10. 上线与回滚

上线策略：
- 先在测试环境全量验证样例内容。
- 通过后发布生产。

回滚策略：
- 保留旧文本渲染分支（临时开关或快速回退提交）。
- 出现异常时回退到纯文本渲染路径。
