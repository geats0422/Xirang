<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import AppSidebar from "../components/layout/AppSidebar.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";

type IdentityItem = {
  key: string;
  name: string;
  icon: string;
  connected: boolean;
};

const { t, locale } = useI18n();

onMounted(() => {
  document.title = t("profile.metaTitle");
});

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("profile.metaTitle");
});

const settingsRoute = ROUTES.settings;
const shopRoute = ROUTES.shop;

const identities = ref<IdentityItem[]>([
  { key: "github", name: "GitHub", icon: "⌘", connected: true },
  { key: "google", name: "Google", icon: "G", connected: false },
  { key: "microsoft", name: "Microsoft", icon: "◰", connected: false },
  { key: "email", name: "Email", icon: "✉", connected: false },
]);

const { currentPath, navigateTo, routingTarget } = useRouteNavigation();

const toggleIdentity = (key: string) => {
  identities.value = identities.value.map((item) =>
    item.key === key ? { ...item, connected: !item.connected } : item,
  );
};
</script>

<template>
  <div class="profile-page">
    <AppSidebar
      :current-path="currentPath"
      :routing-target="routingTarget"
      profile-name="Scholar Li"
      profile-level="Level 42 Scholar"
      @navigate="navigateTo"
    />

    <main class="profile-main">
      <div class="profile-overlay" aria-hidden="true" @click="navigateTo(settingsRoute)" />

      <section class="profile-modal" aria-label="Profile dialog">
        <div class="profile-modal__decor profile-modal__decor--teal" />
        <div class="profile-modal__decor profile-modal__decor--amber" />

        <div class="avatar-ring">
          <div class="avatar-ring__image">🧝</div>
          <button class="avatar-ring__camera" type="button" :aria-label="t('profile.changeAvatar')">📷</button>
        </div>

        <header class="identity-head">
          <div class="identity-head__name-row">
            <h1>Seeker_01</h1>
            <span>✓</span>
          </div>

          <div class="identity-stats">
            <article class="stat-pill">
              <span>XP</span>
              <strong>12,450</strong>
            </article>
            <article class="stat-pill">
              <span>🔥 {{ t("profile.streak") }}</span>
              <strong>{{ t("profile.days", { days: 15 }) }}</strong>
            </article>
            <button class="stat-pill stat-pill--shop" type="button" @click="navigateTo(shopRoute)">
              <span>🪙 {{ t("profile.coins") }}</span>
              <strong>2,300</strong>
            </button>
          </div>
        </header>

        <section class="linked-identity">
          <div class="section-title">⛓ {{ t("profile.linkedIdentity") }}</div>

          <button
            v-for="item in identities"
            :key="item.key"
            class="identity-row"
            :class="{ 'identity-row--connected': item.connected }"
            type="button"
            @click="toggleIdentity(item.key)"
          >
            <div class="identity-row__left">
              <span class="identity-row__icon">{{ item.icon }}</span>
              <div>
                <p class="identity-row__name">{{ item.name }}</p>
                <p class="identity-row__status">{{ item.connected ? t("profile.connected") : t("profile.notConnected") }}</p>
              </div>
            </div>

            <span class="identity-row__action" :class="{ 'identity-row__action--on': item.connected }">
              {{ item.connected ? "◉" : t("profile.link") }}
            </span>
          </button>
        </section>

        <footer class="profile-footer">
          <button class="signout-btn" type="button">↪ {{ t("profile.signOut") }}</button>
        </footer>
      </section>
    </main>
  </div>
</template>

<style scoped>
.profile-page {
  display: grid;
  grid-template-columns: 256px minmax(0, 1fr);
  min-height: 100vh;
}

.profile-main {
  background: #f6f8f6;
  min-height: 100vh;
  overflow: hidden;
  padding: 24px;
  position: relative;
}

.profile-main::before {
  background: radial-gradient(circle at 22% 18%, rgba(46, 164, 168, 0.18), transparent 34%),
    radial-gradient(circle at 80% 82%, rgba(246, 185, 113, 0.2), transparent 36%),
    linear-gradient(180deg, rgba(234, 242, 239, 0.9), rgba(246, 248, 246, 0.95));
  content: "";
  inset: 0;
  position: absolute;
}

.profile-overlay {
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  background: rgba(255, 255, 255, 0.3);
  inset: 0;
  position: absolute;
}

.profile-modal {
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 32px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.07);
  margin: 120px auto 0;
  max-width: 512px;
  padding: 64px 40px 32px;
  position: relative;
  z-index: 1;
}

