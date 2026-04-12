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
  // Access locale.value to make computed reactive to locale changes
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
  // Access locale.value to make computed reactive to locale changes
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
  document.title = t("landing.metaTitle");
});

const navItems = computed(() => {
  // Access locale.value to make computed reactive to locale changes
  const _ = locale.value;
  return [
    { label: t("landing.home"), href: ROUTES.landing },
    { label: t("landing.features"), href: ROUTES.features },
    { label: t("landing.pricing"), href: ROUTES.pricing },
    { label: t("landing.community"), href: ROUTES.community },
  ];
});

const featureCards = computed(() => {
  // Access locale.value to make computed reactive to locale changes
  const _ = locale.value;
  return [
    {
      title: t("landing.gameModesTitle"),
      description: t("landing.gameModesDesc"),
      icon: "🗡",
      accent: "green" as const,
    },
    {
      title: t("landing.aiDungeonTitle"),
      description: t("landing.aiDungeonDesc"),
      icon: "🧠",
      accent: "cyan" as const,
    },
    {
      title: t("landing.zeroFrictionTitle"),
      description: t("landing.zeroFrictionDesc"),
      icon: "☁",
      accent: "green" as const,
    },
  ];
});

const footerLinks = computed(() => {
  // Access locale.value to make computed reactive to locale changes
  const _ = locale.value;
  return [
{ text: t("landing.privacyPolicy"), href: "/privacy-policy" },
        { text: t("landing.termsOfService"), href: "/terms-of-service" },
        { text: t("landing.contactUs"), href: "/help-center" },
    { text: t("landing.twitter"), href: "#" },
    { text: t("landing.discord"), href: "#" },
  ];
});

// Template-level translations that need locale tracking
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

const betaLabel = computed(() => {
  const _ = locale.value;
  return t("landing.beta");
});

const heroTitle1 = computed(() => {
  const _ = locale.value;
  return t("landing.heroTitle1");
});

const heroTitle2 = computed(() => {
  const _ = locale.value;
  return t("landing.heroTitle2");
});

const heroTitle3 = computed(() => {
  const _ = locale.value;
  return t("landing.heroTitle3");
});

const heroSubtitle = computed(() => {
  const _ = locale.value;
  return t("landing.heroSubtitle");
});

const getStartedLabel = computed(() => {
  const _ = locale.value;
  return t("landing.getStarted");
});

const watchDemoLabel = computed(() => {
  const _ = locale.value;
  return t("landing.watchDemo");
});

const scholarsJoinedLabel = computed(() => {
  const _ = locale.value;
  return t("landing.scholarsJoined");
});

const forgeTitle = computed(() => {
  const _ = locale.value;
  return t("landing.forgeTitle");
});

const forgeSubtitle = computed(() => {
  const _ = locale.value;
  return t("landing.forgeSubtitle");
});

const joinScholarLabel = computed(() => {
  const _ = locale.value;
  return t("landing.joinScholar");
});

const readyAscendLabel = computed(() => {
  const _ = locale.value;
  return t("landing.readyAscend");
});

const ascendDescLabel = computed(() => {
  const _ = locale.value;
  return t("landing.ascendDesc");
});

