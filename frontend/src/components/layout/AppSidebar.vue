<script setup lang="ts">
import { PRIMARY_NAV_ITEMS, ROUTES, type AppRoutePath } from "../../constants/routes";

const props = withDefaults(
  defineProps<{
    currentPath: string;
    routingTarget: string | null;
    profileLevel?: string;
    profileName?: string;
  }>(),
  {
    profileLevel: "Level 12 Scholar",
    profileName: "Default User",
  },
);

const emit = defineEmits<{
  navigate: [targetRoute: AppRoutePath];
}>();

const isActiveRoute = (targetRoute: string) => props.currentPath === targetRoute;

const onNavigate = (targetRoute: AppRoutePath) => {
  emit("navigate", targetRoute);
};
</script>

<template>
  <aside class="sidebar" aria-label="Sidebar">
    <div class="brand-block">
      <div class="brand-icon">
        <img class="brand-icon__image" src="/taotie-logo.svg" alt="" aria-hidden="true">
      </div>
      <p class="brand-name">XI Rang Scholar</p>
    </div>

    <nav class="side-nav" aria-label="Primary">
      <button
        v-for="item in PRIMARY_NAV_ITEMS"
        :key="item.label"
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
        <span>{{ item.label }}</span>
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
        <span>Settings</span>
      </button>

      <button
        class="profile-card"
        :class="{
          'profile-card--active': isActiveRoute(ROUTES.profile),
          'profile-card--routing': routingTarget === ROUTES.profile,
        }"
        type="button"
        :aria-current="isActiveRoute(ROUTES.profile) ? 'page' : undefined"
        aria-label="User profile"
        @click="onNavigate(ROUTES.profile)"
      >
        <div class="profile-avatar">🧙</div>
        <div>
          <p class="profile-name">{{ profileName }}</p>
          <p class="profile-level">{{ profileLevel }}</p>
        </div>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  background: var(--color-surface);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 20px 16px;
}

.brand-block {
  align-items: center;
  display: flex;
  gap: 12px;
}

.brand-icon {
  align-items: center;
  background: rgba(16, 139, 150, 0.12);
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
  color: var(--color-text-tertiary);
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
  background: rgba(16, 139, 150, 0.08);
  transform: translateX(2px);
}

.side-nav__item--active {
  background: rgba(16, 139, 150, 0.14);
  color: var(--color-deep-teal);
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
  background: var(--color-surface);
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  color: #7a8699;
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
  background: #f8fafc;
  border-color: #dce2ea;
  transform: translateX(2px);
}

.settings-item--active {
  background: rgba(16, 139, 150, 0.12);
  border-color: #c8dde1;
  color: var(--color-deep-teal);
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
  background: #f6f1e8;
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
  border-color: #e1ddcf;
  transform: translateX(2px);
}

.profile-card--active {
  border-color: #d3cdbf;
  box-shadow: 0 8px 20px -12px rgba(71, 85, 105, 0.45);
}

.profile-card--routing {
  animation: sidebar-route-pulse 220ms ease;
}

.profile-avatar {
  align-items: center;
  background: #f8d9ad;
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
