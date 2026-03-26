import { shallowRef } from "vue";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
}

const toasts = shallowRef<ToastItem[]>([]);
let toastIdCounter = 0;

export function useToast() {
  const show = (message: string, type: ToastType = "info", duration = 4000) => {
    const id = `toast-${++toastIdCounter}`;
    const toast: ToastItem = { id, type, message };

    toasts.value = [...toasts.value, toast];

    if (duration > 0) {
      setTimeout(() => {
        dismiss(id);
      }, duration);
    }

    return id;
  };

  const dismiss = (id: string) => {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  };

  const success = (message: string, duration?: number) => show(message, "success", duration);
  const error = (message: string, duration?: number) => show(message, "error", duration);
  const warning = (message: string, duration?: number) => show(message, "warning", duration);
  const info = (message: string, duration?: number) => show(message, "info", duration);

  return {
    toasts,
    show,
    dismiss,
    success,
    error,
    warning,
    info,
  };
}
