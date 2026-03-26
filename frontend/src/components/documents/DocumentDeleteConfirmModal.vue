<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    visible: boolean;
    title?: string;
    heading?: string;
    message?: string;
    processing?: boolean;
  }>(),
  {
    title: "",
    heading: "Delete document?",
    message: "",
    processing: false,
  },
);

const emit = defineEmits<{
  (e: "confirm"): void;
  (e: "cancel"): void;
}>();

const onConfirm = () => {
  if (props.processing) {
    return;
  }
  emit("confirm");
};

const onCancel = () => {
  if (props.processing) {
    return;
  }
  emit("cancel");
};

const resolvedMessage = () => {
  if (props.message.trim().length > 0) {
    return props.message;
  }
  return `Are you sure you want to delete "${props.title}"?`;
};
</script>

<template>
  <div v-if="props.visible" class="delete-modal-overlay" @click.self="onCancel">
    <section class="delete-modal" role="dialog" aria-modal="true" aria-label="Delete document confirmation">
      <button class="delete-modal__close" type="button" aria-label="Close" :disabled="props.processing" @click="onCancel">✕</button>
      <h3>{{ props.heading }}</h3>
      <p>{{ resolvedMessage() }}</p>
      <div class="delete-modal__actions">
        <button class="delete-modal__btn delete-modal__btn--cancel" type="button" :disabled="props.processing" @click="onCancel">No</button>
        <button class="delete-modal__btn delete-modal__btn--confirm" type="button" :disabled="props.processing" @click="onConfirm">
          {{ props.processing ? "Deleting..." : "Yes" }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.delete-modal-overlay {
  align-items: center;
  background: rgba(15, 23, 42, 0.28);
  display: flex;
  inset: 0;
  justify-content: center;
  padding: 24px;
  position: fixed;
  z-index: 1200;
}

.delete-modal {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.18);
  max-width: 420px;
  padding: 22px;
  position: relative;
  width: 100%;
}

.delete-modal h3 {
  color: #0f172a;
  font-size: 22px;
  margin: 0;
}

.delete-modal p {
  color: #475569;
  font-size: 14px;
  line-height: 1.5;
  margin: 10px 0 0;
}

.delete-modal__close {
  background: transparent;
  border: 0;
  color: #64748b;
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  position: absolute;
  right: 10px;
  top: 10px;
}

.delete-modal__close:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.delete-modal__actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 18px;
}

.delete-modal__btn {
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  min-width: 86px;
  padding: 9px 12px;
}

.delete-modal__btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.delete-modal__btn--cancel {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #475569;
}

.delete-modal__btn--confirm {
  background: #ef4444;
  color: #fff;
}
</style>
