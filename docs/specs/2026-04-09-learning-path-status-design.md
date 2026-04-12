# 学习路径状态管理设计规格

## 1. 背景与目标

### 问题描述
当前学习路径缺少状态管理，用户无法清晰了解每个关卡的学习状态（未学习、可学习、已完成），也无法按照线性顺序逐步解锁关卡。

### 目标
- 实现类似多邻国的学习路径状态管理
- 三种状态：禁止（locked）、可学习（unlocked）、已完成（completed）
- 线性进度：完成前一个关卡才能解锁下一个
- 混合存储：后端数据库 + 前端本地

## 2. 技术方案

### 方案选择
采用**扩展现有系统**的方案：
- 在 `runs` 表中增加 `path_id` 和 `stage_index` 字段
- 前端通过 API 获取路径进度并缓存到本地
- 新增 `LearningPathStageStatus` 枚举定义三种状态

### 优点
- 最小改动，复用现有 runs 服务
- 与现有 document -> question_set -> runs 流程一致
- 便于追踪每个 run 对应的路径和关卡

### 缺点
- runs 表字段需要扩展
- 需要处理历史数据迁移

## 3. 架构设计

### 状态定义

```typescript
enum StageStatus {
  LOCKED = "locked",       // 禁止状态 - 不可点击
  UNLOCKED = "unlocked",   // 可学习状态 - 可点击
  COMPLETED = "completed"   // 已完成状态 - 已学习
}
```

### 数据流

```
[文档上传] 
    ↓
[LLM + PageIndex 生成题库]
    ↓
[LLM 生成学习路径] → 存储到 document_question_sets 或新建表
    ↓
[用户开始学习] → 创建 run 并关联 path_id
    ↓
[完成关卡] → 更新 run 状态，next_stage 解锁
```

### 路径结构

- 每个 document 有 3 个模式的学习路径
- 每个模式有 N 个关卡（由 LLM 根据知识点数量生成）
- 关卡按顺序解锁：Stage 1 → Stage 2 → ... → Stage N

## 4. 接口设计

### 后端 API

#### GET /api/v1/learning-paths
获取用户的学习路径进度

Response:
```json
{
  "document_id": "uuid",
  "mode": "speed|draft|endless",
  "stages": [
    {
      "stage_index": 0,
      "stage_id": "R1",
      "status": "locked|unlocked|completed",
      "best_run_id": "uuid|null",
      "best_score": 0,
      "completed_at": "datetime|null"
    }
  ],
  "current_stage_index": 1,
  "completed_stages_count": 0,
  "total_stages_count": 3
}
```

#### POST /api/v1/learning-paths/generate
为文档生成学习路径（通常由 worker 自动调用）

Request:
```json
{
  "document_id": "uuid",
  "mode": "speed|draft|endless",
  "knowledge_points": ["知识点1", "知识点2", ...]
}
```

Response:
```json
{
  "path_id": "uuid",
  "stages": [
    {"stage_id": "R1", "label": "R1", "knowledge_points": ["知识点1"]},
    {"stage_id": "R2", "label": "R2", "knowledge_points": ["知识点2"]},
    ...
  ]
}
```

### 前端状态

```typescript
interface LearningPathStage {
  id: string;
  label: string;
  status: StageStatus;
  completedAt?: string;
  bestScore?: number;
}

interface LearningPathState {
  documentId: string;
  mode: RunMode;
  stages: LearningPathStage[];
  isLoading: boolean;
  error?: string;
}
```

## 5. 数据库模型

### 扩展 runs 表

```python
class Run(UUIDPrimaryKeyMixin, Base):
    # ... existing fields ...
    
    path_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="SET NULL"),
    )
    stage_index: Mapped[int | None] = mapped_column(Integer, default=0)
```

### 新建 learning_paths 表

```python
class LearningPath(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_paths"
    
    user_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("users.id"))
    document_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("documents.id"))
    mode: Mapped[RunMode] = mapped_column(String(20))  # speed, draft, endless
    
    # LLM 生成的路径结构 JSON
    path_structure: Mapped[dict] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now())

class LearningPathStage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_path_stages"
    
    path_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("learning_paths.id"))
    stage_index: Mapped[int] = mapped_column(Integer)
    stage_id: Mapped[str] = mapped_column(String(20))  # R1, R2, R3
    
    best_run_id: Mapped[UUID | None] = mapped_column(PGUUID)
    best_score: Mapped[int] = mapped_column(default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # 唯一约束
    __table_args__ = (UniqueConstraint("path_id", "stage_index"),)
```