const startJourneyLabel = computed(() => {
  const _ = locale.value;
  return t("landing.startJourney");
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

const heroMascotAlt = computed(() => {
  const _ = locale.value;
  return t("landing.heroMascotAlt");
});

const heroStatTopLine1 = computed(() => {
  const _ = locale.value;
  return t("landing.heroStatTopLine1");
});

const heroStatTopLine2 = computed(() => {
  const _ = locale.value;
  return t("landing.heroStatTopLine2");
});

const heroStatBottomLine1 = computed(() => {
  const _ = locale.value;
  return t("landing.heroStatBottomLine1");
});

const heroStatBottomLine2 = computed(() => {
  const _ = locale.value;
  return t("landing.heroStatBottomLine2");
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
  <div class="landing-page" data-node-id="4:1178">
    <header class="site-header" data-node-id="4:1317">
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
      <section class="hero">
        <div class="container hero__inner">
          <div class="hero__content">
            <p class="hero__beta">{{ betaLabel }}</p>
            <h1 class="hero__title">
              {{ heroTitle1 }}
              <span>{{ heroTitle2 }}</span>
              <span>{{ heroTitle3 }}</span>
            </h1>
            <p class="hero__subtitle">
              {{ heroSubtitle }}
            </p>
            <div class="hero__actions">
              <BaseButton
                class="cta-route-btn"
                :class="{ 'cta-route-btn--active': activeAction === 'get-started' }"
                :disabled="isRouting"
                @click="routeByAuthState('get-started')"
              >
                {{ getStartedLabel }}
              </BaseButton>
              <BaseButton variant="ghost">{{ watchDemoLabel }}</BaseButton>
            </div>
            <p class="hero__social">{{ scholarsJoinedLabel }}</p>
          </div>

          <div class="hero__visual" aria-hidden="true">
            <div class="hero__card">
              <div class="hero__stat hero__stat--top">{{ heroStatTopLine1 }}<br /><strong>{{ heroStatTopLine2 }}</strong></div>
              <div class="hero__mascot">
                <img src="/taotie-hero.svg" :alt="heroMascotAlt" class="hero__mascot-image" />
              </div>
              <div class="hero__stat hero__stat--bottom">{{ heroStatBottomLine1 }}<br /><strong>{{ heroStatBottomLine2 }}</strong></div>
            </div>
          </div>
        </div>
      </section>

      <section class="features" data-node-id="4:1182">
        <div class="container">
          <div class="section-head">
            <h2>{{ forgeTitle }}</h2>
            <p>
              {{ forgeSubtitle }}
            </p>
          </div>

          <div class="feature-grid">
            <FeatureCard
              v-for="feature in featureCards"
              :key="feature.title"
              :title="feature.title"
              :description="feature.description"
              :accent="feature.accent"
            >
              <template #icon>{{ feature.icon }}</template>
            </FeatureCard>
          </div>
        </div>
      </section>

      <section class="cta" data-node-id="4:1217">
        <div class="cta__overlay" />
        <div class="container cta__inner">
          <p class="cta__badge">{{ joinScholarLabel }}</p>
          <h2>{{ readyAscendLabel }}</h2>
          <p>
            {{ ascendDescLabel }}
          </p>
          <BaseButton>{{ startJourneyLabel }}</BaseButton>
        </div>
      </section>
    </main>

    <footer class="site-footer" data-node-id="4:1296">
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
.landing-page {
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

.site-nav--centered a:hover,
.site-footer__links a:hover {
  color: var(--color-primary-700);
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
  color: var(--color-primary-700);
}

.header-dropdown__item--active {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  font-weight: 600;
}

.header-auth {
  align-items: center;
  display: flex;
  gap: var(--space-2);
}

.hero {
  background: linear-gradient(90deg, rgba(212, 177, 130, 0.35) 0 38%, rgba(236, 213, 172, 0.38) 38% 100%);
  min-height: 760px;
  overflow: hidden;
  padding: 64px 0 112px;
}

.hero__inner {
  align-items: center;
  display: grid;
  gap: 40px;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}

.hero__beta {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: var(--radius-pill);
  color: var(--color-primary-700);
  display: inline-block;
  font-size: 14px;
  margin: 0 0 24px;
  padding: 6px 14px;
}

.hero__title {
  font-family: var(--font-serif);
  font-size: clamp(44px, 6vw, 60px);
  font-weight: 700;
  letter-spacing: -1.5px;
  line-height: 1.05;
  margin: 0;
}

.hero__title span {
  background: linear-gradient(90deg, var(--color-primary-600), #0891b2);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  display: block;
}

.hero__subtitle {
  color: var(--color-text-secondary);
  font-size: 18px;
  line-height: 1.8;
  margin: 24px 0 0;
  max-width: 580px;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 24px;
}

.hero__actions :deep(.base-btn--ghost) {
  background: var(--color-glass-bg);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

.hero__actions :deep(.base-btn--ghost:hover) {
  background: color-mix(in srgb, var(--color-surface) 82%, var(--color-glass-bg));
  border-color: var(--color-border);
  color: var(--color-text-strong);
}

.hero__actions :deep(.cta-route-btn),
.site-header__inner :deep(.cta-route-btn) {
  transform-origin: center;
}

.hero__actions :deep(.cta-route-btn--active),
.site-header__inner :deep(.cta-route-btn--active) {
  animation: route-pulse 220ms ease;
}

@keyframes route-pulse {
  0% {
    transform: scale(1);
  }

  45% {
    transform: scale(0.96);
  }

  100% {
    transform: scale(1);
  }
}

.hero__social {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 24px 0 0;
}

.hero__visual {
  align-items: center;
  display: flex;
  justify-content: center;
  min-height: 500px;
}

.hero__card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-elevated);
  min-height: 470px;
  padding: 16px;
  position: relative;
  transform: rotate(1deg);
  width: min(624px, 100%);
}

.hero__card::before {
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.12), rgba(16, 185, 129, 0.02));
  border-radius: var(--radius-md);
  content: "";
  inset: 16px;
  position: absolute;
}

.hero__mascot {
  align-items: center;
  display: flex;
  height: 100%;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.hero__mascot-image {
  display: block;
  height: auto;
  max-height: 320px;
  max-width: min(92%, 520px);
  object-fit: contain;
  width: 100%;
}

.hero__stat {
  backdrop-filter: blur(2px);
  background: color-mix(in srgb, var(--color-white) 90%, transparent);
  border: 1px solid var(--color-primary-100);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.4;
  padding: 13px;
  position: absolute;
  z-index: 2;
}

.hero__stat strong {
  color: var(--color-text-strong);
  font-size: 14px;
}

.hero__stat--top {
  right: 32px;
  top: 32px;
}

.hero__stat--bottom {
  bottom: 48px;
  left: 32px;
}

.features {
  background: var(--color-surface-alt);
  padding: 96px 0;
}

.section-head {
  margin: 0 auto;
  max-width: 672px;
  text-align: center;
}

.section-head h2,
.cta h2 {
  font-family: var(--font-serif);
  font-size: clamp(36px, 4vw, 48px);
  margin: 0;
}

.section-head p,
.cta p {
  color: var(--color-text-secondary);
  font-size: 18px;
  line-height: 1.6;
  margin: 16px 0 0;
}

.feature-grid {
  display: grid;
  gap: 32px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 64px;
}

.cta {
  overflow: hidden;
  padding: 80px 0;
  position: relative;
}

.cta__overlay {
  background: linear-gradient(180deg, rgba(252, 251, 247, 0.45), var(--color-surface-alt));
  inset: 0;
  position: absolute;
}

.cta__inner {
  position: relative;
  text-align: center;
}

.cta__badge {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: var(--radius-pill);
  color: var(--color-primary-700);
  display: inline-block;
  font-size: 14px;
  margin: 0;
  padding: 12px 16px;
}

.cta__inner > h2 {
  margin-top: 28px;
}

.cta__inner > p {
  margin: 16px auto 0;
  max-width: 720px;
}

.cta__inner :deep(.base-btn) {
  margin-top: 32px;
  min-height: 56px;
}

.site-footer {
  background: var(--color-page-bg);
  border-top: 1px solid var(--color-border);
  padding: 48px 0;
}

.site-footer__inner {
  text-align: center;
}

.site-footer__brand {
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 700;
  margin: 0;
}

.site-footer__links {
  display: flex;
  flex-wrap: wrap;
  gap: 24px 32px;
  justify-content: center;
  margin-top: 32px;
}

.site-footer__copyright {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 32px 0 0;
  opacity: 0.65;
}

@media (max-width: 1120px) {
  .hero__inner {
    grid-template-columns: 1fr;
  }

  .hero__visual {
    min-height: 380px;
  }

  .feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .container {
    padding: 0 20px;
  }

  .site-nav {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
    margin-left: auto;
    margin-right: var(--space-2);
  }

  .mobile-nav--open {
    display: flex;
    padding-bottom: var(--space-3);
  }

  .hero {
    padding: 48px 0 72px;
  }

  .hero__subtitle,
  .section-head p,
  .cta p {
    font-size: 16px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
    margin-top: 40px;
  }

  .hero__stat {
    padding: 10px;
  }

  .hero__stat--top {
    right: 16px;
    top: 16px;
  }

  .hero__stat--bottom {
    bottom: 20px;
    left: 16px;
  }
}
</style>
