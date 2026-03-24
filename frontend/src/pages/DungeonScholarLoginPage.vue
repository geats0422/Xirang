<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import BaseButton from "../components/ui/BaseButton.vue";
import { useScholarData } from "../composables/useScholarData";
import { ROUTES } from "../constants/routes";
import { SUPPORTED_LOCALES, type SupportedLocale } from "../i18n";

const route = useRoute();
const router = useRouter();
const { t, locale } = useI18n();
const { applyLanguage } = useScholarData();

const isSignUpRoute = computed(() => route.path === ROUTES.signUp);
const isLanguageMenuOpen = ref(false);

const socialProviders = computed(() => [
  {
    key: "google",
    label: t("login.social.google"),
    icon: "/login-assets/icon-google.svg",
  },
  {
    key: "microsoft",
    label: t("login.social.microsoft"),
    icon: "/login-assets/icon-microsoft.svg",
  },
  {
    key: "github",
    label: t("login.social.github"),
    icon: "/login-assets/icon-github.svg",
  },
]);

const languageOptions = SUPPORTED_LOCALES.filter((item) => item === "en" || item === "zh-CN" || item === "zh-TW");

const bgImage = "/login-assets/bg-pattern.svg";
const heroImage = "/taotie-hero.svg";
const mailIcon = "/login-assets/icon-mail.svg";
const eyeIcon = "/login-assets/icon-eye.svg";

const formTitle = computed(() => (isSignUpRoute.value ? t("login.signUpTitle") : t("login.title")));
const formSubtitle = computed(() =>
  isSignUpRoute.value ? t("login.signUpSubtitle") : t("login.subtitle"),
);
const primaryActionLabel = computed(() =>
  isSignUpRoute.value ? t("login.signUpAction") : t("login.enterDungeon"),
);
const panelEyebrow = computed(() =>
  isSignUpRoute.value ? t("login.panelSignUpEyebrow") : t("login.panelLoginEyebrow"),
);
const panelTitle = computed(() => (isSignUpRoute.value ? t("login.panelSignUpTitle") : t("login.panelLoginTitle")));
const panelBody = computed(() => (isSignUpRoute.value ? t("login.panelSignUpBody") : t("login.panelLoginBody")));

const localeName = (value: SupportedLocale) => t(`settings.localeNames.${value}`);

const switchLanguage = (value: SupportedLocale) => {
  applyLanguage(value);
  isLanguageMenuOpen.value = false;
};

const toggleLanguageMenu = () => {
  isLanguageMenuOpen.value = !isLanguageMenuOpen.value;
};

const goToLogin = async () => {
  if (!isSignUpRoute.value) {
    return;
  }
  await router.push(ROUTES.login);
};

const goToSignUp = async () => {
  if (isSignUpRoute.value) {
    return;
  }
  await router.push(ROUTES.signUp);
};

watchEffect(() => {
  document.title = isSignUpRoute.value ? t("login.signUpMetaTitle") : t("login.metaTitle");
});
</script>

