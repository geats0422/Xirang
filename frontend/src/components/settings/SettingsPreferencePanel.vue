<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useTheme, type Theme } from "../../composables/useTheme";
import { useScholarData } from "../../composables/useScholarData";
import { SUPPORTED_LOCALES, type SupportedLocale } from "../../i18n";

type PreferenceRow = {
  icon: string;
  title: string;
  description: string;
  kind: "theme" | "select" | "toggle";
  value?: string;
  enabled?: boolean;
};

defineProps<{
  rows: PreferenceRow[];
}>();

type ToggleKey = "sound" | "haptic" | "reminder";

const TOGGLE_STORAGE_KEY = "xirang-toggle-states";
const themeOptions: Theme[] = ["light", "dark", "system"];
const defaultToggleStates: Record<ToggleKey, boolean> = {
  sound: true,
  haptic: true,
  reminder: false,
};

const { t, locale } = useI18n();
const { theme, setTheme } = useTheme();
const { applyLanguage } = useScholarData();

const showLangDropdown = ref(false);
const languageSelectRef = ref<HTMLElement | null>(null);
const toggleStates = ref<Record<ToggleKey, boolean>>({ ...defaultToggleStates });

const currentLangLabel = computed(() => {
  const key = `settings.localeNames.${locale.value}`;
  const translated = t(key);
  return translated === key ? locale.value : translated;
});

const resolveToggleKey = (row: PreferenceRow): ToggleKey => {
  const normalized = row.title.toLowerCase();
  if (normalized.includes("sound")) {
    return "sound";
  }
  if (normalized.includes("haptic")) {
    return "haptic";
  }
  return "reminder";
};

const getToggleEnabled = (row: PreferenceRow) => {
  return toggleStates.value[resolveToggleKey(row)] ?? Boolean(row.enabled);
};

const loadToggleStates = () => {
  if (typeof window === "undefined") {
    return;
  }

  const saved = window.localStorage.getItem(TOGGLE_STORAGE_KEY);
  if (!saved) {
    return;
  }

  try {
    const parsed = JSON.parse(saved) as Partial<Record<ToggleKey, boolean>>;
    toggleStates.value = {
      ...defaultToggleStates,
      ...parsed,
    };
  } catch {
    toggleStates.value = { ...defaultToggleStates };
  }
};

const saveToggleStates = () => {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(TOGGLE_STORAGE_KEY, JSON.stringify(toggleStates.value));
};

const handleToggle = (row: PreferenceRow) => {
  const key = resolveToggleKey(row);
  toggleStates.value[key] = !toggleStates.value[key];
  saveToggleStates();
};

const handleThemeClick = (nextTheme: Theme) => {
  setTheme(nextTheme);
};

const localeLabel = (value: SupportedLocale) => {
  const key = `settings.localeNames.${value}`;
  const translated = t(key);
  return translated === key ? value : translated;
};

const toggleLangDropdown = () => {
  showLangDropdown.value = !showLangDropdown.value;
};

const selectLanguage = (lang: SupportedLocale) => {
  applyLanguage(lang);
  showLangDropdown.value = false;
};

const handleDocumentClick = (event: MouseEvent) => {
  const target = event.target;
  if (!(target instanceof Node)) {
    return;
  }

  if (!languageSelectRef.value?.contains(target)) {
    showLangDropdown.value = false;
  }
};

const handleDocumentKeydown = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    showLangDropdown.value = false;
  }
};

onMounted(() => {
  loadToggleStates();
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleDocumentKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
  document.removeEventListener("keydown", handleDocumentKeydown);
});
</script>