## 6. UI 状态显示

### 视觉规范

| 状态 | 边框颜色 | 图标 | 动画 | 可点击 |
|------|---------|------|------|--------|
| LOCKED | `var(--color-border)` | 🔒 | 无 | 否 |
| UNLOCKED | `var(--color-primary-500)` | ▶️ | 脉冲动画 | 是 |
| COMPLETED | `var(--color-success)` | ✓ | 闪烁效果 | 是 |

### CSS 样式

```css
.path-node--locked {
  opacity: 0.5;
  cursor: not-allowed;
}

.path-node--unlocked {
  border-color: var(--color-primary-500);
  animation: pulse 2s infinite;
}

.path-node--completed {
  border-color: var(--color-success);
  animation: glow 1.5s ease-in-out infinite alternate;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--color-primary-rgb), 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(var(--color-primary-rgb), 0); }
}

@keyframes glow {
  from { box-shadow: 0 0 4px var(--color-success); }
  to { box-shadow: 0 0 12px var(--color-success); }
}
```

## 7. 前端组件修改

### DungeonScholarLevelPathPage.vue

需要修改：
1. `PathNode` 类型增加 `status` 字段
2. `mapOptionToNode` 函数从 API 获取状态
3. 节点点击逻辑判断状态
4. 样式类根据状态切换

```typescript
type PathNode = {
  id: string;
  label: string;
  type: "battle" | "study" | "checkpoint" | "boss" | "speed" | "draft" | "review";
  description: string;
  floor?: number;
  status: "locked" | "unlocked" | "completed";
};
```

### 新增 composable

```typescript
// useLearningPath.ts
export function useLearningPath(documentId: string, mode: RunMode) {
  const stages = ref<LearningPathStage[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  
  const fetchProgress = async () => {
    // 调用 GET /api/v1/learning-paths
  };
  
  const getStageStatus = (index: number): StageStatus => {
    if (index < currentStageIndex.value) return "completed";
    if (index === currentStageIndex.value) return "unlocked";
    return "locked";
  };
  
  return { stages, isLoading, error, fetchProgress, getStageStatus };
}
```

## 8. Worker 修改

在 `document_ingestion` worker 中增加生成学习路径的步骤：

```python
async def document_ingestion_flow(document_id: UUID, user_id: UUID):
    # ... 现有步骤 ...
    
    # Step 4: 生成学习路径
    if document.format != DocumentFormat.MARKDOWN:
        await generate_learning_path(document_id, user_id, mode="speed")
        await generate_learning_path(document_id, user_id, mode="draft")
        await generate_learning_path(document_id, user_id, mode="endless")
```

## 9. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 获取进度失败 | 显示静态 fallbackNodes，降级到本地状态 |
| 生成路径失败 | 重试 3 次，失败后标记文档状态为部分可用 |
| 关卡未解锁 | 点击时显示 toast 提示"请先完成上一关卡" |
| 网络离线 | 使用本地缓存，标记"未同步"状态 |

## 10. 风险与约束

### 风险
1. **LLM 生成不稳定** - 学习路径的结构和关卡数可能不一致
2. **迁移复杂性** - 需要为现有 runs 数据填充 path_id 和 stage_index
3. **并发问题** - 多个客户端同时学习可能状态不一致

### 约束
1. 学习路径在文档上传后自动生成，用户无法手动编辑
2. 每个文档的每个模式只有一条学习路径
3. 关卡顺序由 LLM 生成，无法手动调整

## 11. 验收标准

1. ✅ 用户上传文档后，系统自动生成 3 个模式的学习路径
2. ✅ 学习路径页面正确显示每个关卡的状态（locked/unlocked/completed）
3. ✅ 只有 unlocked 和 completed 状态的关卡可以点击
4. ✅ 完成一个关卡后，下一个关卡自动变为 unlocked
5. ✅ 刷新页面后状态从后端同步，不丢失进度
6. ✅ 离线时使用本地缓存，在线后同步到后端
7. ✅ UI 状态显示符合视觉规范（颜色+动画）
