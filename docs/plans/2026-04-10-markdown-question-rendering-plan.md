# 题目内容 Markdown 渲染优化实现计划

> **For agentic workers:** 使用 `/execute` 执行单个任务。每个任务都按 RED → GREEN → REFACTOR 顺序执行，不要跳过测试步骤。

**Goal:** 在不改后端存储结构的前提下，为四个题目页面增加安全的 Markdown 实时渲染与代码高亮能力，并保持现有答题流程不变。

**Architecture:** 前端新增统一的 `MarkdownRichText` 渲染组件，内部负责 Markdown 解析、HTML 清洗和代码块高亮。四个题目页面只替换展示层，不改动答题状态流、提交逻辑和接口结构。样式通过独立 markdown 样式命名空间隔离，避免污染现有页面视觉。

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, `markdown-it`, `highlight.js`, `dompurify`

**Design Spec:** `docs/specs/2026-04-10-markdown-question-rendering-design.md`

---

## 文件规划

### 新增文件
- `frontend/src/components/ui/MarkdownRichText.vue`
  - 统一 Markdown 渲染组件
- `frontend/src/components/ui/MarkdownRichText.spec.ts`
  - 组件单测
- `frontend/src/styles/markdown.css`
  - Markdown 渲染专用样式

### 修改文件
- `frontend/package.json`
  - 增加渲染、安全、高亮依赖
- `frontend/src/pages/DungeonScholarReviewPage.vue`
  - 题干、选项、解析改接组件
- `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue`
  - 题干、解析改接组件
- `frontend/src/pages/DungeonScholarEndlessAbyssPage.vue`
  - 题干、解析改接组件
- `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue`
  - 仅 text segment 与解析改接组件，保留 blank 交互
- `frontend/src/main.ts` 或当前全局样式入口文件
  - 引入 `markdown.css`

### 可选新增测试文件
- `frontend/src/pages/DungeonScholarReviewPage.spec.ts`
- `frontend/src/pages/DungeonScholarKnowledgeDraftPage.spec.ts`

说明：优先补最关键的组件测试与一到两个页面回归测试，避免计划膨胀。

---

## Task List

### Task 1: 安装依赖并建立渲染组件骨架

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/components/ui/MarkdownRichText.vue`

- [ ] **Step 1: 写失败测试（RED）**

```ts
import { mount } from "@vue/test-utils";
import MarkdownRichText from "./MarkdownRichText.vue";

describe("MarkdownRichText", () => {
  it("renders bold text from markdown", () => {
    const wrapper = mount(MarkdownRichText, {
      props: { content: "hello **world**" },
    });

    expect(wrapper.html()).toContain("<strong>world</strong>");
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- src/components/ui/MarkdownRichText.spec.ts`
Expected: FAIL

- [ ] **Step 3: 最小实现组件骨架（GREEN）**

```vue
<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{
  content: string;
  inline?: boolean;
}>(), {
  inline: false,
});

const renderedHtml = computed(() => props.content);
</script>

<template>
  <div class="markdown-rich-text" v-html="renderedHtml" />
</template>
```

- [ ] **Step 4: 接入 `markdown-it` / `dompurify` / `highlight.js` 完成真实实现**

```ts
const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code, language) {
    // use highlight.js with fallback
  },
});

const renderedHtml = computed(() => {
  const source = props.content ?? "";
  const html = props.inline ? markdown.renderInline(source) : markdown.render(source);
  return DOMPurify.sanitize(html);
});
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm run test -- src/components/ui/MarkdownRichText.spec.ts`
Expected: PASS

- [ ] **Step 6: 运行 lint/typecheck**

Run:
- `npm run lint`
- `npm run typecheck`

- [ ] **Step 7: 提交**

```bash
git add frontend/package.json frontend/src/components/ui/MarkdownRichText.vue frontend/src/components/ui/MarkdownRichText.spec.ts
git commit -m "feat: add markdown rich text renderer"
```

### Task 2: 完善组件安全与高亮细节

**Files:**
- Modify: `frontend/src/components/ui/MarkdownRichText.vue`
- Modify: `frontend/src/components/ui/MarkdownRichText.spec.ts`

- [ ] **Step 1: 写失败测试（RED）**

```ts
it("sanitizes dangerous html", () => {
  const wrapper = mount(MarkdownRichText, {
    props: { content: '<img src=x onerror="alert(1)">' },
  });

  expect(wrapper.html()).not.toContain("onerror");
});

