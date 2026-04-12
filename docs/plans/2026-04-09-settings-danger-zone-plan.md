# Settings 危险区域功能实现计划

**目标：** 实现 Settings 页面危险区域三个操作（清空游戏数据、删除账号、退出登录）的后端 API 与前端确认弹窗交互，确保操作需二次确认且与数据库联通。

**架构概述：** 后端在现有 `auth` 和 `settings` API 路由下新增 `DELETE /api/v1/auth/me`（删除账号）和 `POST /api/v1/settings/clear-game-data`（清空游戏数据）端点，利用现有 SQLAlchemy 模型的 `user_id` 外键关联与 `CASCADE` 删除策略。前端参考已有 `DocumentDeleteConfirmModal` 模式，创建通用 `DangerConfirmModal` 组件，改造 `SettingsDangerPanel` 集成弹窗与 API 调用。

**技术栈：** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL / Vue 3 + TypeScript + Vitest

---

## 需求分析

### 三个危险操作

| 操作 | 后端行为 | 前端行为 |
|------|----------|----------|
| **清空游戏数据** | 删除用户的 runs、settlements、mistakes、feedback、documents 等游戏数据；保留 users、auth_credentials、profiles、user_settings、wallets | 弹出确认弹窗 → 确认后调用 API → 刷新页面 |
| **删除账号** | 软删除用户（设置 `deleted_at`），级联删除所有关联数据（CASCADE） | 弹出确认弹窗 → 确认后调用 API → 清除本地存储 → 跳转登录页 |
| **退出登录** | 调用已有 `POST /api/v1/auth/logout`，撤销当前 session | 弹出确认弹窗 → 确认后调用 API → 清除本地存储 → 跳转登录页 |

### 数据库表与 user_id 关联分析

**清空游戏数据需删除的表（按依赖顺序）：**
1. `run_answers` (→ runs) — `ondelete="CASCADE"`
2. `run_questions` (→ runs) — `ondelete="CASCADE"`
3. `settlements` (→ users) — `ondelete="CASCADE"`
4. `runs` (→ users) — `ondelete="CASCADE"`
5. `mistake_embeddings` (→ mistakes) — `ondelete="CASCADE"`
6. `mistakes` (→ users) — `ondelete="CASCADE"`
7. `question_feedback` (→ users) — `ondelete="CASCADE"`
8. `active_effects` (→ users) — `ondelete="CASCADE"`
9. `use_records` (→ users) — `ondelete="CASCADE"`
10. `inventories` (→ users) — `ondelete="CASCADE"`
11. `purchase_records` (→ users) — `ondelete="CASCADE"`
12. `wallet_ledger` (→ users) — `ondelete="CASCADE"`
13. `leaderboard_snapshots` (→ users) — `ondelete="CASCADE"`
14. `document_question_sets` → `questions` → `question_options` (via documents)
15. `document_pageindex_trees` (via documents)
16. `document_ingestion_jobs` (via documents)
17. `documents` (→ users) — `ondelete="CASCADE"`

**保留的表：**
- `users` — 账号本体
- `auth_credentials` — 登录凭据
- `auth_sessions` — 当前会话
- `profiles` — 基本资料
- `user_settings` — 用户设置
- `wallets` — 钱包主表（余额清零，但保留记录）

---

## 依赖关系

```
[T1 后端: 删除账号 API] ──→ [T4 后端测试]
[T2 后端: 清空游戏数据 API] ──→ [T4 后端测试]
[T3 后端: logout 确认可用] ──→ [T5 前端 API 层]
                                      ↓
[T5 前端: API 调用函数] ──→ [T6 前端: DangerConfirmModal]
                                      ↓
[T6 前端: 确认弹窗组件] ──→ [T7 前端: SettingsDangerPanel 重构]
                                      ↓
[T7 + T8: i18n] ──→ [T9 前端测试]
                           ↓
                      [T10 质量验证]
```

---

## 任务清单

### Task 1: 后端 — AuthService 新增 delete_account 方法

**Files:**
- Modify: `backend/app/services/auth/service.py`
- Modify: `backend/app/repositories/auth_repository.py`

**说明：** 在 `AuthService` 中新增 `delete_account` 方法，执行软删除（设置 `User.deleted_at`）。由于所有关联表都有 `ondelete="CASCADE"` 或 `ondelete="SET NULL"`，数据库会自动处理级联删除。