<template>
  <div class="auth-page" data-node-id="4:714">
    <div class="auth-page__bg" aria-hidden="true">
      <img :src="bgImage" alt="" />
    </div>

    <div class="language-dock">
      <button
        class="language-dock__trigger"
        type="button"
        :aria-expanded="isLanguageMenuOpen"
        :aria-label="$t('landing.languageLabel')"
        @click="toggleLanguageMenu"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M12 3A9 9 0 1 0 12 21A9 9 0 1 0 12 3ZM5.7 10.5H9.2C9.3 8.6 9.8 6.8 10.5 5.6C8.2 6.2 6.4 8.1 5.7 10.5ZM5.7 13.5C6.4 15.9 8.2 17.8 10.5 18.4C9.8 17.2 9.3 15.4 9.2 13.5H5.7ZM12 5.1C11.3 6.1 10.8 8.1 10.7 10.5H13.3C13.2 8.1 12.7 6.1 12 5.1ZM12 18.9C12.7 17.9 13.2 15.9 13.3 13.5H10.7C10.8 15.9 11.3 17.9 12 18.9ZM13.5 18.4C15.8 17.8 17.6 15.9 18.3 13.5H14.8C14.7 15.4 14.2 17.2 13.5 18.4ZM14.8 10.5H18.3C17.6 8.1 15.8 6.2 13.5 5.6C14.2 6.8 14.7 8.6 14.8 10.5Z"
          />
        </svg>
      </button>

      <div v-if="isLanguageMenuOpen" class="language-dock__menu" role="menu">
        <button
          v-for="value in languageOptions"
          :key="value"
          type="button"
          class="language-dock__option"
          :class="{ 'language-dock__option--active': locale === value }"
          role="menuitemradio"
          :aria-checked="locale === value"
          @click="switchLanguage(value)"
        >
          {{ localeName(value) }}
        </button>
      </div>
    </div>

    <main class="auth-main">
      <section class="auth-panel" aria-hidden="true">
        <div class="auth-panel__badge">
          <img src="/taotie-logo.svg" :alt="$t('landing.logoAlt')" />
          <span>{{ $t("landing.brand") }}</span>
        </div>
        <p class="auth-panel__eyebrow">{{ panelEyebrow }}</p>
        <h1>{{ panelTitle }}</h1>
        <p>{{ panelBody }}</p>
        <img class="auth-panel__hero" :src="heroImage" :alt="$t('landing.heroMascotAlt')" />
      </section>

      <section class="auth-card" :aria-label="$t('login.cardAria')">
        <header class="auth-card__header">
          <h2>{{ formTitle }}</h2>
          <p>{{ formSubtitle }}</p>
        </header>

        <div class="social-buttons">
          <button v-for="provider in socialProviders" :key="provider.key" type="button" class="social-buttons__item">
            <span class="social-buttons__icon" aria-hidden="true">
              <img :src="provider.icon" alt="" />
            </span>
            <span>{{ provider.label }}</span>
          </button>
        </div>

        <div class="divider">
          <span>{{ $t("login.emailDivider") }}</span>
        </div>

        <form class="email-form" @submit.prevent>
          <label v-if="isSignUpRoute" class="email-form__field">
            <span>{{ $t("login.nameLabel") }}</span>
            <span class="email-form__input-wrap">
              <input type="text" :placeholder="$t('login.namePlaceholder')" />
            </span>
          </label>

          <label class="email-form__field">
            <span>{{ $t("login.emailLabel") }}</span>
            <span class="email-form__input-wrap">
              <input type="email" :placeholder="$t('login.emailPlaceholder')" />
              <img class="email-form__field-icon email-form__field-icon--mail" :src="mailIcon" alt="" aria-hidden="true" />
            </span>
          </label>

          <label class="email-form__field">
            <span>{{ $t("login.passwordLabel") }}</span>
            <span class="email-form__input-wrap">
              <input type="password" :placeholder="$t('login.passwordPlaceholder')" />
              <img class="email-form__field-icon email-form__field-icon--eye" :src="eyeIcon" alt="" aria-hidden="true" />
            </span>
          </label>

          <label v-if="isSignUpRoute" class="email-form__field">
            <span>{{ $t("login.confirmPasswordLabel") }}</span>
            <span class="email-form__input-wrap">
              <input type="password" :placeholder="$t('login.confirmPasswordPlaceholder')" />
              <img class="email-form__field-icon email-form__field-icon--eye" :src="eyeIcon" alt="" aria-hidden="true" />
            </span>
          </label>

          <BaseButton class="email-form__submit" full-width>{{ primaryActionLabel }}</BaseButton>
        </form>

        <footer class="card-footer">
          <a href="#">{{ $t("login.forgotPassword") }}</a>
          <p v-if="isSignUpRoute">
            {{ $t("login.haveAccount") }}
            <button type="button" class="card-footer__switch" @click="goToLogin">{{ $t("login.backToLogin") }}</button>
          </p>
          <p v-else>
            {{ $t("login.newHere") }}
            <button type="button" class="card-footer__switch" @click="goToSignUp">{{ $t("login.forgeAccount") }}</button>
          </p>
        </footer>
      </section>
    </main>

    <footer class="page-footer">
      <p>{{ $t("login.copyright") }}</p>
    </footer>
  </div>
</template>

<style scoped>
.auth-page {
  align-items: stretch;
  background: linear-gradient(120deg, rgba(15, 102, 102, 0.08), rgba(255, 255, 255, 0.96));
  display: flex;
  flex-direction: column;
  isolation: isolate;
  min-height: 100vh;
  overflow: hidden;
  position: relative;
}

.auth-page__bg {
  inset: 0;
  opacity: 0.08;
  pointer-events: none;
  position: absolute;
}

.auth-page__bg img {
  height: 100%;
  object-fit: cover;
  width: 100%;
}

.language-dock {
  left: 20px;
  position: fixed;
  top: 20px;
  z-index: 5;
}