<template>
  <section class="panel">
    <div class="panel__header">
      <span class="panel__icon">☷</span>
      <h3>Game Preferences</h3>
    </div>

    <div class="prefs-list">
      <div v-for="row in rows" :key="row.title" class="prefs-row">
        <div class="prefs-row__left">
          <span class="prefs-row__icon">{{ row.icon }}</span>
          <div>
            <p class="prefs-row__title">{{ row.title }}</p>
            <p class="prefs-row__desc">{{ row.description }}</p>
          </div>
        </div>

        <div v-if="row.kind === 'theme'" class="segmented" role="group" aria-label="Theme">
          <button
            v-for="themeOption in themeOptions"
            :key="themeOption"
            class="segmented__btn"
            :class="{ 'segmented__btn--active': theme === themeOption }"
            type="button"
            @click="handleThemeClick(themeOption)"
          >
            {{ t(`settings.preferences.${themeOption}`) }}
          </button>
        </div>

        <div v-else-if="row.kind === 'select'" ref="languageSelectRef" class="lang-select">
          <button class="select-btn" type="button" :aria-expanded="showLangDropdown" @click="toggleLangDropdown">
            <span>{{ currentLangLabel }}</span>
            <span>▾</span>
          </button>

          <div v-if="showLangDropdown" class="dropdown-menu" role="menu" aria-label="Language">
            <button
              v-for="lang in SUPPORTED_LOCALES"
              :key="lang"
              class="dropdown-item"
              :class="{ 'dropdown-item--active': locale === lang }"
              type="button"
              role="menuitemradio"
              :aria-checked="locale === lang"
              @click="selectLanguage(lang)"
            >
              {{ localeLabel(lang) }}
            </button>
          </div>
        </div>

        <button
          v-else
          class="toggle"
          :class="{ 'toggle--on': getToggleEnabled(row) }"
          type="button"
          @click="handleToggle(row)"
        >
          <span />
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-top: 16px;
  overflow: visible;
}

.panel__header {
  align-items: center;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  gap: 10px;
  padding: 14px 16px;
}

.panel__icon {
  color: var(--color-text-muted);
  font-size: 16px;
}

.panel__header h3 {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 24px;
  margin: 0;
}

.prefs-list {
  display: grid;
}

.prefs-row {
  align-items: center;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  padding: 14px 16px;
}

.prefs-row:last-child {
  border-bottom: 0;
}

.prefs-row__left {
  align-items: center;
  display: flex;
  gap: 14px;
}

.prefs-row__icon {
  align-items: center;
  background: var(--color-primary-50);
  border-radius: 999px;
  color: var(--color-primary-600);
  display: inline-flex;
  font-size: 14px;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.prefs-row__title {
  color: var(--color-text-dark);
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.prefs-row__desc {
  color: var(--color-text-muted);
  font-size: 12px;
  margin: 2px 0 0;
}

.segmented {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: inline-flex;
  gap: 4px;
  padding: 4px;
}

.segmented__btn {
  background: transparent;
  border: 0;
  border-radius: 6px;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  height: 28px;
  min-width: 52px;
  padding: 0 10px;
}

.segmented__btn--active {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-dark);
}

.select-btn {
  align-items: center;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  font-size: 13px;
  font-weight: 600;
  gap: 12px;
  height: 38px;
  justify-content: space-between;
  min-width: 160px;
  padding: 0 12px;
}

.lang-select {
  position: relative;
}

.dropdown-menu {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  left: 0;
  min-width: 180px;
  padding: 6px 0;
  position: absolute;
  top: calc(100% + 6px);
  z-index: 9999;
}

.dropdown-item {
  background: none;
  border: 0;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: block;
  font-size: 13px;
  font-weight: 500;
  padding: 10px 14px;
  text-align: left;
  width: 100%;
}

.dropdown-item:hover {
  background: var(--color-primary-50);
}

.dropdown-item--active {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  font-weight: 600;
}

.toggle {
  background: #d9dee2;
  border: 0;
  border-radius: 999px;
  cursor: pointer;
  height: 20px;
  padding: 2px;
  width: 36px;
}

.toggle span {
  background: var(--color-surface);
  border-radius: 999px;
  display: block;
  height: 16px;
  transition: transform 0.2s ease;
  width: 16px;
}

.toggle--on {
  background: #2a99a4;
}

.toggle--on span {
  transform: translateX(16px);
}

@media (max-width: 768px) {
  .prefs-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}
</style>
