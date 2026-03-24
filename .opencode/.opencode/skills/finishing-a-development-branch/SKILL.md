---
name: finishing-a-development-branch
description: |
  当实现完成、所有测试通过时使用。
  指导完成开发工作，呈现结构化的合并/PR/清理选项。
  用于完成一个功能或修复后，如何处理分支。
compatibility: opencode
---

# Finishing a Development Branch - 完成开发分支

## 概述

当实现完成、测试通过后，指导完成开发工作的结构化选项。

## 核心原则

**验证测试 → 呈现选项 → 执行选择 → 清理**

## 流程步骤

### Step 1: 验证测试

**在呈现选项之前，验证测试通过:**

```bash
# 运行项目的测试套件
npm test / cargo test / pytest / go test ./...
```

**如果测试失败:**
```
测试失败 (<N> 个失败)。必须先修复：

[显示失败]

测试通过前不能继续合并/PR。
```

停止。不要继续到 Step 2。

**如果测试通过:** 继续到 Step 2。

### Step 2: 确定基础分支

```bash
# 尝试常见的基础分支
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

或询问: "这个分支从 main 分出 - 正确吗？"

### Step 3: 呈现选项

呈现这 4 个选项:

```
实现完成。你想怎么做？

1. 本地合并到 <base-branch>
2. 推送并创建 Pull Request
3. 保持分支（稍后处理）
4. 放弃此工作

选择哪个？
```

**不要添加解释** - 保持选项简洁。

### Step 4: 执行选择

#### 选项 1: 本地合并

```bash
# 切换到基础分支
git checkout <base-branch>

# 拉取最新
git pull

# 合并功能分支
git merge <feature-branch>

# 验证合并后的测试
<test command>

# 如果测试通过
git branch -d <feature-branch>
```

然后: 清理 worktree (Step 5)

#### 选项 2: 推送并创建 PR

```bash
# 推送分支
git push -u origin <feature-branch>

# 创建 PR
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 要点的变更内容>

## Test Plan
[测试计划描述]

## Notes
[任何相关备注]
EOF
)"
```

#### 选项 3: 保持分支

记录分支状态供用户稍后处理。

#### 选项 4: 放弃工作

```bash
# 确认放弃
git branch -D <feature-branch>

# 清理 worktree（如有）
git worktree remove <worktree-path>
```

### Step 5: 清理

- 删除已完成的工作分支
- 清理任何临时文件
- 更新相关文档（如需要）

## 注意事项

1. **必须验证测试通过**后才能呈现选项
2. **不要跳过任何步骤**
3. **用户选择后执行**，不要默认执行
4. **保持简洁**，不要添加额外解释

## 输出格式

```
═══════════════════════════════════════════════════════════
                    分支完成
═══════════════════════════════════════════════════════════

✅ 测试验证: 通过

📋 当前分支: feature-xxx
📋 基础分支: main

请选择一个选项:
1. 本地合并到 main
2. 推送并创建 PR
3. 保持分支
4. 放弃
```