- [ ] **Step 1: 在 AuthRepository 新增软删除方法**

在 `backend/app/repositories/auth_repository.py` 新增：

```python
async def soft_delete_user(self, *, user_id: UUID) -> User | None:
    user = await self.get_user_by_id(user_id)
    if user is None:
        return None
    user.deleted_at = datetime.now(UTC)
    user.status = UserStatus.DELETED
    await self._session.flush()
    return user

async def hard_delete_user_game_data(self, *, user_id: UUID) -> None:
    from sqlalchemy import delete as sql_delete
    from app.db.models.runs import Run, RunAnswer, RunQuestion, Settlement
    from app.db.models.economy import (
        WalletLedger, Inventory, PurchaseRecord, LeaderboardSnapshot,
        ActiveEffect, UseRecord,
    )
    from app.db.models.review import Mistake, MistakeEmbedding, QuestionFeedback
    from app.db.models.documents import Document
    tables_to_delete = [
        (RunAnswer, RunAnswer.user_id == user_id),
        (RunQuestion, RunQuestion.run_id.in_(
            select(Run.id).where(Run.user_id == user_id)
        )),
        (Settlement, Settlement.user_id == user_id),
        (Run, Run.user_id == user_id),
        (MistakeEmbedding, MistakeEmbedding.mistake_id.in_(
            select(Mistake.id).where(Mistake.user_id == user_id)
        )),
        (Mistake, Mistake.user_id == user_id),
        (QuestionFeedback, QuestionFeedback.user_id == user_id),
        (ActiveEffect, ActiveEffect.user_id == user_id),
        (UseRecord, UseRecord.user_id == user_id),
        (Inventory, Inventory.user_id == user_id),
        (PurchaseRecord, PurchaseRecord.user_id == user_id),
        (WalletLedger, WalletLedger.user_id == user_id),
        (LeaderboardSnapshot, LeaderboardSnapshot.user_id == user_id),
        (Document, Document.owner_user_id == user_id),
    ]
    for model, condition in tables_to_delete:
        await self._session.execute(sql_delete(model).where(condition))
    await self._session.flush()
```

- [ ] **Step 2: 在 AuthService 新增 delete_account 和 clear_game_data 方法**

```python
async def delete_account(self, *, user_id: UUID) -> None:
    user = await self.repository.get_user_by_id(user_id)
    if not user:
        raise InvalidTokenError("User not found")
    await self.repository.soft_delete_user(user_id=user_id)
    await self.repository.commit()

async def clear_game_data(self, *, user_id: UUID) -> None:
    user = await self.repository.get_user_by_id(user_id)
    if not user:
        raise InvalidTokenError("User not found")
    await self.repository.hard_delete_user_game_data(user_id=user_id)
    await self.repository.commit()
```

- [ ] **Step 3: 在 AuthRepositoryProtocol 中新增协议方法**

在 `backend/app/services/auth/service.py` 的 `AuthRepositoryProtocol` 中新增：

```python
async def soft_delete_user(self, *, user_id: UUID) -> Any | None: ...
async def hard_delete_user_game_data(self, *, user_id: UUID) -> None: ...
```

- [ ] **Step 4: 运行 ruff check + mypy**

Run: `cd backend && uv run ruff check app && uv run mypy app`

---

### Task 2: 后端 — 新增 DELETE /api/v1/auth/me 和 POST /api/v1/settings/clear-game-data 端点

**Files:**
- Modify: `backend/app/api/v1/auth.py` — 新增 DELETE /me
- Modify: `backend/app/api/v1/settings.py` — 新增 POST /clear-game-data

- [ ] **Step 1: 在 auth.py 新增 delete_account 端点**

在 `backend/app/api/v1/auth.py` 的 `get_me` 端点后新增：

```python
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    authorization: Annotated[str | None, Header()] = None,
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> Response:
    started_at = time.perf_counter()
    token = parse_bearer_token(authorization)
    try:
        payload = service.token_service.decode_token(token, expected_token_type="access")
        await service.delete_account(user_id=payload.user_id)
        log_auth_event(
            endpoint="/api/v1/auth/me",
            status_code=status.HTTP_204_NO_CONTENT,
            started_at=started_at,
            request_id=x_request_id,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except InvalidTokenError as e:
        log_auth_event(
            endpoint="/api/v1/auth/me",
            status_code=status.HTTP_401_UNAUTHORIZED,
            started_at=started_at,
            request_id=x_request_id,
            failure_reason="invalid_token",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
```