@supports not ((backdrop-filter: blur(6px)) or (-webkit-backdrop-filter: blur(6px))) {
  .profile-overlay {
    background: rgba(115, 129, 125, 0.72);
  }

  .profile-modal {
    background: rgba(246, 248, 246, 0.94);
  }
}

.profile-modal__decor {
  border-radius: 999px;
  filter: blur(32px);
  opacity: 0.2;
  position: absolute;
}

.profile-modal__decor--teal {
  background: #5eead4;
  height: 128px;
  right: 0;
  top: 0;
  width: 128px;
}

.profile-modal__decor--amber {
  background: #fed7aa;
  bottom: 0;
  height: 96px;
  left: 0;
  width: 96px;
}

.avatar-ring {
  left: 50%;
  position: absolute;
  top: -64px;
  transform: translateX(-50%);
}

.avatar-ring__image {
  align-items: center;
  background: linear-gradient(180deg, #706b72, #b2a9af);
  border: 4px solid #fff;
  border-radius: 999px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
  color: #f3f5f9;
  display: inline-flex;
  font-size: 56px;
  height: 128px;
  justify-content: center;
  width: 128px;
}

.avatar-ring__camera {
  align-items: center;
  background: #14b8a6;
  border: 2px solid #fff;
  border-radius: 999px;
  bottom: 4px;
  color: #fff;
  cursor: pointer;
  display: inline-flex;
  font-size: 12px;
  height: 28px;
  justify-content: center;
  position: absolute;
  right: 4px;
  width: 28px;
}

.identity-head {
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  padding-bottom: 28px;
}

.identity-head__name-row {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: center;
}

.identity-head__name-row h1 {
  color: #1e293b;
  font-family: var(--font-serif);
  font-size: 31px;
  line-height: 1;
  margin: 0;
}

.identity-head__name-row span {
  color: #14b8a6;
  font-size: 15px;
  font-weight: 700;
}

.identity-stats {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 16px;
}

.stat-pill {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid #f1f5f9;
  border-radius: 24px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  font-family: inherit;
  padding: 9px;
  text-align: center;
}

.stat-pill--shop:hover {
  transform: translateY(-1px);
}

.stat-pill span {
  color: #64748b;
  display: block;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.stat-pill strong {
  color: #1e293b;
  display: block;
  font-size: 17px;
  margin-top: 4px;
}

.linked-identity {
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  padding: 24px 0 28px;
}

.section-title {
  color: #1e293b;
  font-family: var(--font-serif);
  font-size: 31px;
  margin-bottom: 14px;
}

.identity-row {
  align-items: center;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid transparent;
  border-radius: 24px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  padding: 12px;
  transition: border-color 0.2s ease, background-color 0.2s ease;
  width: 100%;
}

.identity-row--connected {
  background: rgba(255, 255, 255, 0.82);
  border-color: #ccfbf1;
}

.identity-row__left {
  align-items: center;
  display: flex;
  gap: 12px;
}

.identity-row__icon {
  align-items: center;
  background: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 16px;
  color: #334155;
  display: inline-flex;
  font-size: 17px;
  font-weight: 700;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.identity-row--connected .identity-row__icon {
  background: #0f172a;
  color: #fff;
}

.identity-row__name {
  color: #1e293b;
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.identity-row__status {
  color: #64748b;
  font-size: 12px;
  margin: 2px 0 0;
}

.identity-row--connected .identity-row__status {
  color: #0d9488;
}

.identity-row__action {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  color: #334155;
  font-size: 12px;
  font-weight: 700;
  min-width: 58px;
  padding: 6px 10px;
  text-align: center;
}

.identity-row__action--on {
  border-color: #9de8dc;
  color: #0d9488;
}

.profile-footer {
  display: flex;
  justify-content: center;
  padding-top: 24px;
}

.signout-btn {
  background: transparent;
  border: 0;
  color: rgba(239, 68, 68, 0.8);
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 700;
}

@media (max-width: 1080px) {
  .profile-page {
    grid-template-columns: 1fr;
  }

  .profile-main {
    padding: 18px;
  }
}

@media (max-width: 768px) {
  .profile-main {
    order: -1;
    padding: 14px;
  }

  .profile-modal {
    margin-top: 88px;
    padding: 52px 16px 20px;
  }

  .identity-stats {
    grid-template-columns: 1fr;
  }
}
</style>
