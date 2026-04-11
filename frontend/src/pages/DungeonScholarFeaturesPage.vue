<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watchEffect } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import BaseButton from "../components/ui/BaseButton.vue";
import FeatureCard from "../components/ui/FeatureCard.vue";
import { useTheme, type Theme } from "../composables/useTheme";
import { SUPPORTED_LOCALES, type SupportedLocale } from "../i18n";
import { ROUTES } from "../constants/routes";

const isMenuOpen = ref(false);
const router = useRouter();
const { locale, t } = useI18n();
const { theme, setTheme } = useTheme();
const isRouting = ref(false);
const activeAction = ref<"login" | "sign-up" | "get-started" | null>(null);
const showLangDropdown = ref(false);

const themeCycle: Theme[] = ["light", "dark", "system"];

const languages = computed(() => {
  const _ = locale.value;
  return SUPPORTED_LOCALES.map((code) => ({
    code,
    name: t(`settings.localeNames.${code}`),
  }));
});

const currentLangName = computed(() => {
  return languages.value.find((entry) => entry.code === locale.value)?.name ?? locale.value;
});

const currentThemeLabel = computed(() => {
  const _ = locale.value;
  return t(`settings.preferences.${theme.value}`);
});

const closeHeaderDropdowns = () => {
  showLangDropdown.value = false;
};

const toggleLang = () => {
  showLangDropdown.value = !showLangDropdown.value;
};

const selectLang = (code: SupportedLocale) => {
  locale.value = code;
  showLangDropdown.value = false;
};

const cycleTheme = () => {
  const currentIndex = themeCycle.indexOf(theme.value);
  const nextIndex = (currentIndex + 1) % themeCycle.length;
  setTheme(themeCycle[nextIndex]);
};

onMounted(() => {
  document.addEventListener("click", closeHeaderDropdowns);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", closeHeaderDropdowns);
});

watchEffect(() => {
  document.title = t("features.metaTitle");
});

const navItems = computed(() => {
  const _ = locale.value;
  return [
    { label: t("landing.home"), href: ROUTES.landing },
    { label: t("landing.features"), href: ROUTES.features },
    { label: t("landing.pricing"), href: ROUTES.pricing },
    { label: t("landing.community"), href: ROUTES.community },
  ];
});

const featureCards = computed(() => {
  const _ = locale.value;
  return [
    {
      title: t("features.gameModesTitle"),
      description: t("features.gameModesDesc"),
      icon: "game",
      accent: "green" as const,
    },
    {
      title: t("features.aiDungeonTitle"),
      description: t("features.aiDungeonDesc"),
      icon: "brain",
      accent: "cyan" as const,
    },
    {
      title: t("features.zeroFrictionTitle"),
      description: t("features.zeroFrictionDesc"),
      icon: "cloud",
      accent: "green" as const,
    },
    {
      title: t("features.questSystemTitle"),
      description: t("features.questSystemDesc"),
      icon: "quest",
      accent: "cyan" as const,
    },
    {
      title: t("features.leaderboardTitle"),
      description: t("features.leaderboardDesc"),
      icon: "trophy",
      accent: "green" as const,
    },
    {
      title: t("features.walletTitle"),
      description: t("features.walletDesc"),
      icon: "wallet",
      accent: "cyan" as const,
    },
  ];
});

const footerLinks = computed(() => {
  const _ = locale.value;
  return [
    { text: t("landing.privacyPolicy"), href: "/privacy-policy" },
    { text: t("landing.termsOfService"), href: "/terms-of-service" },
    { text: t("landing.contactUs"), href: "/help-center" },
    { text: t("landing.twitter"), href: "#" },
    { text: t("landing.discord"), href: "#" },
  ];
});

const brandName = computed(() => {
  const _ = locale.value;
  return t("landing.brand");
});

const logoAlt = computed(() => {
  const _ = locale.value;
  return t("landing.logoAlt");
});

const mainNavAria = computed(() => {
  const _ = locale.value;
  return t("landing.mainNavAria");
});

const languageLabel = computed(() => {
  const _ = locale.value;
  return t("landing.languageLabel");
});

const loginLabel = computed(() => {
  const _ = locale.value;
  return t("landing.login");
});

