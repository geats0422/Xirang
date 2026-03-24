<script setup lang="ts">
import { onMounted } from "vue";
import AppSidebar from "../components/layout/AppSidebar.vue";
import SettingsDangerPanel from "../components/settings/SettingsDangerPanel.vue";
import SettingsForgePanel from "../components/settings/SettingsForgePanel.vue";
import SettingsPreferencePanel from "../components/settings/SettingsPreferencePanel.vue";
import SettingsProfileHero from "../components/settings/SettingsProfileHero.vue";
import SettingsSupportPanel from "../components/settings/SettingsSupportPanel.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";

type PreferenceRow = {
  icon: string;
  title: string;
  description: string;
  kind: "theme" | "select" | "toggle";
  value?: string;
  enabled?: boolean;
};

onMounted(() => {
  document.title = "Xi Rang Settings";
});

const profileRoute = ROUTES.profile;
const { currentPath, navigateTo, routingTarget } = useRouteNavigation();

const preferenceRows: PreferenceRow[] = [
  {
    icon: "◐",
    title: "Interface Theme",
    description: "Choose your preferred visual style",
    kind: "theme",
  },
  {
    icon: "文",
    title: "Language",
    description: "Select interface language",
    kind: "select",
    value: "English",
  },
  {
    icon: "🔊",
    title: "Sound Effects",
    description: "Menu clicks and interaction sounds",
    kind: "toggle",
    enabled: true,
  },
  {
    icon: "📳",
    title: "Haptic Feedback",
    description: "Vibrate on successful quest completion",
    kind: "toggle",
    enabled: true,
  },
  {
    icon: "⏰",
    title: "Daily Reminders",
    description: "Receive scroll notifications at dawn",
    kind: "toggle",
    enabled: false,
  },
];
</script>

<template>
  <div class="settings-page">
    <AppSidebar :current-path="currentPath" :routing-target="routingTarget" @navigate="navigateTo" />

    <main class="settings-main">
      <div class="settings-content">
        <header class="page-header">
          <h1>Settings</h1>
          <p>Manage your profile, game preferences, and ancient technologies.</p>
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
  background: linear-gradient(180deg, #f7f9f8 0%, #f1f5f4 100%);
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
  color: #24323d;
  font-family: var(--font-serif);
  font-size: 40px;
  line-height: 1.1;
  margin: 0;
}

.page-header p {
  color: #91a0a5;
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
