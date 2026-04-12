<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useTheme, type Theme } from "../composables/useTheme";
import { SUPPORTED_LOCALES, type SupportedLocale } from "../i18n";

const router = useRouter();
const { t, locale } = useI18n();
const { theme, setTheme } = useTheme();

const themeCycle: Theme[] = ["light", "dark", "system"];
const showLangDropdown = ref(false);

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

const closeDropdown = () => {
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

const goBack = () => {
  router.back();
};

onMounted(() => {
  document.addEventListener("click", closeDropdown);
  document.title = t("termsOfService.metaTitle");
});

onBeforeUnmount(() => {
  document.removeEventListener("click", closeDropdown);
});
</script>

<template>
  <main class="privacy-page">
    <header class="privacy-header">
      <button class="privacy-back" type="button" :aria-label="t('common.goBackAria')" @click="goBack">
        <span aria-hidden="true">&larr;</span>
        <span class="privacy-back__label">{{ t("termsOfService.back") }}</span>
      </button>
      <h1 class="privacy-header__title">{{ t("termsOfService.title") }}</h1>

      <div class="privacy-header__actions">
        <div class="header-icon-btn" @click.stop>
          <button
            class="icon-btn"
            type="button"
            :aria-expanded="showLangDropdown"
            :aria-label="`${t('landing.languageLabel')}: ${currentLangName}`"
            @click="toggleLang"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
          </button>
          <div v-if="showLangDropdown" class="header-dropdown" role="menu" :aria-label="t('landing.languageLabel')">
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

        <button
          class="icon-btn"
          type="button"
          :aria-label="`${t('settings.preferences.themeLabel')}: ${currentThemeLabel}`"
          @click="cycleTheme"
        >
          <svg v-if="theme === 'light'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="5" />
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
          </svg>
          <svg v-else-if="theme === 'dark'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
        </button>
      </div>
    </header>

    <article class="privacy-body">
      <p class="privacy-effective">{{ t("termsOfService.effectiveDate") }}</p>

      <section class="privacy-section">
        <h2>{{ t("termsOfService.section1Title") }}</h2>
        <p>{{ t("termsOfService.section1Body") }}</p>
        <ul>
          <li><strong>{{ t("termsOfService.section1Item1Title") }}</strong> {{ t("termsOfService.section1Item1Body") }}</li>
          <li><strong>{{ t("termsOfService.section1Item2Title") }}</strong> {{ t("termsOfService.section1Item2Body") }}</li>
          <li><strong>{{ t("termsOfService.section1Item3Title") }}</strong> {{ t("termsOfService.section1Item3Body") }}</li>
        </ul>
      </section>

      <section class="privacy-section">
        <h2>{{ t("termsOfService.section2Title") }}</h2>
        <p>{{ t("termsOfService.section2Body") }}</p>
        <ul>
          <li>{{ t("termsOfService.section2Item1") }}</li>
          <li>{{ t("termsOfService.section2Item2") }}</li>
          <li>{{ t("termsOfService.section2Item3") }}</li>
          <li>{{ t("termsOfService.section2Item4") }}</li>
        </ul>
        <p class="privacy-note">{{ t("termsOfService.section2Note") }}</p>
      </section>

      <section class="privacy-section">
        <h2>{{ t("termsOfService.section3Title") }}</h2>
        <p>{{ t("termsOfService.section3Body") }}</p>
        <ul>
          <li>{{ t("termsOfService.section3Item1") }}</li>
          <li>{{ t("termsOfService.section3Item2") }}</li>
          <li>{{ t("termsOfService.section3Item3") }}</li>
        </ul>
      </section>

      <section class="privacy-section">
        <h2>{{ t("termsOfService.section4Title") }}</h2>
        <p>{{ t("termsOfService.section4Body") }}</p>
        <h3>{{ t("termsOfService.section4_1Title") }}</h3>
        <ul>
          <li>{{ t("termsOfService.section4_1Item1") }}</li>
          <li>{{ t("termsOfService.section4_1Item2") }}</li>
          <li>{{ t("termsOfService.section4_1Item3") }}</li>
        </ul>
        <h3>{{ t("termsOfService.section4_2Title") }}</h3>
        <ul>
          <li>{{ t("termsOfService.section4_2Item1") }}</li>
          <li>{{ t("termsOfService.section4_2Item2") }}</li>
        </ul>
      </section>

      <section class="privacy-section">
        <h2>{{ t("termsOfService.section5Title") }}</h2>
        <p>{{ t("termsOfService.section5Body") }}</p>
        <ul>
          <li>{{ t("termsOfService.section5Item1") }}</li>
          <li>{{ t("termsOfService.section5Item2") }}</li>
          <li>{{ t("termsOfService.section5Item3") }}</li>
        </ul>
      </section>

      <section class="privacy-section">
        <h2>{{ t("termsOfService.section6Title") }}</h2>
        <p>{{ t("termsOfService.section6Body") }}</p>
        <ul>
          <li>{{ t("termsOfService.section6Item1") }}</li>
          <li>{{ t("termsOfService.section6Item2") }}</li>
          <li>{{ t("termsOfService.section6Item3") }}</li>
        </ul>
      </section>

      <section class="privacy-section">
        <h2>{{ t("termsOfService.section7Title") }}</h2>
        <p>{{ t("termsOfService.section7Body") }}</p>
        <ul>
          <li>{{ t("termsOfService.section7Item1") }}</li>
          <li>{{ t("termsOfService.section7Item2") }}</li>
        </ul>
      </section>

      <section class="privacy-section">
        <h2>{{ t("termsOfService.section8Title") }}</h2>
        <p>{{ t("termsOfService.section8Body1") }}</p>
        <ul>
          <li>
            <strong>{{ t("termsOfService.section8EmailLabel") }}</strong>
            huanyugezhishe@hotmail.com
          </li>
          <li>
            <strong>{{ t("termsOfService.section8CompanyLabel") }}</strong>
            {{ t("termsOfService.section8CompanyName") }}
          </li>
        </ul>
        <p>{{ t("termsOfService.section8Body2") }}</p>
      </section>

      <footer class="privacy-footer">
        <p>{{ t("termsOfService.footerEffective") }}</p>
      </footer>
    </article>
  </main>
</template>

<style scoped>
.privacy-page {
  background: var(--color-page-bg);
  min-height: 100vh;
  padding: 24px;
}

.privacy-header {
  align-items: center;
  background: linear-gradient(90deg, var(--color-primary-500), var(--color-primary-600));
  border-radius: var(--radius-lg);
  color: var(--color-surface);
  display: grid;
  gap: 14px;
  grid-template-columns: auto 1fr auto;
  margin: 0 auto;
  max-width: 980px;
  padding: 14px 16px;
}

.privacy-header__title {
  font-family: var(--font-serif);
  font-size: 26px;
  margin: 0;
  text-align: center;
}

.privacy-header__actions {
  align-items: center;
  display: flex;
  gap: 4px;
}

.header-icon-btn {
  align-items: center;
  display: inline-flex;
  position: relative;
}

.icon-btn {
  align-items: center;
  background: color-mix(in srgb, var(--color-surface) 16%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-surface) 52%, transparent);
  border-radius: var(--radius-sm);
  color: var(--color-surface);
  cursor: pointer;
  display: inline-flex;
  height: 36px;
  justify-content: center;
  transition: background-color 0.2s ease;
  width: 36px;
}

