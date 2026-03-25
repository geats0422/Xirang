<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useI18n } from "vue-i18n";
import AppSidebar from "../components/layout/AppSidebar.vue";
import SettingsDangerPanel from "../components/settings/SettingsDangerPanel.vue";
import SettingsForgePanel from "../components/settings/SettingsForgePanel.vue";
import SettingsPreferencePanel from "../components/settings/SettingsPreferencePanel.vue";
import SettingsProfileHero from "../components/settings/SettingsProfileHero.vue";
import SettingsSupportPanel from "../components/settings/SettingsSupportPanel.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";

const { t, locale } = useI18n();

type PreferenceRow = {
  icon: string;
  title: string;
  description: string;
  kind: "theme" | "select" | "toggle";
  value?: string;
  enabled?: boolean;
};

onMounted(() => {
  document.title = t("settings.title");
});

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("settings.title");
});

const profileRoute = ROUTES.profile;
const { currentPath, navigateTo, routingTarget } = useRouteNavigation();

// Use computed to make preferenceRows reactive to locale changes
const preferenceRows = computed<PreferenceRow[]>(() => [
  {
    icon: "◐",
    title: t("settings.preferences.themeLabel"),
    description: t("settings.preferences.themeDesc"),
    kind: "theme",
  },
  {
    icon: "文",
    title: t("settings.preferences.languageLabel"),
    description: t("settings.preferences.languageDesc"),
    kind: "select",
    value: "English",
  },
  {
    icon: "🔊",
    title: t("settings.preferences.soundLabel"),
    description: t("settings.preferences.soundDesc"),
    kind: "toggle",
    enabled: true,
  },
  {
    icon: "📳",
    title: t("settings.preferences.hapticLabel"),
    description: t("settings.preferences.hapticDesc"),
    kind: "toggle",
    enabled: true,
  },
  {
    icon: "⏰",
    title: t("settings.preferences.reminderLabel"),
    description: t("settings.preferences.reminderDesc"),
    kind: "toggle",
    enabled: false,
  },
]);
</script>

<template>
  <div class="settings-page">
    <AppSidebar :current-path="currentPath" :routing-target="routingTarget" @navigate="navigateTo" />

    <main class="settings-main">
      <div class="settings-content">
        <header class="page-header">
          <h1>{{ t("settings.title") }}</h1>
          <p>{{ t("settings.subtitle") }}</p>
        </header>

        <SettingsProfileHero @edit-profile="navigateTo(profileRoute)" />
        <SettingsPreferencePanel :rows="preferenceRows" />
        <SettingsForgePanel />
        <SettingsSupportPanel />
        <SettingsDangerPanel />
      </div>
    </main>
  </div>
</template>

<style scoped>
.settings-page {
  background: var(--color-page-bg);
  display: grid;
  gap: 24px;
  grid-template-columns: 256px minmax(0, 1fr);
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
  padding: 24px;
}

.settings-main {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 0;
  min-width: 0;
  overflow-y: auto;
}

.settings-content {
  margin: 0 auto;
  max-width: 1280px;
  width: 100%;
}

.page-header h1 {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 40px;
  line-height: 1.1;
  margin: 0;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: 13px;
  margin: 8px 0 0;
}

@media (max-width: 1200px) {
  .settings-content {
    max-width: 100%;
  }
}

@media (max-width: 1080px) {
  .settings-page {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .settings-page {
    height: 100vh;
    padding: 14px;
  }

  .settings-content {
    max-width: none;
  }
}
</style>
