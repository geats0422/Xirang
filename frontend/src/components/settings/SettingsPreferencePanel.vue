<script setup lang="ts">
type PreferenceRow = {
  icon: string;
  title: string;
  description: string;
  kind: "theme" | "select" | "toggle";
  value?: string;
  enabled?: boolean;
};

defineProps<{
  rows: PreferenceRow[];
}>();
</script>

<template>
  <section class="panel">
    <div class="panel__header">
      <span class="panel__icon">☷</span>
      <h3>Game Preferences</h3>
    </div>

    <div class="prefs-list">
      <div v-for="row in rows" :key="row.title" class="prefs-row">
        <div class="prefs-row__left">
          <span class="prefs-row__icon">{{ row.icon }}</span>
          <div>
            <p class="prefs-row__title">{{ row.title }}</p>
            <p class="prefs-row__desc">{{ row.description }}</p>
          </div>
        </div>

        <div v-if="row.kind === 'theme'" class="segmented" role="group" aria-label="Theme">
          <button class="segmented__btn segmented__btn--active" type="button">Light</button>
          <button class="segmented__btn" type="button">Dark</button>
          <button class="segmented__btn" type="button">System</button>
        </div>

        <button v-else-if="row.kind === 'select'" class="select-btn" type="button">
          <span>{{ row.value }}</span>
          <span>▾</span>
        </button>

        <button v-else class="toggle" :class="{ 'toggle--on': row.enabled }" type="button">
          <span />
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: #ffffff;
  border: 1px solid #e6ece8;
  border-radius: 8px;
  margin-top: 16px;
  overflow: hidden;
}

.panel__header {
  align-items: center;
  border-bottom: 1px solid #edf1ee;
  display: flex;
  gap: 10px;
  padding: 14px 16px;
}

.panel__icon {
  color: #728a8d;
  font-size: 16px;
}

.panel__header h3 {
  color: #25333d;
  font-family: var(--font-serif);
  font-size: 24px;
  margin: 0;
}

.prefs-list {
  display: grid;
}

.prefs-row {
  align-items: center;
  border-bottom: 1px solid #edf1ee;
  display: flex;
  justify-content: space-between;
  padding: 14px 16px;
}

.prefs-row:last-child {
  border-bottom: 0;
}

.prefs-row__left {
  align-items: center;
  display: flex;
  gap: 14px;
}

.prefs-row__icon {
  align-items: center;
  background: #f0f5f2;
  border-radius: 999px;
  color: #5b7f81;
  display: inline-flex;
  font-size: 14px;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.prefs-row__title {
  color: #293741;
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.prefs-row__desc {
  color: #7f9198;
  font-size: 12px;
  margin: 2px 0 0;
}

.segmented {
  background: #f5f7f5;
  border: 1px solid #e2e8e4;
  border-radius: 8px;
  display: inline-flex;
  gap: 4px;
  padding: 4px;
}

.segmented__btn {
  background: transparent;
  border: 0;
  border-radius: 6px;
  color: #7f9198;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  height: 28px;
  min-width: 52px;
  padding: 0 10px;
}

.segmented__btn--active {
  background: #ffffff;
  border: 1px solid #d9e1dc;
  color: #344451;
}

.select-btn {
  align-items: center;
  background: #f9fbfa;
  border: 1px solid #dbe3de;
  border-radius: 8px;
  color: #3b4c57;
  cursor: pointer;
  display: inline-flex;
  font-size: 13px;
  font-weight: 600;
  gap: 12px;
  height: 38px;
  justify-content: space-between;
  min-width: 160px;
  padding: 0 12px;
}

.toggle {
  background: #d9dee2;
  border: 0;
  border-radius: 999px;
  cursor: pointer;
  height: 20px;
  padding: 2px;
  width: 36px;
}

.toggle span {
  background: #fff;
  border-radius: 999px;
  display: block;
  height: 16px;
  transition: transform 0.2s ease;
  width: 16px;
}

.toggle--on {
  background: #2a99a4;
}

.toggle--on span {
  transform: translateX(16px);
}

@media (max-width: 768px) {
  .prefs-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}
</style>