const signUpLabel = computed(() => {
  const _ = locale.value;
  return t("landing.signUp");
});

const mobileNavAria = computed(() => {
  const _ = locale.value;
  return t("landing.mobileNavAria");
});

const footerLinksAria = computed(() => {
  const _ = locale.value;
  return t("landing.footerLinksAria");
});

const footerBrand = computed(() => {
  const _ = locale.value;
  return t("landing.footerBrand");
});

const copyrightLabel = computed(() => {
  const _ = locale.value;
  return t("landing.copyright");
});

const menuLabel = computed(() => {
  const _ = locale.value;
  return t("landing.menu");
});

const closeLabel = computed(() => {
  const _ = locale.value;
  return t("landing.close");
});

const routeByAuthState = async (action: "login" | "sign-up" | "get-started") => {
  if (isRouting.value) {
    return;
  }

  isRouting.value = true;
  activeAction.value = action;

  await new Promise<void>((resolve) => {
    window.setTimeout(() => resolve(), 220);
  });

  const targetPath =
    action === "get-started" ? ROUTES.home : action === "sign-up" ? ROUTES.signUp : ROUTES.login;
  await router.push(targetPath);

  isRouting.value = false;
  activeAction.value = null;
};
</script>

<template>
  <div class="features-page">
    <header class="site-header">
      <div class="container site-header__inner">
        <div class="brand">
          <div class="brand__badge">
            <img src="/taotie-logo.svg" :alt="logoAlt" class="brand__logo" />
          </div>
          <p class="brand__name">{{ brandName }}</p>
        </div>

        <nav class="site-nav site-nav--centered" :aria-label="mainNavAria">
          <router-link
            v-for="item in navItems"
            :key="item.label"
            :to="item.href"
            class="nav-link"
            :class="{ 'nav-link--active': $route.path === item.href }"
          >
            {{ item.label }}
          </router-link>
        </nav>

        <div class="header-right">
          <div class="header-icon-btn" @click.stop>
            <button
              class="icon-btn"
              type="button"
              :aria-expanded="showLangDropdown"
              :aria-label="`${languageLabel}: ${currentLangName}`"
              @click="toggleLang"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            </button>
            <div v-if="showLangDropdown" class="header-dropdown" role="menu" :aria-label="languageLabel">
              <button
                v-for="lang in languages"
                :key="lang.code"
                class="header-dropdown__item"
                :class="{ 'header-dropdown__item--active': locale === lang.code }"
                type="button"
                role="menuitemradio"
                :aria-checked="locale === lang.code"
                @click="selectLang(lang.code)"
              >
                {{ lang.name }}
              </button>
            </div>
          </div>

          <div class="header-icon-btn" @click.stop>
            <button
              class="icon-btn"
              type="button"
              :aria-label="`${t('settings.preferences.themeLabel')}: ${currentThemeLabel}`"
              @click="cycleTheme"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="12" cy="12" r="5" />
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
              </svg>
            </button>
          </div>

          <div class="header-auth">
            <BaseButton
              variant="primary"
              size="sm"
              class="cta-route-btn"
              :class="{ 'cta-route-btn--active': activeAction === 'login' }"
              :disabled="isRouting"
              @click="routeByAuthState('login')"
            >
              {{ loginLabel }}
            </BaseButton>
            <BaseButton
              variant="ghost"
              size="sm"
              class="cta-route-btn"
              :class="{ 'cta-route-btn--active': activeAction === 'sign-up' }"
              :disabled="isRouting"
              @click="routeByAuthState('sign-up')"
            >
              {{ signUpLabel }}
            </BaseButton>
          </div>
        </div>

        <button
          class="menu-toggle"
          type="button"
          :aria-expanded="isMenuOpen"
          aria-controls="mobile-nav"
          @click="isMenuOpen = !isMenuOpen"
        >
          {{ isMenuOpen ? closeLabel : menuLabel }}
        </button>
      </div>

      <nav id="mobile-nav" class="mobile-nav" :class="{ 'mobile-nav--open': isMenuOpen }" :aria-label="mobileNavAria">
        <router-link
          v-for="item in navItems"
          :key="`mobile-${item.label}`"
          :to="item.href"
          class="mobile-nav-link"
          :class="{ 'mobile-nav-link--active': $route.path === item.href }"
          @click="isMenuOpen = false"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </header>

    <main>
      <section class="features-hero">
        <div class="container features-hero__inner">
          <h1 class="features-hero__title">{{ t("features.heroTitle") }}</h1>
          <p class="features-hero__subtitle">{{ t("features.heroSubtitle") }}</p>
        </div>
      </section>

      <section class="features-grid-section">
        <div class="container">
          <div class="feature-grid">
            <FeatureCard
              v-for="feature in featureCards"
              :key="feature.title"
              :title="feature.title"
              :description="feature.description"
              :accent="feature.accent"
            >
              <template #icon>
                <svg v-if="feature.icon === 'game'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M15 5v2M15 11v2M15 17v2M5 5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5z" />
                  <path d="M9 12h6M12 9v6" />
                </svg>
                <svg v-else-if="feature.icon === 'brain'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2a4 4 0 0 1 4 4c0 1.95-1.4 3.58-3.25 3.93M8 6a4 4 0 0 1 8 0" />
                  <path d="M12 10v4M8 14a4 4 0 0 0 4 4 4 4 0 0 0 4-4" />
                  <circle cx="12" cy="18" r="4" />
                </svg>
                <svg v-else-if="feature.icon === 'cloud'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
                </svg>
                <svg v-else-if="feature.icon === 'quest'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <line x1="10" y1="9" x2="8" y2="9" />
                </svg>
                <svg v-else-if="feature.icon === 'trophy'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
                  <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
                  <path d="M4 22h16" />
                  <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20 7 22" />
                  <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20 17 22" />
                  <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
                </svg>
                <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="5" width="20" height="14" rx="2" />
                  <line x1="2" y1="10" x2="22" y2="10" />
                </svg>
              </template>
            </FeatureCard>
          </div>
        </div>
      </section>

      <section class="features-cta">
        <div class="cta__overlay" />
        <div class="container cta__inner">
          <h2>{{ t("features.ctaTitle") }}</h2>
          <p>{{ t("features.ctaDesc") }}</p>
          <BaseButton @click="routeByAuthState('get-started')">
            {{ t("features.ctaButton") }}
          </BaseButton>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <div class="container site-footer__inner">
        <p class="site-footer__brand">{{ footerBrand }}</p>

        <nav class="site-footer__links" :aria-label="footerLinksAria">
          <a v-for="item in footerLinks" :key="item.text" :href="item.href">{{ item.text }}</a>
        </nav>

        <p class="site-footer__copyright">{{ copyrightLabel }}</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.features-page {
  background: radial-gradient(circle at top right, rgba(212, 175, 55, 0.1), transparent 45%), var(--color-page-bg);
}

