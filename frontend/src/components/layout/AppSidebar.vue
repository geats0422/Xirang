<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { ROUTES, type AppRoutePath } from "../../constants/routes";

const { t, locale } = useI18n();

// Force reactivity on locale change
const _ = locale.value;

// Nav items with i18n keys
const navItems = [
  { icon: "⌂", route: ROUTES.home, i18nKey: "sidebar.home" as const },
  { icon: "◫", route: ROUTES.library, i18nKey: "sidebar.library" as const },
  { icon: "✦", route: ROUTES.quests, i18nKey: "sidebar.quests" as const },
  { icon: "▤", route: ROUTES.leaderboard, i18nKey: "sidebar.leaderboard" as const },
];

const props = withDefaults(
  defineProps<{
    currentPath: string;
    routingTarget: string | null;
    profileLevel?: string | null;
    profileName?: string | null;
  }>(),
  {
    profileLevel: "",
    profileName: "",
  },
);

const emit = defineEmits<{
  navigate: [targetRoute: AppRoutePath];
}>();

const isActiveRoute = (targetRoute: string) => props.currentPath === targetRoute;

const onNavigate = (targetRoute: AppRoutePath) => {
  emit("navigate", targetRoute);
};

// Computed translated labels - force dependency on locale
const brandName = computed(() => {
  const _ = locale.value;
  return t("landing.brand");
});

const settingsLabel = computed(() => {
  const _ = locale.value;
  return t("sidebar.settings");
});

const navLabels = computed(() => {
  const _ = locale.value;
  return navItems.map((item) => t(item.i18nKey));
});

const displayProfileName = computed(() => props.profileName?.trim() || "");
const displayProfileLevel = computed(() => props.profileLevel?.trim() || "");
</script>

<template>
  <aside class="sidebar" :aria-label="t('sidebar.aria')">
    <div class="brand-block">
      <div class="brand-icon">
        <img class="brand-icon__image" src="/taotie-logo.svg" alt="" aria-hidden="true">
      </div>
      <p class="brand-name">{{ brandName }}</p>
    </div>

    <nav class="side-nav" :aria-label="t('sidebar.primaryNavAria')">
      <button
        v-for="(item, index) in navItems"
        :key="item.route"
        class="side-nav__item"
        :class="{
          'side-nav__item--active': isActiveRoute(item.route),
          'side-nav__item--routing': routingTarget === item.route,
        }"
        type="button"
        :aria-current="isActiveRoute(item.route) ? 'page' : undefined"
        @click="onNavigate(item.route)"
      >
        <span class="side-nav__icon">{{ item.icon }}</span>
        <span>{{ navLabels[index] }}</span>
      </button>
    </nav>

    <div class="sidebar-bottom">
      <button
        class="settings-item"
        :class="{
          'settings-item--active': isActiveRoute(ROUTES.settings),
          'settings-item--routing': routingTarget === ROUTES.settings,
        }"
        type="button"
        :aria-current="isActiveRoute(ROUTES.settings) ? 'page' : undefined"
        @click="onNavigate(ROUTES.settings)"
      >
        <span class="settings-item__icon" aria-hidden="true">⚙</span>
        <span>{{ settingsLabel }}</span>
      </button>

      <button
        class="profile-card"
        :class="{
          'profile-card--active': isActiveRoute(ROUTES.profile),
          'profile-card--routing': routingTarget === ROUTES.profile,
        }"
        type="button"
        :aria-current="isActiveRoute(ROUTES.profile) ? 'page' : undefined"
        :aria-label="t('sidebar.userProfileAria')"
        @click="onNavigate(ROUTES.profile)"
      >
        <div class="profile-avatar">🧙</div>
        <div>
          <p class="profile-name">{{ displayProfileName }}</p>
          <p class="profile-level">{{ displayProfileLevel }}</p>
        </div>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  background: var(--color-sidebar-bg);
  border: 1px solid var(--color-sidebar-border);
  border-radius: var(--radius-lg);
  color: var(--color-sidebar-text);
  display: flex;
  flex-direction: column;
   flex-shrink: 0;
   max-width: 256px;
  min-height: 0;
   min-width: 256px;
  padding: 20px 16px;
   width: 256px;
}