it("renders fenced code blocks", () => {
  const wrapper = mount(MarkdownRichText, {
    props: { content: '```ts\nconst answer = 42;\n```' },
  });

  expect(wrapper.find("pre code").exists()).toBe(true);
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- src/components/ui/MarkdownRichText.spec.ts -t "sanitizes|renders fenced"`
Expected: FAIL

- [ ] **Step 3: 实现安全白名单与链接增强**

```ts
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  if (node instanceof HTMLAnchorElement) {
    node.setAttribute("target", "_blank");
    node.setAttribute("rel", "noopener noreferrer nofollow");
  }
});
```

- [ ] **Step 4: 注册常见语言并处理 fallback**

```ts
hljs.registerLanguage("typescript", typescript);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("python", python);
hljs.registerLanguage("json", json);
hljs.registerLanguage("bash", bash);
```

- [ ] **Step 5: 测试通过并做小幅重构（REFACTOR）**

Run: `npm run test -- src/components/ui/MarkdownRichText.spec.ts`
Expected: PASS

- [ ] **Step 6: 运行 lint/typecheck**

Run:
- `npm run lint`
- `npm run typecheck`

- [ ] **Step 7: 提交**

```bash
git add frontend/src/components/ui/MarkdownRichText.vue frontend/src/components/ui/MarkdownRichText.spec.ts
git commit -m "feat: harden markdown rendering security"
```

### Task 3: 增加 Markdown 专用样式

**Files:**
- Create: `frontend/src/styles/markdown.css`
- Modify: `frontend/src/main.ts`（或实际样式入口）

- [ ] **Step 1: 写失败测试（RED）**

以页面快照或 class 断言方式验证组件有稳定 class：

```ts
it("applies markdown container class", () => {
  const wrapper = mount(MarkdownRichText, {
    props: { content: "`code`" },
  });

  expect(wrapper.classes()).toContain("markdown-rich-text");
});
```

- [ ] **Step 2: 创建样式文件并引入**

```css
.markdown-rich-text pre {
  overflow-x: auto;
  border-radius: 12px;
}

.markdown-rich-text code {
  font-family: ui-monospace, SFMono-Regular, monospace;
}
```

- [ ] **Step 3: 补齐表格、列表、链接、移动端滚动样式**

```css
.markdown-rich-text table {
  display: block;
  overflow-x: auto;
}
```

- [ ] **Step 4: 运行相关测试和检查**

Run:
- `npm run test -- src/components/ui/MarkdownRichText.spec.ts`
- `npm run lint`
- `npm run typecheck`

- [ ] **Step 5: 提交**

```bash
git add frontend/src/styles/markdown.css frontend/src/main.ts
git commit -m "feat: add markdown content styles"
```

### Task 4: 接入 Review 页面

**Files:**
- Modify: `frontend/src/pages/DungeonScholarReviewPage.vue`
- Test: `frontend/src/pages/DungeonScholarReviewPage.spec.ts`

- [ ] **Step 1: 写失败测试（RED）**

```ts
it("renders markdown in question title and explanation", async () => {
  // mock createRun response with **bold** and ```ts block
  expect(wrapper.html()).toContain("<strong>");
  expect(wrapper.find("pre code").exists()).toBe(true);
});
```

- [ ] **Step 2: 替换题干、选项、解析渲染**

```vue
<MarkdownRichText :content="questionTitle" />
<MarkdownRichText :content="option.text" inline />
<MarkdownRichText :content="feedbackExplanation" />
```

- [ ] **Step 3: 确保交互保持不变**

检查：
- 选项点击仍使用原 button
- 解析展示条件不变
- 提交流程不变

- [ ] **Step 4: 运行测试**

Run: `npm run test -- src/pages/DungeonScholarReviewPage.spec.ts`
Expected: PASS

- [ ] **Step 5: 运行 lint/typecheck**

Run:
- `npm run lint`
- `npm run typecheck`

- [ ] **Step 6: 提交**

```bash
git add frontend/src/pages/DungeonScholarReviewPage.vue frontend/src/pages/DungeonScholarReviewPage.spec.ts
git commit -m "feat: render markdown in review mode"
```

### Task 5: 接入 Speed Survival 与 Endless Abyss 页面

**Files:**
- Modify: `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue`
- Modify: `frontend/src/pages/DungeonScholarEndlessAbyssPage.vue`

- [ ] **Step 1: 写失败测试或补现有页面测试（RED）**

```ts
it("renders markdown question text in speed mode", async () => {
  expect(wrapper.find(".markdown-rich-text").exists()).toBe(true);
});
```

- [ ] **Step 2: 替换题干与解析为统一组件**

```vue
<MarkdownRichText :content="questionText" />
<MarkdownRichText v-if="feedbackExplanation" :content="feedbackExplanation" />
```

- [ ] **Step 3: 验证判断题按钮与填空输入不受影响**

Run: 页面定向测试或已有交互测试

- [ ] **Step 4: 运行质量检查**

Run:
- `npm run lint`
- `npm run typecheck`
- `npm run test -- src/pages/DungeonScholarSpeedSurvivalPage.spec.ts src/pages/DungeonScholarEndlessAbyssPage.spec.ts`

- [ ] **Step 5: 提交**

```bash
git add frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue frontend/src/pages/DungeonScholarEndlessAbyssPage.vue
git commit -m "feat: render markdown in speed and endless modes"
```

### Task 6: 接入 Knowledge Draft 页面并保留 blank 交互

**Files:**
- Modify: `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue`
- Test: `frontend/src/pages/DungeonScholarKnowledgeDraftPage.spec.ts`

- [ ] **Step 1: 写失败测试（RED）**

```ts
it("renders markdown only for text segments while preserving blank slots", async () => {
  expect(wrapper.findAll(".drop-slot").length).toBeGreaterThan(0);
  expect(wrapper.find("strong").exists()).toBe(true);
});
```

- [ ] **Step 2: 仅替换 text segment 渲染，不动 blank button**

```vue
<MarkdownRichText
  v-if="segment.kind === 'text'"
  :content="segment.value"
  inline