- [ ] **Step 2: 在 settings.py 新增 clear_game_data 端点**

在 `backend/app/api/v1/settings.py` 新增：

```python
from app.repositories.auth_repository import AuthRepository
from app.services.auth.service import AuthService
from app.services.auth.passwords import PasswordService
from app.services.auth.tokens import TokenService


async def get_account_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    settings = get_settings()
    token_service = TokenService(
        secret_key=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
        algorithm=settings.jwt_algorithm,
    )
    return AuthService(
        repository=AuthRepository(session),
        password_service=PasswordService(),
        token_service=token_service,
    )


@router.post("/clear-game-data", status_code=status.HTTP_204_NO_CONTENT)
async def clear_game_data(
    user_id: UUID = Depends(get_current_user_id),
    service: AuthService = Depends(get_account_service),
) -> Response:
    await service.clear_game_data(user_id=user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 3: 运行 ruff check + mypy**

Run: `cd backend && uv run ruff check app && uv run mypy app`

---

### Task 3: 后端 — 验证现有 logout 端点可用

**Files:** 无修改，仅验证

- [ ] **Step 1: 确认 `POST /api/v1/auth/logout` 已存在且接收 Bearer token**

已有实现：`backend/app/api/v1/auth.py:196-212`，接收 `Authorization` header，调用 `service.logout(access_token=token)`。

- [ ] **Step 2: 确认前端已能正确调用 logout**

前端 `auth.ts` 中无 `logout` API 函数，需在 Task 5 新增。

---

### Task 4: 后端 — 编写 API 测试

**Files:**
- Create: `backend/tests/api/test_danger_zone_api.py`

- [ ] **Step 1: 编写测试**

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def authenticated_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "dangeruser",
            "email": "danger@test.com",
            "password": "StrongPass123!",
        },
    )
    assert response.status_code == 201
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_clear_game_data_returns_204(client: TestClient, authenticated_headers):
    response = client.post("/api/v1/settings/clear-game-data", headers=authenticated_headers)
    assert response.status_code == 204


def test_clear_game_data_requires_auth(client: TestClient):
    response = client.post("/api/v1/settings/clear-game-data")
    assert response.status_code == 401


def test_delete_account_returns_204(client: TestClient, authenticated_headers):
    response = client.delete("/api/v1/auth/me", headers=authenticated_headers)
    assert response.status_code == 204


def test_delete_account_requires_auth(client: TestClient):
    response = client.delete("/api/v1/auth/me")
    assert response.status_code == 401
```

- [ ] **Step 2: 运行测试**

Run: `cd backend && uv run pytest tests/api/test_danger_zone_api.py -v`

---

### Task 5: 前端 — 新增 API 调用函数

**Files:**
- Modify: `frontend/src/api/auth.ts` — 新增 `logoutApi`、`deleteAccount`
- Modify: `frontend/src/api/settings.ts` — 新增 `clearGameData`

- [ ] **Step 1: 在 auth.ts 新增 logoutApi 和 deleteAccount**

```typescript
export const logoutApi = async (): Promise<void> => {
  return apiRequest<void>("/api/v1/auth/logout", {
    method: "POST",
    headers: getAuthHeaders(),
  });
};

export const deleteAccount = async (): Promise<void> => {
  return apiRequest<void>("/api/v1/auth/me", {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
};
```

- [ ] **Step 2: 在 settings.ts 新增 clearGameData**

```typescript
export const clearGameData = async (): Promise<void> => {
  return apiRequest<void>("/api/v1/settings/clear-game-data", {
    method: "POST",
    headers: getAuthHeaders(),
  });
};
```

- [ ] **Step 3: 运行 typecheck**

Run: `cd frontend && npx vue-tsc --noEmit`

---

### Task 6: 前端 — 创建 DangerConfirmModal 通用确认弹窗组件

**Files:**
- Create: `frontend/src/components/settings/DangerConfirmModal.vue`