.brand-block {
  align-items: center;
  display: flex;
  gap: 12px;
}

.brand-icon {
  align-items: center;
  background: var(--color-sidebar-brand-icon-bg);
  border-radius: 10px;
  display: inline-flex;
  height: 38px;
  justify-content: center;
  overflow: hidden;
  width: 38px;
}

.brand-icon__image {
  display: block;
  height: 100%;
  width: 100%;
}

.brand-name {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.1;
  margin: 0;
}

.side-nav {
  display: grid;
  gap: 8px;
  margin-top: 26px;
}

.side-nav__item {
  align-items: center;
  background: transparent;
  border: 0;
  border-radius: 12px;
  color: var(--color-sidebar-nav-text);
  cursor: pointer;
  display: flex;
  font-size: 15px;
  font-weight: 600;
  gap: 10px;
  justify-content: flex-start;
  min-height: 42px;
  padding: 0 12px;
  text-align: left;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.side-nav__item:hover {
  background: var(--color-sidebar-nav-hover-bg);
  transform: translateX(2px);
}

.side-nav__item--active {
  background: var(--color-sidebar-nav-active-bg);
  color: var(--color-sidebar-nav-active-text);
}

.side-nav__item--routing {
  animation: sidebar-route-pulse 220ms ease;
}

.side-nav__icon {
  font-size: 15px;
  width: 18px;
}

.sidebar-bottom {
  display: grid;
  gap: 12px;
  margin-top: auto;
}

.settings-item {
  align-items: center;
  background: var(--color-sidebar-card-bg);
  border: 1px solid var(--color-sidebar-border);
  border-radius: 10px;
  color: var(--color-sidebar-card-text);
  cursor: pointer;
  display: inline-flex;
  font-size: 15px;
  font-weight: 600;
  gap: 10px;
  justify-content: flex-start;
  min-height: 58px;
  padding: 0 18px;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
  width: 100%;
}

.settings-item:hover {
  background: var(--color-sidebar-card-hover-bg);
  border-color: var(--color-sidebar-card-hover-border);
  transform: translateX(2px);
}

.settings-item--active {
  background: var(--color-sidebar-card-active-bg);
  border-color: var(--color-sidebar-card-active-border);
  color: var(--color-sidebar-card-active-text);
}

.settings-item--routing {
  animation: sidebar-route-pulse 220ms ease;
}

.settings-item__icon {
  display: inline-flex;
  font-size: 16px;
  line-height: 1;
}

.profile-card {
  align-items: center;
  background: var(--color-sidebar-profile-bg);
  border: 1px solid transparent;
  border-radius: 14px;
  color: inherit;
  cursor: pointer;
  display: flex;
  font-family: inherit;
  gap: 12px;
  padding: 12px;
  text-align: left;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  width: 100%;
}

.profile-card:hover {
  border-color: var(--color-sidebar-profile-hover-border);
  transform: translateX(2px);
}

.profile-card--active {
  border-color: var(--color-sidebar-profile-active-border);
  box-shadow: var(--shadow-sidebar-profile);
}

.profile-card--routing {
  animation: sidebar-route-pulse 220ms ease;
}

.profile-avatar {
  align-items: center;
  background: var(--color-sidebar-avatar-bg);
  border-radius: 10px;
  display: inline-flex;
  font-size: 22px;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.profile-name {
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.profile-level {
  color: var(--color-text-muted);
  font-size: 12px;
  margin: 2px 0 0;
}

@keyframes sidebar-route-pulse {
  0% {
    transform: scale(1);
  }

  45% {
    transform: scale(0.98);
  }

  100% {
    transform: scale(1);
  }
}

@media (max-width: 1080px) {
  .sidebar {
    min-height: auto;
  }
}
</style>
