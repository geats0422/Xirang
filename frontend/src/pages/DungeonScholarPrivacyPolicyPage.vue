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
  document.title = t("privacyPolicy.metaTitle");
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
        <span class="privacy-back__label">{{ t("privacyPolicy.back") }}</span>
      </button>
      <h1 class="privacy-header__title">{{ t("privacyPolicy.title") }}</h1>

      <div class="privacy-header__actions">
        <!-- Language switch -->
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

        <!-- Theme switch -->
        <button
          class="icon-btn"
          type="button"
          :aria-label="`${t('settings.preferences.themeLabel')}: ${currentThemeLabel}`"
          @click="cycleTheme"
        >
          <!-- Light: sun -->
          <svg v-if="theme === 'light'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="5" />
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
          </svg>
          <!-- Dark: moon -->
          <svg v-else-if="theme === 'dark'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
          <!-- System: laptop -->
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
        </button>
      </div>
    </header>

    <article class="privacy-body">
      <!-- Effective date -->
      <p class="privacy-effective">{{ t("privacyPolicy.effectiveDate") }}</p>

      <!-- Section 1: Who we are -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section1Title") }}</h2>
        <p>{{ t("privacyPolicy.section1Body") }}</p>
        <p>
          <strong>{{ t("privacyPolicy.section1Company") }}</strong>
          {{ t("privacyPolicy.section1CompanyDesc") }}
        </p>
        <ul>
          <li>
            <strong>{{ t("privacyPolicy.section1EmailLabel") }}</strong>
            huanyugezhishe@hotmail.com
          </li>
        </ul>
      </section>

      <!-- Section 2: Information we collect -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section2Title") }}</h2>
        <h3>{{ t("privacyPolicy.section2_1Title") }}</h3>
        <table class="privacy-table">
          <thead>
            <tr>
              <th>{{ t("privacyPolicy.colInfoType") }}</th>
              <th>{{ t("privacyPolicy.colContent") }}</th>
              <th>{{ t("privacyPolicy.colPurpose") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ t("privacyPolicy.section2_1Row1Type") }}</td>
              <td>{{ t("privacyPolicy.section2_1Row1Content") }}</td>
              <td>{{ t("privacyPolicy.section2_1Row1Purpose") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section2_1Row2Type") }}</td>
              <td>{{ t("privacyPolicy.section2_1Row2Content") }}</td>
              <td>{{ t("privacyPolicy.section2_1Row2Purpose") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section2_1Row3Type") }}</td>
              <td>{{ t("privacyPolicy.section2_1Row3Content") }}</td>
              <td>{{ t("privacyPolicy.section2_1Row3Purpose") }}</td>
            </tr>
          </tbody>
        </table>
        <p class="privacy-note">{{ t("privacyPolicy.section2_1Note") }}</p>

        <h3>{{ t("privacyPolicy.section2_2Title") }}</h3>
        <table class="privacy-table">
          <thead>
            <tr>
              <th>{{ t("privacyPolicy.colInfoType") }}</th>
              <th>{{ t("privacyPolicy.colContent") }}</th>
              <th>{{ t("privacyPolicy.colPurpose") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ t("privacyPolicy.section2_2Row1Type") }}</td>
              <td>{{ t("privacyPolicy.section2_2Row1Content") }}</td>
              <td>{{ t("privacyPolicy.section2_2Row1Purpose") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section2_2Row2Type") }}</td>
              <td>{{ t("privacyPolicy.section2_2Row2Content") }}</td>
              <td>{{ t("privacyPolicy.section2_2Row2Purpose") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section2_2Row3Type") }}</td>
              <td>{{ t("privacyPolicy.section2_2Row3Content") }}</td>
              <td>{{ t("privacyPolicy.section2_2Row3Purpose") }}</td>
            </tr>
          </tbody>
        </table>

        <h3>{{ t("privacyPolicy.section2_3Title") }}</h3>
        <ul>
          <li>{{ t("privacyPolicy.section2_3Item1") }}</li>
          <li>{{ t("privacyPolicy.section2_3Item2") }}</li>
          <li>{{ t("privacyPolicy.section2_3Item3") }}</li>
          <li>{{ t("privacyPolicy.section2_3Item4") }}</li>
        </ul>
      </section>

      <!-- Section 3: How we use your information -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section3Title") }}</h2>
        <ol>
          <li><strong>{{ t("privacyPolicy.section3Item1Title") }}</strong> {{ t("privacyPolicy.section3Item1Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section3Item2Title") }}</strong> {{ t("privacyPolicy.section3Item2Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section3Item3Title") }}</strong> {{ t("privacyPolicy.section3Item3Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section3Item4Title") }}</strong> {{ t("privacyPolicy.section3Item4Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section3Item5Title") }}</strong> {{ t("privacyPolicy.section3Item5Body") }}</li>
        </ol>
        <p class="privacy-note">{{ t("privacyPolicy.section3Note") }}</p>
      </section>

      <!-- Section 4: AI Services -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section4Title") }}</h2>
        <h3>{{ t("privacyPolicy.section4_1Title") }}</h3>
        <ul>
          <li>{{ t("privacyPolicy.section4_1Provider1") }}</li>
          <li>{{ t("privacyPolicy.section4_1Provider2") }}</li>
          <li>{{ t("privacyPolicy.section4_1Provider3") }}</li>
        </ul>
        <h3>{{ t("privacyPolicy.section4_2Title") }}</h3>
        <ul>
          <li>{{ t("privacyPolicy.section4_2Item1") }}</li>
          <li>{{ t("privacyPolicy.section4_2Item2") }}</li>
          <li>{{ t("privacyPolicy.section4_2Item3") }}</li>
        </ul>
        <h3>{{ t("privacyPolicy.section4_3Title") }}</h3>
        <p class="privacy-note privacy-note--important">{{ t("privacyPolicy.section4_3Body") }}</p>
      </section>

      <!-- Section 5: Information sharing -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section5Title") }}</h2>
        <p>{{ t("privacyPolicy.section5Intro") }}</p>
        <h3>{{ t("privacyPolicy.section5_1Title") }}</h3>
        <table class="privacy-table">
          <thead>
            <tr>
              <th>{{ t("privacyPolicy.colProvider") }}</th>
              <th>{{ t("privacyPolicy.colServiceType") }}</th>
              <th>{{ t("privacyPolicy.colSharedData") }}</th>
              <th>{{ t("privacyPolicy.colDataLocation") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Render</td>
              <td>{{ t("privacyPolicy.section5_1Row1Service") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row1Data") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row1Location") }}</td>
            </tr>
            <tr>
              <td>Vercel</td>
              <td>{{ t("privacyPolicy.section5_1Row2Service") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row2Data") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row2Location") }}</td>
            </tr>
            <tr>
              <td>Supabase</td>
              <td>{{ t("privacyPolicy.section5_1Row3Service") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row3Data") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row3Location") }}</td>
            </tr>
            <tr>
              <td>Cloudflare R2</td>
              <td>{{ t("privacyPolicy.section5_1Row4Service") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row4Data") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row4Location") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section5_1Row5Provider") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row5Service") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row5Data") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row5Location") }}</td>
            </tr>
            <tr>
              <td>Google Analytics</td>
              <td>{{ t("privacyPolicy.section5_1Row6Service") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row6Data") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row6Location") }}</td>
            </tr>
            <tr>
              <td>Resend</td>
              <td>{{ t("privacyPolicy.section5_1Row7Service") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row7Data") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row7Location") }}</td>
            </tr>
            <tr>
              <td>Creem</td>
              <td>{{ t("privacyPolicy.section5_1Row8Service") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row8Data") }}</td>
              <td>{{ t("privacyPolicy.section5_1Row8Location") }}</td>
            </tr>
          </tbody>
        </table>
        <p class="privacy-note">{{ t("privacyPolicy.section5_1Note") }}</p>
        <h3>{{ t("privacyPolicy.section5_2Title") }}</h3>
        <ul>
          <li>{{ t("privacyPolicy.section5_2Item1") }}</li>
          <li>{{ t("privacyPolicy.section5_2Item2") }}</li>
          <li>{{ t("privacyPolicy.section5_2Item3") }}</li>
        </ul>
      </section>

      <!-- Section 6: Data storage & security -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section6Title") }}</h2>
        <h3>{{ t("privacyPolicy.section6_1Title") }}</h3>
        <p>{{ t("privacyPolicy.section6_1Body") }}</p>
        <h3>{{ t("privacyPolicy.section6_2Title") }}</h3>
        <ul>
          <li>{{ t("privacyPolicy.section6_2Item1") }}</li>
          <li>{{ t("privacyPolicy.section6_2Item2") }}</li>
          <li>{{ t("privacyPolicy.section6_2Item3") }}</li>
        </ul>
        <h3>{{ t("privacyPolicy.section6_3Title") }}</h3>
        <ul>
          <li><strong>{{ t("privacyPolicy.section6_3Item1Title") }}</strong> {{ t("privacyPolicy.section6_3Item1Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section6_3Item2Title") }}</strong> {{ t("privacyPolicy.section6_3Item2Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section6_3Item3Title") }}</strong> {{ t("privacyPolicy.section6_3Item3Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section6_3Item4Title") }}</strong> {{ t("privacyPolicy.section6_3Item4Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section6_3Item5Title") }}</strong> {{ t("privacyPolicy.section6_3Item5Body") }}</li>
        </ul>
        <h3>{{ t("privacyPolicy.section6_4Title") }}</h3>
        <p>{{ t("privacyPolicy.section6_4Body") }}</p>
      </section>

      <!-- Section 7: Data retention & deletion -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section7Title") }}</h2>
        <h3>{{ t("privacyPolicy.section7_1Title") }}</h3>
        <ul>
          <li>{{ t("privacyPolicy.section7_1Item1") }}</li>
          <li>{{ t("privacyPolicy.section7_1Item2") }}</li>
          <li>{{ t("privacyPolicy.section7_1Item3") }}</li>
        </ul>
        <h3>{{ t("privacyPolicy.section7_2Title") }}</h3>
        <ol>
          <li><strong>{{ t("privacyPolicy.section7_2Item1Title") }}</strong> {{ t("privacyPolicy.section7_2Item1Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section7_2Item2Title") }}</strong> {{ t("privacyPolicy.section7_2Item2Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section7_2Item3Title") }}</strong> {{ t("privacyPolicy.section7_2Item3Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section7_2Item4Title") }}</strong> {{ t("privacyPolicy.section7_2Item4Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section7_2Item5Title") }}</strong> {{ t("privacyPolicy.section7_2Item5Body") }}</li>
        </ol>
        <p class="privacy-note">{{ t("privacyPolicy.section7_2Note") }}</p>
      </section>

      <!-- Section 8: Copyright -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section8Title") }}</h2>
        <p>{{ t("privacyPolicy.section8Body") }}</p>
      </section>

      <!-- Section 9: Minors -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section9Title") }}</h2>
        <p>{{ t("privacyPolicy.section9Body1") }}</p>
        <ul>
          <li>{{ t("privacyPolicy.section9Item1") }}</li>
          <li>{{ t("privacyPolicy.section9Item2") }}</li>
        </ul>
        <p>{{ t("privacyPolicy.section9Body2") }}</p>
      </section>

      <!-- Section 10: Cookie policy -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section10Title") }}</h2>
        <h3>{{ t("privacyPolicy.section10_1Title") }}</h3>
        <table class="privacy-table">
          <thead>
            <tr>
              <th>{{ t("privacyPolicy.colCookieType") }}</th>
              <th>{{ t("privacyPolicy.colCookieNamePurpose") }}</th>
              <th>{{ t("privacyPolicy.colNecessity") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ t("privacyPolicy.section10_1Row1Type") }}</td>
              <td>{{ t("privacyPolicy.section10_1Row1Name") }}</td>
              <td>{{ t("privacyPolicy.section10_1Row1Necessity") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section10_1Row2Type") }}</td>
              <td>{{ t("privacyPolicy.section10_1Row2Name") }}</td>
              <td>{{ t("privacyPolicy.section10_1Row2Necessity") }}</td>
            </tr>
          </tbody>
        </table>
        <h3>{{ t("privacyPolicy.section10_2Title") }}</h3>
        <p>{{ t("privacyPolicy.section10_2Body") }}</p>
      </section>

      <!-- Section 11: Your rights -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section11Title") }}</h2>
        <table class="privacy-table">
          <thead>
            <tr>
              <th>{{ t("privacyPolicy.colRight") }}</th>
              <th>{{ t("privacyPolicy.colDescription") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ t("privacyPolicy.section11Row1Right") }}</td>
              <td>{{ t("privacyPolicy.section11Row1Desc") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section11Row2Right") }}</td>
              <td>{{ t("privacyPolicy.section11Row2Desc") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section11Row3Right") }}</td>
              <td>{{ t("privacyPolicy.section11Row3Desc") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section11Row4Right") }}</td>
              <td>{{ t("privacyPolicy.section11Row4Desc") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section11Row5Right") }}</td>
              <td>{{ t("privacyPolicy.section11Row5Desc") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section11Row6Right") }}</td>
              <td>{{ t("privacyPolicy.section11Row6Desc") }}</td>
            </tr>
            <tr>
              <td>{{ t("privacyPolicy.section11Row7Right") }}</td>
              <td>{{ t("privacyPolicy.section11Row7Desc") }}</td>
            </tr>
          </tbody>
        </table>
        <p>
          {{ t("privacyPolicy.section11Contact") }}
        </p>
        <p>{{ t("privacyPolicy.section11ResponseTime") }}</p>
      </section>

      <!-- Section 12: Policy updates -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section12Title") }}</h2>
        <ul>
          <li><strong>{{ t("privacyPolicy.section12Item1Title") }}</strong> {{ t("privacyPolicy.section12Item1Body") }}</li>
          <li><strong>{{ t("privacyPolicy.section12Item2Title") }}</strong> {{ t("privacyPolicy.section12Item2Body") }}</li>
          <li>{{ t("privacyPolicy.section12Item3") }}</li>
        </ul>
      </section>

      <!-- Section 13: Disclaimer -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section13Title") }}</h2>
        <h3>{{ t("privacyPolicy.section13_1Title") }}</h3>
        <p>{{ t("privacyPolicy.section13_1Body") }}</p>
        <h3>{{ t("privacyPolicy.section13_2Title") }}</h3>
        <ul>
          <li>{{ t("privacyPolicy.section13_2Item1") }}</li>
          <li>{{ t("privacyPolicy.section13_2Item2") }}</li>
          <li>{{ t("privacyPolicy.section13_2Item3") }}</li>
          <li>{{ t("privacyPolicy.section13_2Item4") }}</li>
        </ul>
        <h3>{{ t("privacyPolicy.section13_3Title") }}</h3>
        <p>{{ t("privacyPolicy.section13_3Body") }}</p>
      </section>

      <!-- Section 14: Applicable law -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section14Title") }}</h2>
        <ul>
          <li>{{ t("privacyPolicy.section14Item1") }}</li>
          <li>{{ t("privacyPolicy.section14Item2") }}</li>
          <li>{{ t("privacyPolicy.section14Item3") }}</li>
        </ul>
      </section>

      <!-- Section 15: Regulatory statement -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section15Title") }}</h2>
        <ul>
          <li>{{ t("privacyPolicy.section15Item1") }}</li>
          <li>{{ t("privacyPolicy.section15Item2") }}</li>
          <li>{{ t("privacyPolicy.section15Item3") }}</li>
          <li>{{ t("privacyPolicy.section15Item4") }}</li>
        </ul>
        <p class="privacy-note">{{ t("privacyPolicy.section15Note") }}</p>
      </section>

      <!-- Section 16: Contact -->
      <section class="privacy-section">
        <h2>{{ t("privacyPolicy.section16Title") }}</h2>
        <ul>
          <li>
            <strong>{{ t("privacyPolicy.section16EmailLabel") }}</strong>
            huanyugezhishe@hotmail.com
          </li>
          <li>
            <strong>{{ t("privacyPolicy.section16CompanyLabel") }}</strong>
            {{ t("privacyPolicy.section16CompanyName") }}
          </li>
        </ul>
        <p>{{ t("privacyPolicy.section16ResponseTime") }}</p>
      </section>

      <footer class="privacy-footer">
        <p>{{ t("privacyPolicy.footerEffective") }}</p>
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

.privacy-table {
  border-collapse: collapse;
  font-size: var(--text-sm);
  margin: 16px 0;
  width: 100%;
}

.privacy-table th {
  background: var(--color-surface-alt);
  border-bottom: 2px solid var(--color-border);
  color: var(--color-text-strong);
  font-weight: 700;
  padding: 10px 12px;
  text-align: left;
}

.privacy-table td {
  border-bottom: 1px solid var(--color-border-soft);
  padding: 10px 12px;
  vertical-align: top;
}

.privacy-table tbody tr:hover {
  background: var(--color-surface-alt);
}

.privacy-note {
  background: var(--color-primary-50);
  border-left: 3px solid var(--color-primary-500);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: var(--text-sm);
  margin: 16px 0;
  padding: 12px 16px;
}

.privacy-note--important {
  background: color-mix(in srgb, var(--color-warm-beige) 60%, var(--color-surface) 40%);
  border-left-color: var(--color-soft-brown);
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

  .privacy-table {
    font-size: 12px;
  }

  .privacy-table th,
  .privacy-table td {
    padding: 8px 6px;
  }
}
</style>