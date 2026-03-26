<script setup lang="ts">
import { useToast, type ToastType } from "../../composables/useToast";

const { toasts, dismiss } = useToast();

const iconMap: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  warning: "⚠",
  info: "ℹ",
};

const toastClass: Record<ToastType, string> = {
  success: "toast--success",
  error: "toast--error",
  warning: "toast--warning",
  info: "toast--info",
};
</script>

<template>
  <Teleport to="body">
    <div class="toast-container" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="toastClass[toast.type]"
          role="alert"
        >
          <span class="toast__icon" aria-hidden="true">{{ iconMap[toast.type] }}</span>
          <span class="toast__message">{{ toast.message }}</span>
          <button class="toast__close" type="button" aria-label="Dismiss" @click="dismiss(toast.id)">
            ✕
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  left: 50%;
  position: fixed;
  transform: translateX(-50%);
  width: min(420px, calc(100vw - 48px));
  z-index: 9999;
}

.toast {
  align-items: center;
  backdrop-filter: blur(8px);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  gap: 12px;
  padding: 14px 16px;
}

.toast--success {
  background: linear-gradient(135deg, rgba(22, 163, 74, 0.95), rgba(21, 128, 61, 0.9));
  color: #ffffff;
}

.toast--error {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.95), rgba(185, 28, 28, 0.9));
  color: #ffffff;
}

.toast--warning {
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.95), rgba(202, 138, 4, 0.9));
  color: #1a1a1a;
}

.toast--info {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.95), rgba(37, 99, 235, 0.9));
  color: #ffffff;
}

.toast__icon {
  font-size: 18px;
  flex-shrink: 0;
}

.toast__message {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
}

.toast__close {
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.8;
  padding: 4px;
  transition: opacity 0.15s;
}

.toast__close:hover {
  opacity: 1;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px);
}
</style>