/>
```

- [ ] **Step 3: 保证拖拽、点击、自动提交逻辑不变**

重点回归：
- blank slot 填充
- drag & drop
- wrong answer feedback

- [ ] **Step 4: 运行测试**

Run: `npm run test -- src/pages/DungeonScholarKnowledgeDraftPage.spec.ts`
Expected: PASS

- [ ] **Step 5: 运行 lint/typecheck**

Run:
- `npm run lint`
- `npm run typecheck`

- [ ] **Step 6: 提交**

```bash
git add frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue frontend/src/pages/DungeonScholarKnowledgeDraftPage.spec.ts
git commit -m "feat: render markdown in draft mode"
```

### Task 7: 端到端回归与构建验证

**Files:**
- Modify: 测试文件按实际需要补齐

- [ ] **Step 1: 运行组件与页面定向测试**

Run:
- `npm run test -- src/components/ui/MarkdownRichText.spec.ts`
- `npm run test -- src/pages/DungeonScholarReviewPage.spec.ts src/pages/DungeonScholarKnowledgeDraftPage.spec.ts`

- [ ] **Step 2: 运行完整前端质量检查**

Run:
- `npm run lint`
- `npm run typecheck`
- `npm run test`
- `npm run build`

- [ ] **Step 3: 手动验证设计文档中的样例内容**

验证：
- `**粗体**`
- `` `inline code` ``
- `~~~` 或 ``` fenced code block
- 表格
- 链接
- 恶意 HTML 被清洗

- [ ] **Step 4: 如需补修，最小范围修复后重跑命令**

- [ ] **Step 5: 提交**

```bash
git add frontend
git commit -m "test: verify markdown rendering across study modes"
```

---

## 依赖关系

- Task 1 是基础任务，后续任务全部依赖它。
- Task 2 依赖 Task 1。
- Task 3 依赖 Task 1。
- Task 4、Task 5、Task 6 依赖 Task 1-3。
- Task 7 依赖 Task 4-6。

## 风险提醒

- `KnowledgeDraft` 的题干由文本段和 blank slot 混排，是本次改造最容易引入视觉或交互回归的点。
- 若页面测试覆盖不足，至少保证 `Review` 和 `KnowledgeDraft` 有定向测试，因为它们分别覆盖“通用题面”和“复杂混排题面”。
- 若包体积超预期，优先减少 `highlight.js` 注册语言，而不是牺牲渲染安全。

## 执行命令参考

在 `D:\project\Xirang\frontend` 下执行：

```bash
npm install
npm run lint
npm run typecheck
npm run test -- src/components/ui/MarkdownRichText.spec.ts
npm run build
```