.icon-btn:hover {
  background: color-mix(in srgb, var(--color-surface) 28%, transparent);
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

.privacy-back {
  align-items: center;
  background: color-mix(in srgb, var(--color-surface) 16%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-surface) 52%, transparent);
  border-radius: var(--radius-sm);
  color: var(--color-surface);
  cursor: pointer;
  display: inline-flex;
  font-weight: 700;
  gap: 6px;
  min-height: 40px;
  padding: 0 12px;
}

.privacy-back:hover {
  background: color-mix(in srgb, var(--color-surface) 28%, transparent);
}

.privacy-back__label {
  font-size: 13px;
}

.privacy-body {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
  font-size: var(--text-md);
  line-height: 1.75;
  margin: 24px auto 0;
  max-width: 980px;
  padding: 32px;
}

.privacy-effective {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  margin: 0 0 24px;
}

.privacy-section {
  border-top: 1px solid var(--color-border-soft);
  margin-top: 28px;
  padding-top: 24px;
}

.privacy-section h2 {
  color: var(--color-text-strong);
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  margin: 0 0 12px;
}

.privacy-section h3 {
  color: var(--color-text-primary);
  font-size: var(--text-md);
  font-weight: 700;
  margin: 20px 0 8px;
}

.privacy-section p {
  margin: 8px 0;
}

.privacy-section ul,
.privacy-section ol {
  padding-left: 20px;
}

.privacy-section li {
  margin: 6px 0;
}

.privacy-note {
  background: var(--color-primary-50);
  border-left: 3px solid var(--color-primary-500);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: var(--text-sm);
  margin: 16px 0;
  padding: 12px 16px;
}

.privacy-footer {
  border-top: 1px solid var(--color-border);
  font-size: var(--text-sm);
  margin-top: 40px;
  padding-top: 20px;
  text-align: center;
}

.privacy-footer p {
  color: var(--color-text-muted);
  font-style: italic;
}

@media (max-width: 768px) {
  .privacy-body {
    padding: 20px 16px;
  }
}
</style>