.container {
  margin: 0 auto;
  max-width: 1280px;
  padding: 0 32px;
  width: 100%;
}

.site-header {
  backdrop-filter: blur(6px);
  background: var(--color-glass-bg);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.site-header__inner {
  align-items: center;
  display: flex;
  justify-content: space-between;
  min-height: 64px;
  position: relative;
}

.brand {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  gap: 12px;
}

.brand__badge {
  align-items: center;
  background: rgba(255, 244, 214, 0.28);
  border: 1px solid #f0c95f;
  border-radius: var(--radius-sm);
  display: inline-flex;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.brand__logo {
  display: block;
  height: 30px;
  width: 30px;
}

.brand__name {
  color: var(--color-text-primary);
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin: 0;
}

.site-nav {
  display: flex;
  gap: 32px;
}

.site-nav--centered {
  left: 50%;
  position: absolute;
  transform: translateX(-50%);
}

.header-right {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  gap: var(--space-2);
}

.site-nav--centered .nav-link,
.site-footer__links a {
  color: var(--color-text-tertiary);
  font-size: 14px;
  text-decoration: none;
  position: relative;
  transition: color 0.2s ease;
}

.site-nav--centered .nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--color-primary-500);
  transition: width 0.3s ease, left 0.3s ease;
}

.site-nav--centered .nav-link:hover {
  color: var(--color-primary-700);
}

.site-nav--centered .nav-link:hover::after {
  width: 100%;
  left: 0;
}

