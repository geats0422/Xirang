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
