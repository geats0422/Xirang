<script setup lang="ts">
import { useI18n } from "vue-i18n";

type NotificationItem = {
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
}>();

const { t } = useI18n();
</script>

<template>
  <div v-if="visible" class="notice-overlay" @click="emit('close')">
    <section class="notice-card" @click.stop>
      <header class="notice-card__head">
        <h3>{{ t("notifications.popover.title") }}</h3>
      </header>
      <div v-if="items.length === 0" class="notice-empty">{{ t("notifications.popover.empty") }}</div>
      <ul v-else class="notice-list">
        <li v-for="item in items" :key="item.id" class="notice-item">
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
  min-width: 240px;
  padding: 12px;
}

.notice-card__head h3 {
  color: var(--color-text-primary);
  font-size: 18px;
  margin: 0;
  text-align: center;
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
  padding: 10px;
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