.site-nav--centered .nav-link--active {
  color: var(--color-primary-600);
  font-weight: 500;
}

.site-nav--centered .nav-link--active::after {
  width: 100%;
  left: 0;
}

.menu-toggle {
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  display: none;
  font-size: var(--text-sm);
  min-height: 36px;
  padding: 0 var(--space-3);
}

.mobile-nav {
  background: var(--color-glass-bg);
  border-bottom: 1px solid var(--color-border);
  display: none;
  flex-direction: column;
  gap: var(--space-2);
  padding: 0 var(--space-8);
}

.mobile-nav .mobile-nav-link {
  color: var(--color-text-tertiary);
  padding: var(--space-2) 0;
  text-decoration: none;
  position: relative;
  transition: color 0.2s ease, padding-left 0.2s ease;
}

.mobile-nav .mobile-nav-link:hover {
  color: var(--color-primary-600);
  padding-left: var(--space-2);
}

.mobile-nav .mobile-nav-link--active {
  color: var(--color-primary-600);
  font-weight: 500;
  padding-left: var(--space-2);
}

.header-icon-btn {
  align-items: center;
  display: inline-flex;
  position: relative;
}

.icon-btn {
  align-items: center;
  background: transparent;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  display: inline-flex;
  height: 36px;
  justify-content: center;
  transition: color 0.2s ease, background-color 0.2s ease;
  width: 36px;
}

.icon-btn:hover {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
}

.header-dropdown {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-elevated);
  min-width: 140px;
  overflow: hidden;
  position: absolute;
  right: 0;
  top: calc(100% + var(--space-2));
  z-index: 100;
}

.header-dropdown__item {
  background: transparent;
  border: 0;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: block;
  font-size: var(--text-sm);
  padding: 10px 14px;
  text-align: left;
  transition: background-color 0.15s ease, color 0.15s ease;
  width: 100%;
}

.header-dropdown__item:hover {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
}

.header-dropdown__item--active {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
  font-weight: 500;
}

.header-auth {
  display: flex;
  gap: var(--space-2);
  margin-left: var(--space-4);
}

.cta-route-btn {
  transition: transform 0.2s ease;
}

.cta-route-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.cta-route-btn--active {
  transform: scale(0.97);
}

.features-hero {
  padding: 80px 0 60px;
  text-align: center;
}

.features-hero__title {
  color: var(--color-text-primary);
  font-family: var(--font-serif);
  font-size: var(--text-4xl);
  font-weight: 700;
  margin: 0 0 var(--space-4);
}

.features-hero__subtitle {
  color: var(--color-text-secondary);
  font-size: var(--text-lg);
  margin: 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.features-grid-section {
  padding: 40px 0 80px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--space-6);
}

.features-cta {
  background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-700));
  padding: 80px 0;
  position: relative;
  text-align: center;
}

.cta__overlay {
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  position: absolute;
  inset: 0;
}

.cta__inner {
  position: relative;
  z-index: 1;
}

.cta__inner h2 {
  color: white;
  font-family: var(--font-serif);
  font-size: var(--text-3xl);
  margin: 0 0 var(--space-4);
}

.cta__inner p {
  color: rgba(255, 255, 255, 0.9);
  font-size: var(--text-lg);
  margin: 0 0 var(--space-6);
}

.site-footer {
  border-top: 1px solid var(--color-border);
  padding: var(--space-8) 0;
}

.site-footer__inner {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  text-align: center;
}

.site-footer__brand {
  color: var(--color-text-primary);
  font-family: var(--font-serif);
  font-size: var(--text-lg);
  font-weight: 600;
  margin: 0;
}

.site-footer__links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  justify-content: center;
}

.site-footer__links a {
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  text-decoration: none;
  transition: color 0.2s ease;
}

.site-footer__links a:hover {
  color: var(--color-primary-600);
}

.site-footer__copyright {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  margin: 0;
}

@media (max-width: 768px) {
  .site-nav--centered {
    display: none;
  }

  .header-auth {
    display: none;
  }

  .menu-toggle {
    display: block;
  }

  .mobile-nav--open {
    display: flex;
  }

  .features-hero__title {
    font-size: var(--text-3xl);
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>