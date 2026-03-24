---
name: planning
description: |
  根据已批准的设计规格生成详细的实现计划。
  当设计探索阶段完成并获得用户批准后，使用此技能生成实现计划。
  每个计划任务必须包含 TDD 步骤、测试步骤、提交步骤。
compatibility: opencode
---

# Planning - 实现计划生成

## 概述

根据已批准的设计规格文档，生成详细的实现计划。

**前提条件**: 设计规格文档必须已经用户批准。

## 核心原则

### 输入要求
- 设计规格文档路径 (docs/specs/*-design.md)
- 用户确认批准设计的证据

### 输出要求
- 实现计划文档 (docs/plans/*-plan.md)
- TodoWrite 任务清单

## 流程步骤

### Step 1: 验证设计规格

1. **读取设计规格文档**
   - 确认文档存在
   - 确认已获得用户批准

2. **检查规格完整性**
   - 是否包含背景与目标？
   - 是否包含技术方案？
   - 是否包含架构设计？
   - 是否包含接口设计？
   - 是否包含验收标准？

3. **如有问题**
   - 报告给用户
   - 等待用户补充/修正

### Step 2: 文件结构规划

1. **分析需要创建/修改的文件**
   - 新文件：创建什么
   - 修改文件：修改什么
   - 删除文件：删除什么

2. **每个文件明确职责**
   - 文件负责什么功能
   - 文件的输入输出是什么
   - 文件依赖哪些其他文件

3. **遵循项目现有模式**
   - 参考现有代码结构
   - 使用现有命名约定
   - 遵循现有测试模式

### Step 3: 任务分解

**原则**: 每个任务 2-5 分钟可完成

**任务结构**:
```markdown
### Task N: [组件名称]

**Files:**
- Create: `path/to/new-file.ts`
- Modify: `path/to/existing-file.ts:123-145`
- Test: `tests/path/to/test.ts`

- [ ] **Step 1: Write failing test (RED)**

```typescript
describe('functionName', () => {
  it('should do something', () => {
    expect(functionName(input)).toBe(expected);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --testPathPattern=test.ts`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```typescript
export function functionName(input: Type): ReturnType {
  return expected;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --testPathPattern=test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add files...
git commit -m "feat: add component name"
```

- [ ] **Step 6: Run linter/formatter**
```

### Step 4: 生成计划文档

**路径**: `docs/plans/YYYY-MM-DD-<feature>-plan.md`

**文档头部**:
```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Design Spec:** [path to design spec]

---
```

### Step 5: 计划审查循环

1. **内部审查**
   - 检查任务是否完整覆盖设计规格
   - 检查任务是否遵循 TDD 原则
   - 检查任务粒度是否合适（2-5分钟）

2. **如有问题**
   - 修复问题
   - 重新审查
   - 最多5轮

3. **生成 TodoWrite 任务清单**
   - 每个任务一个 todo
   - 包含任务编号和描述

## 输出要求

### 计划文档结构

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Use /execute command to implement tasks. Steps use checkbox syntax.

**Goal:** ...

**Architecture:** ...

**Tech Stack:** ...

---

## Task List

### Task 1: [Component Name]
...

### Task 2: [Component Name]
...

---

## Dependencies
- [List of dependencies between tasks]
```

### 用户输出

```
═══════════════════════════════════════════════════════════
                    计划生成 - 完成 ✅
═══════════════════════════════════════════════════════════

📄 计划文档: docs/plans/2026-03-13-auth-plan.md

📋 任务清单: N 个任务
   ├── 任务1: 实现 XXX
   ├── 任务2: 实现 YYY
   └── ...

═══════════════════════════════════════════════════════════

准备好执行计划了吗？
   /execute 1   → 执行任务1
   /execute all → 全部执行
   /modify      → 修改计划
```

## 关键原则

1. **TDD 强制**: 每个任务必须包含 RED→GREEN→REFACTOR 循环
2. **测试优先**: 先写测试，再写实现
3. **小步提交**: 每个任务包含提交步骤
4. **完整代码**: 计划中包含可直接使用的代码示例
5. **明确路径**: 所有文件路径必须精确
6. **DRY 原则**: 避免重复代码
7. **YAGNI 原则**: 不做过度设计