.language-dock__trigger {
  align-items: center;
  background: color-mix(in srgb, var(--color-white) 90%, transparent);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.language-dock__trigger svg {
  display: block;
  fill: currentcolor;
  height: 20px;
  width: 20px;
}

.language-dock__menu {
  backdrop-filter: blur(12px);
  background: color-mix(in srgb, var(--color-white) 94%, transparent);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  display: grid;
  gap: 6px;
  margin-top: 10px;
  min-width: 140px;
  padding: 8px;
}

.language-dock__option {
  background: transparent;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 13px;
  padding: 8px 10px;
  text-align: left;
}

.language-dock__option--active {
  background: rgba(16, 139, 150, 0.12);
  color: var(--color-primary-700);
  font-weight: 600;
}

.auth-main {
  align-items: center;
  display: grid;
  flex: 1;
  gap: 24px;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  margin: 0 auto;
  max-width: 1200px;
  padding: 72px 24px 32px;
  position: relative;
  width: 100%;
  z-index: 1;
}

.auth-panel {
  align-self: stretch;
  background: linear-gradient(160deg, rgba(16, 139, 150, 0.12), rgba(8, 145, 178, 0.06));
  border: 1px solid color-mix(in srgb, var(--color-primary-200) 60%, transparent);
  border-radius: 20px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 560px;
  padding: 34px 36px;
}

.auth-panel__badge {
  align-items: center;
  color: var(--color-text-secondary);
  display: inline-flex;
  font-size: 14px;
  font-weight: 700;
  gap: 8px;
}

.auth-panel__badge img {
  height: 28px;
  width: 28px;
}

.auth-panel__eyebrow {
  color: var(--color-primary-700);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 18px 0 0;
  text-transform: uppercase;
}

.auth-panel h1 {
  font-family: var(--font-serif);
  font-size: clamp(34px, 4.8vw, 52px);
  line-height: 1.1;
  margin: 10px 0 0;
}

.auth-panel p {
  color: var(--color-text-secondary);
  font-size: 15px;
  line-height: 1.8;
  margin: 14px 0 0;
  max-width: 440px;
}

.auth-panel__hero {
  align-self: center;
  display: block;
  margin-top: 16px;
  max-width: min(90%, 440px);
  width: 100%;
}

.auth-card {
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 18px;
  box-shadow: 0 20px 34px rgba(15, 23, 42, 0.12);
  display: flex;
  flex-direction: column;
  min-height: 560px;
  padding: 28px;
}

.auth-card__header h2 {
  font-family: var(--font-serif);
  font-size: clamp(34px, 4.5vw, 44px);
  line-height: 1.1;
  margin: 0;
}

.auth-card__header p {
  color: var(--color-text-muted);
  font-size: 14px;
  line-height: 1.6;
  margin: 10px 0 0;
}

.social-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: 22px;
}

.social-buttons__item {
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  color: #334155;
  cursor: pointer;
  display: inline-flex;
  font-size: var(--text-sm);
  font-weight: 600;
  gap: var(--space-3);
  justify-content: center;
  min-height: 42px;
  padding: 11px 17px;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
  width: 100%;
}

.social-buttons__item:hover {
  border-color: #cbd5e1;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.social-buttons__icon {
  align-items: center;
  display: inline-flex;
  height: 18px;
  justify-content: center;
  width: 18px;
}

.social-buttons__icon img {
  display: block;
  height: 18px;
  object-fit: contain;
  width: 18px;
}

.divider {
  align-items: center;
  color: #64748b;
  display: flex;
  font-size: 12px;
  font-weight: 500;
  justify-content: center;
  letter-spacing: 0.02em;
  margin-top: 20px;
  position: relative;
  text-transform: uppercase;
}

.divider::before,
.divider::after {
  border-top: 1px solid #e2e8f0;
  content: "";
  flex: 1;
}

.divider span {
  backdrop-filter: blur(4px);
  background: rgba(255, 255, 255, 0.5);
  padding: 0 var(--space-2);
}

.email-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: 16px;
}

.email-form__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.email-form__field > span {
  color: #334155;
  font-size: var(--text-sm);
  font-weight: 500;
  line-height: 20px;
}

.email-form__input-wrap {
  align-items: center;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  height: 47px;
  padding: 0 12px 0 17px;
}

.email-form__input-wrap:focus-within {
  border-color: rgba(16, 139, 150, 0.6);
  box-shadow: 0 0 0 2px rgba(16, 139, 150, 0.15);
}

.email-form__input-wrap input {
  background: transparent;
  border: 0;
  color: #334155;
  flex: 1;
  font-size: var(--text-sm);
  line-height: 1;
  outline: none;
}

.email-form__input-wrap input::placeholder {
  color: #94a3b8;
}

.email-form__field-icon {
  display: block;
  flex: 0 0 auto;
}

.email-form__field-icon--mail {
  height: 12px;
  width: 15px;
}

.email-form__field-icon--eye {
  height: 11.25px;
  width: 16.5px;
}

.email-form__submit {
  margin-top: 8px;
}

.card-footer {
  align-items: center;
  color: #64748b;
  display: flex;
  flex-direction: column;
  font-size: var(--text-sm);
  gap: var(--space-3);
  margin-top: auto;
  padding-top: 20px;
  text-align: center;
}

.card-footer a {
  color: #64748b;
  text-decoration: none;
}

.card-footer p {
  margin: 0;
}

.card-footer__switch {
  background: transparent;
  border: 0;
  color: var(--color-primary-600);
  cursor: pointer;
  font-size: inherit;
  font-weight: 600;
  padding: 0;
}

.card-footer a:hover,
.card-footer__switch:hover {
  text-decoration: underline;
}

.page-footer {
  padding: 0 24px 18px;
  position: relative;
  text-align: center;
  z-index: 1;
}

.page-footer p {
  color: #94a3b8;
  font-size: 12px;
  line-height: 16px;
  margin: 0;
}

@media (max-width: 1024px) {
  .auth-main {
    grid-template-columns: 1fr;
    max-width: 720px;
    padding-top: 84px;
  }

  .auth-panel {
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .auth-main {
    gap: 18px;
    padding: 76px 14px 24px;
  }

  .language-dock {
    left: 14px;
    top: 14px;
  }

  .auth-panel,
  .auth-card {
    border-radius: var(--radius-lg);
    min-height: auto;
    padding: 20px;
  }

  .auth-panel__hero {
    max-width: min(86%, 300px);
  }
}
</style>