**说明：** 参考现有 `DocumentDeleteConfirmModal.vue` 的模式，创建一个通用的危险操作确认弹窗。

- [ ] **Step 1: 创建 DangerConfirmModal.vue**

```vue
<script setup lang="ts">
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const props = withDefaults(
  defineProps<{
    visible: boolean;
    heading?: string;
    message?: string;
    confirmLabel?: string;
    processing?: boolean;
    tone?: "danger" | "warning" | "default";
  }>(),
  {
    heading: "",
    message: "",
    confirmLabel: "",
    processing: false,
    tone: "danger",
  },
);

const emit = defineEmits<{
  (e: "confirm"): void;
  (e: "cancel"): void;
}>();

const onConfirm = () => {
  if (props.processing) return;
  emit("confirm");
};

const onCancel = () => {
  if (props.processing) return;
  emit("cancel");
};
</script>

<template>
  <div v-if="props.visible" class="danger-confirm-overlay" @click.self="onCancel">
    <section
      class="danger-confirm"
      role="dialog"
      aria-modal="true"
      :aria-label="props.heading"
    >
      <button
        class="danger-confirm__close"
        type="button"
        :aria-label="t('common.closeAria')"
        :disabled="props.processing"
        @click="onCancel"
      >
        ✕
      </button>
      <h3>{{ props.heading }}</h3>
      <p>{{ props.message }}</p>
      <div class="danger-confirm__actions">
        <button
          class="danger-confirm__btn danger-confirm__btn--cancel"
          type="button"
          :disabled="props.processing"
          @click="onCancel"
        >
          {{ t("settings.danger.cancelButton") }}
        </button>
        <button
          class="danger-confirm__btn"
          :class="`danger-confirm__btn--${props.tone}`"
          type="button"
          :disabled="props.processing"
          @click="onConfirm"
        >
          {{ props.processing ? t("settings.danger.processing") : props.confirmLabel }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.danger-confirm-overlay {
  align-items: center;
  background: rgba(15, 23, 42, 0.28);
  display: flex;
  inset: 0;
  justify-content: center;
  padding: 24px;
  position: fixed;
  z-index: 1200;
}

.danger-confirm {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-danger-border, #e9c8c0);
  border-radius: 14px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.18);
  max-width: 420px;
  padding: 22px;
  position: relative;
  width: 100%;
}

.danger-confirm h3 {
  color: var(--color-danger-title, #8f3a32);
  font-size: 22px;
  margin: 0;
}

.danger-confirm p {
  color: var(--color-text-muted, #475569);
  font-size: 14px;
  line-height: 1.5;
  margin: 10px 0 0;
}

.danger-confirm__close {
  background: transparent;
  border: 0;
  color: var(--color-text-secondary, #64748b);
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  position: absolute;
  right: 10px;
  top: 10px;
}

.danger-confirm__close:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.danger-confirm__actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 18px;
}

.danger-confirm__btn {
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  min-width: 86px;
  padding: 9px 12px;
}

.danger-confirm__btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.danger-confirm__btn--cancel {
  background: var(--color-surface, #f8fafc);
  border-color: var(--color-border, #cbd5e1);
  color: var(--color-text-secondary, #475569);
}

.danger-confirm__btn--danger {
  background: var(--color-danger-solid-bg, #ef4444);
  color: var(--color-surface, #fff);
}

.danger-confirm__btn--warning {
  background: var(--color-danger-solid-bg, #ef4444);
  color: var(--color-surface, #fff);
}

.danger-confirm__btn--default {
  background: var(--color-surface, #f8fafc);
  border-color: var(--color-border, #cbd5e1);
  color: var(--color-text-secondary, #475569);
}
</style>
```

- [ ] **Step 2: 运行 lint + typecheck**

Run: `cd frontend && npm run lint && npm run typecheck`

---

### Task 7: 前端 — 重构 SettingsDangerPanel 集成弹窗和 API 调用

**Files:**
- Modify: `frontend/src/components/settings/SettingsDangerPanel.vue`

**说明：** 为三个按钮添加点击处理，弹出对应的确认弹窗，确认后调用 API。

- [ ] **Step 1: 重构 SettingsDangerPanel.vue**

