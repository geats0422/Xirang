<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { clearAuthSessionStorage, deleteAccount, logoutApi } from "../../api/auth";
import { clearGameData } from "../../api/settings";
import { ROUTES } from "../../constants/routes";
import { useRouteNavigation } from "../../composables/useRouteNavigation";
import DangerConfirmModal from "./DangerConfirmModal.vue";

const { t } = useI18n();
const { navigateTo } = useRouteNavigation();

type DangerAction = "clearData" | "deleteAccount" | "logout" | null;

const activeAction = ref<DangerAction>(null);
const processing = ref(false);

const dialogConfig: Record<
  Exclude<DangerAction, null>,
  { heading: () => string; message: () => string; confirmLabel: () => string; tone: "danger" | "warning" | "default" }
> = {
  clearData: {
    heading: () => t("settings.danger.resetConfirmTitle"),
    message: () => t("settings.danger.resetConfirmMessage"),
    confirmLabel: () => t("settings.danger.resetButton"),
    tone: "warning",
  },
  deleteAccount: {
    heading: () => t("settings.danger.deleteConfirmTitle"),
    message: () => t("settings.danger.deleteConfirmMessage"),
    confirmLabel: () => t("settings.danger.deleteAccountButton"),
    tone: "danger",
  },
  logout: {
    heading: () => t("settings.danger.logoutConfirmTitle"),
    message: () => t("settings.danger.logoutConfirmMessage"),
    confirmLabel: () => t("settings.danger.logoutButton"),
    tone: "default",
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
