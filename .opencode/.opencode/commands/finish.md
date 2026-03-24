---
description: |
  当实现完成、测试通过时使用。
  指导完成开发工作，提供合并/PR/清理选项。
  先加载 finishing-a-development-branch skill。
agent: build
subtask: false
model: openai/gpt-5.4
---

# Finish Command - 完成开发分支

## 核心理念

**验证测试 → 呈现选项 → 执行选择 → 清理**

## 执行流程

### Phase 1: 验证测试

**在呈现选项之前，必须验证测试通过:**

```bash
npm test / cargo test / pytest / go test ./...
```

**如果测试失败:**
- 显示失败的测试
- 告知用户必须先修复测试
- **不能继续到选项阶段**

### Phase 2: 确定基础分支

自动检测当前分支的基础分支。

### Phase 3: 呈现选项

呈现 4 个选项:
1. 本地合并到基础分支
2. 推送并创建 Pull Request
3. 保持分支（稍后处理）
4. 放弃此工作

### Phase 4: 执行选择

根据用户选择执行相应操作。

---

## 输出格式示例

```
═══════════════════════════════════════════════════════════
                    分支完成
═══════════════════════════════════════════════════════════

✅ 测试验证: 通过 (12 tests, 0 failures)

📋 当前分支: feature-auth
📋 基础分支: main

═══════════════════════════════════════════════════════════

请选择一个选项:
1. 本地合并到 main
2. 推送并创建 PR
3. 保持分支
4. 放弃

输入选项编号，或 "cancel" 取消:
```

## 加载 skill

使用 finishing-a-development-branch skill 执行完整流程：

```
skill: finishing-a-development-branch
```