```vue
<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { deleteAccount, clearAuthSessionStorage, logoutApi } from "../api/auth";
import { clearGameData } from "../api/settings";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import DangerConfirmModal from "./DangerConfirmModal.vue";

const { t } = useI18n();
const { navigateTo } = useRouteNavigation();

type DangerAction = "clearData" | "deleteAccount" | "logout" | null;

const activeAction = ref<DangerAction>(null);
const processing = ref(false);

const dialogConfig = {
  clearData: {
    heading: () => t("settings.danger.resetConfirmTitle"),
    message: () => t("settings.danger.resetConfirmMessage"),
    confirmLabel: () => t("settings.danger.resetButton"),
    tone: "warning" as const,
  },
  deleteAccount: {
    heading: () => t("settings.danger.deleteConfirmTitle"),
    message: () => t("settings.danger.deleteConfirmMessage"),
    confirmLabel: () => t("settings.danger.deleteAccountButton"),
    tone: "danger" as const,
  },
  logout: {
    heading: () => t("settings.danger.logoutConfirmTitle"),
    message: () => t("settings.danger.logoutConfirmMessage"),
    confirmLabel: () => t("settings.danger.logoutButton"),
    tone: "default" as const,
  },
};

const currentDialog = () => {
  if (!activeAction.value) return null;
  return dialogConfig[activeAction.value];
};

const openDialog = (action: DangerAction) => {
  activeAction.value = action;
};

const closeDialog = () => {
  if (processing.value) return;
  activeAction.value = null;
};

const onConfirm = async () => {
  processing.value = true;
  try {
    switch (activeAction.value) {
      case "clearData":
        await clearGameData();
        activeAction.value = null;
        break;
      case "deleteAccount":
        await deleteAccount();
        clearAuthSessionStorage();
        await navigateTo(ROUTES.login);
        break;
      case "logout":
        await logoutApi();
        clearAuthSessionStorage();
        await navigateTo(ROUTES.login);
        break;
    }
  } finally {
    processing.value = false;
    activeAction.value = null;
  }
};
</script>

<template>
  <section class="danger-panel">
    <div class="danger-panel__head">⚠ {{ t("settings.danger.title") }}</div>

    <div class="danger-row">
      <div>
        <p class="danger-row__title">{{ t("settings.danger.resetTitle") }}</p>
        <p class="danger-row__desc">{{ t("settings.danger.resetDesc") }}</p>
      </div>
      <button class="danger-btn danger-btn--ghost" type="button" @click="openDialog('clearData')">
        {{ t("settings.danger.resetButton") }}
      </button>
    </div>

    <div class="danger-row">
      <div>
        <p class="danger-row__title">{{ t("settings.danger.deleteAccountTitle") }}</p>
        <p class="danger-row__desc">{{ t("settings.danger.deleteAccountDesc") }}</p>
      </div>
      <button class="danger-btn danger-btn--solid" type="button" @click="openDialog('deleteAccount')">
        {{ t("settings.danger.deleteAccountButton") }}
      </button>
    </div>

    <div class="danger-row">
      <div>
        <p class="danger-row__title">{{ t("settings.danger.logoutTitle") }}</p>
        <p class="danger-row__desc">{{ t("settings.danger.logoutDesc") }}</p>
      </div>
      <button class="danger-btn danger-btn--logout" type="button" @click="openDialog('logout')">
        ↪ {{ t("settings.danger.logoutButton") }}
      </button>
    </div>

    <DangerConfirmModal
      v-if="currentDialog()"
      :visible="!!activeAction"
      :heading="currentDialog()!.heading()"
      :message="currentDialog()!.message()"
      :confirm-label="currentDialog()!.confirmLabel()"
      :processing="processing"
      :tone="currentDialog()!.tone"
      @confirm="onConfirm"
      @cancel="closeDialog"
    />
  </section>
</template>

<style scoped>
/* 保留原有样式不变 */
.danger-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-danger-border);
  border-radius: 8px;
  margin-top: 16px;
  overflow: hidden;
}

.danger-panel__head {
  background: var(--color-danger-surface);
  border-bottom: 1px solid var(--color-danger-border);
  color: var(--color-danger-title);
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  padding: 10px 14px;
}

.danger-row {
  align-items: center;
  border-bottom: 1px solid var(--color-danger-divider);
  display: flex;
  justify-content: space-between;
  padding: 12px 14px;
}

.danger-row:last-child {
  border-bottom: 0;
}

.danger-row__title {
  color: var(--color-text-dark);
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.danger-row__desc {
  color: var(--color-text-muted);
  font-size: 12px;
  margin: 2px 0 0;
}

.danger-btn {
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  height: 32px;
  padding: 0 12px;
}

.danger-btn--ghost {
  background: var(--color-surface);
  border: 1px solid var(--color-danger-border);
  color: var(--color-danger-title);
}

.danger-btn--solid {
  background: var(--color-danger-solid-bg);
  border: 1px solid var(--color-danger-solid-bg);
  color: var(--color-surface);
}

.danger-btn--logout {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

@media (max-width: 768px) {
  .danger-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}
</style>
```

