<script setup lang="ts">
type Variant = "primary" | "ghost";
type Size = "sm" | "md";

withDefaults(
  defineProps<{
    variant?: Variant;
    size?: Size;
    fullWidth?: boolean;
  }>(),
  {
    variant: "primary",
    size: "md",
    fullWidth: false,
  }
);
</script>

<template>
  <button
    class="base-btn"
    :class="[
      `base-btn--${variant}`,
      `base-btn--${size}`,
      { 'base-btn--full': fullWidth },
    ]"
  >
    <slot />
  </button>
</template>

<style scoped>
.base-btn {
  align-items: center;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: inline-flex;
  font-family: var(--font-serif);
  font-weight: 700;
  gap: 8px;
  justify-content: center;
  line-height: 1.2;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.base-btn--sm {
  font-size: 14px;
  min-height: 40px;
  padding: 10px 24px;
}

.base-btn--md {
  font-size: 16px;
  min-height: 48px;
  padding: 12px 32px;
}

.base-btn--full {
  width: 100%;
}

.base-btn--primary {
  background: var(--color-primary-500);
  box-shadow: var(--shadow-button);
  color: var(--color-white);
}

.base-btn--primary:hover {
  background: var(--color-primary-600);
  transform: translateY(-1px);
}

.base-btn--ghost {
  background: rgba(255, 255, 255, 0.6);
  border-color: var(--color-border);
  color: var(--color-text-tertiary);
  font-weight: 600;
}

.base-btn--ghost:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: #c4c9d1;
}
</style>
