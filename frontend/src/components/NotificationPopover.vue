<script setup lang="ts">
import { useI18n } from "vue-i18n";

export type NotificationItem = {
  id: string;
  title: string;
  time: string;
};

defineProps<{
  items: NotificationItem[];
  visible: boolean;
}>();

const emit = defineEmits<{
  close: [];
  itemClick: [item: NotificationItem];
  markAllRead: [];
}>();

const { t } = useI18n();
</script>

<template>
  <div v-if="visible" class="notice-overlay" @click="emit('close')">
    <section class="notice-card" @click.stop>
      <header class="notice-card__head">
        <h3>{{ t("notifications.popover.title") }}</h3>
        <button v-if="items.length > 0" class="mark-all-btn" type="button" @click="emit('markAllRead')">
          {{ t("notifications.popover.markAllRead") }}
        </button>
      </header>
      <div v-if="items.length === 0" class="notice-empty">{{ t("notifications.popover.empty") }}</div>
      <ul v-else class="notice-list">
        <li
          v-for="item in items"
          :key="item.id"
          class="notice-item"
          role="button"
          tabindex="0"
          @click="emit('itemClick', item)"
          @keydown.enter="emit('itemClick', item)"
        >
          <strong>{{ item.title }}</strong>
          <span>{{ item.time }}</span>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.notice-overlay {
  align-items: flex-start;
  display: flex;
  justify-content: flex-end;
  inset: 0;
  padding: 56px 24px 0;
  position: fixed;
  z-index: 90;
}

.notice-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.16);
  min-width: 280px;
  max-width: 360px;
  padding: 12px;
}

.notice-card__head {
  align-items: center;
  display: flex;
  justify-content: space-between;
  padding: 0 4px;
}

.notice-card__head h3 {
  color: var(--color-text-primary);
  font-size: 18px;
  margin: 0;
}

.mark-all-btn {
  background: transparent;
  border: 0;
  color: var(--color-primary-500);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 8px;
}

.mark-all-btn:hover {
  text-decoration: underline;
}

.notice-empty {
  color: var(--color-text-secondary);
  font-size: 13px;
  padding: 12px 8px 6px;
  text-align: center;
}

.notice-list {
  display: grid;
  gap: 8px;
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
}

.notice-item {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border-soft);
  border-radius: 10px;
  cursor: pointer;
  padding: 10px;
}

.notice-item:hover {
  background: var(--color-surface-hover);
}

.notice-item:focus {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

.notice-item strong {
  color: var(--color-text-primary);
  display: block;
  font-size: 13px;
}

.notice-item span {
  color: var(--color-text-muted);
  font-size: 12px;
}
</style>