- [ ] **Step 2: 运行 lint + typecheck**

Run: `cd frontend && npm run lint && npm run typecheck`

---

### Task 8: 前端 — 补充 i18n 确认弹窗文案

**Files:**
- Modify: `frontend/src/i18n/index.ts`

- [ ] **Step 1: 在 `settings.danger` 下新增确认弹窗相关文案**

在 `en.settings.danger` 中新增：

```typescript
cancelButton: "Cancel",
processing: "Processing...",
resetConfirmTitle: "Clear All Game Data?",
resetConfirmMessage: "This will reset your quest progress, runs, scores, and documents. Your account and settings will be kept. This cannot be undone.",
deleteConfirmTitle: "Delete Your Account?",
deleteConfirmMessage: "This will permanently remove your profile, achievements, and all data. This action is irreversible.",
logoutConfirmTitle: "Log Out?",
logoutConfirmMessage: "You will be signed out and redirected to the login page.",
```

在 `zh-CN.settings.danger` 中新增：

```typescript
cancelButton: "取消",
processing: "处理中...",
resetConfirmTitle: "确认清空全部游戏数据？",
resetConfirmMessage: "将重置你的任务进度、答题记录、分数和文档。账号信息和设置将被保留。此操作不可撤销。",
deleteConfirmTitle: "确认删除账号？",
deleteConfirmMessage: "将永久移除你的资料、成就及全部数据，且无法撤销。",
logoutConfirmTitle: "确认退出登录？",
logoutConfirmMessage: "你将被登出并跳转至登录页面。",
```

- [ ] **Step 2: 运行 typecheck**

Run: `cd frontend && npx vue-tsc --noEmit`

---

### Task 9: 前端 — 编写测试

**Files:**
- Modify: `frontend/src/pages/DungeonScholarSettingsPage.spec.ts`

- [ ] **Step 1: 编写 SettingsDangerPanel 交互测试**

在测试文件中新增测试用例，覆盖：
- 点击"清空全部数据"按钮弹出确认弹窗
- 点击"取消"关闭弹窗
- 点击"确认"调用 API
- 点击"删除账号"按钮弹出确认弹窗
- 确认后跳转登录页
- 点击"退出登录"按钮弹出确认弹窗
- 确认后跳转登录页

Run: `cd frontend && npm run test -- src/pages/DungeonScholarSettingsPage.spec.ts`

---

### Task 10: 质量验证 — lint + typecheck + test

- [ ] **Step 1: 后端质量验证**

Run:
```bash
cd backend && uv run ruff check app tests && uv run mypy app && uv run pytest tests -q --tb=short
```

- [ ] **Step 2: 前端质量验证**

Run:
```bash
cd frontend && npm run lint && npm run typecheck && npm run test && npm run build
```

---

## 风险提示

1. **级联删除安全**：清空游戏数据使用显式 SQL DELETE（非 CASCADE），需确保删除顺序正确，避免外键约束冲突。
2. **软删除 vs 硬删除**：删除账号采用软删除（`deleted_at` + `status=deleted`），数据库 CASCADE 仅在硬删除时生效。如需真正删除数据，应改为 `session.delete(user)` + `await session.flush()`。
3. **并发安全**：用户在操作进行中再次点击按钮，需通过 `processing` 状态禁用按钮和弹窗操作。
4. **Logout API 返回类型**：现有 `POST /api/v1/auth/logout` 返回 `Response(status_code=204)`，前端 `apiRequest` 需处理空响应体（已支持：`parseResponseData` 返回 `null`）。
