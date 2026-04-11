<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";

const { t } = useI18n();
const router = useRouter();

const navigateTo = (path: string) => {
  router.push(path);
};
</script>

<template>
  <section class="panel">
    <div class="panel__header">
      <span class="panel__icon">⚒</span>
      <h3>{{ t("settings.support.title") }}</h3>
    </div>

    <div class="support-row">
      <div class="support-row__left">
        <span class="support-row__icon">💬</span>
        <div>
          <p class="support-row__title">{{ t("settings.support.subscription") }}</p>
          <p class="support-row__desc">{{ t("settings.support.subscriptionDesc") }}</p>
        </div>
      </div>
      <button class="plan-btn" type="button">{{ t("settings.support.manage") }}</button>
    </div>

    <div class="legal-links">
      <button type="button" @click="navigateTo('/settings/user-agreement')">
        {{ $t("settings.support.userAgreement") }}
      </button>
      <button type="button" @click="navigateTo('/privacy-policy')">
        {{ $t("settings.support.privacyPolicy") }}
      </button>
      <button type="button" @click="navigateTo('/settings/help-center')">
        {{ $t("settings.support.helpCenter") }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-top: 16px;
  overflow: hidden;
}

.panel__header {
  align-items: center;
  border-bottom: 1px solid var(--color-border-soft);
  display: flex;
  gap: 10px;
  padding: 14px 16px;
}

.panel__icon {
  color: var(--color-icon-text);
  font-size: 16px;
}

.panel__header h3 {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 24px;
  margin: 0;
}

.support-row {
  align-items: center;
  border-bottom: 1px solid var(--color-border-soft);
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
}

.support-row__left {
  align-items: center;
  display: flex;
  gap: 12px;
}

.support-row__icon {
  align-items: center;
  background: var(--color-icon-bg);
  border-radius: 6px;
  color: var(--color-icon-text);
  display: inline-flex;
  font-size: 15px;
  height: 26px;
  justify-content: center;
  width: 26px;
}

.support-row__title {
  color: var(--color-text-dark);
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.support-row__desc {
  color: var(--color-text-muted);
  font-size: 12px;
  margin: 2px 0 0;
}

.plan-btn {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: 6px;
  color: var(--color-primary-600);
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  height: 30px;
  padding: 0 12px;
}

.legal-links {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.legal-links button {
  background: var(--color-surface);
  border: 0;
  border-right: 1px solid var(--color-border-soft);
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 12px;
  height: 44px;
}

.legal-links button:last-child {
  border-right: 0;
}

@media (max-width: 768px) {
  .support-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .legal-links {
    grid-template-columns: 1fr;
  }

  .legal-links button {
    border-bottom: 1px solid var(--color-border-soft);
    border-right: 0;
    padding: 0 16px;
    text-align: left;
  }

  .legal-links button:last-child {
    border-bottom: 0;
  }
}
</style>
