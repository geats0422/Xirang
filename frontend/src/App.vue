<script setup lang="ts">
import { onMounted } from "vue";
import { RouterView } from "vue-router";
import { useTheme } from "./composables/useTheme";
import { i18n, SUPPORTED_LOCALES, type SupportedLocale } from "./i18n";

const LANGUAGE_STORAGE_KEY = "xirang:language";

const { initTheme } = useTheme();
initTheme();

const restoreLanguagePreference = () => {
  if (typeof window === "undefined") {
    return;
  }

  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (!stored || !(SUPPORTED_LOCALES as readonly string[]).includes(stored)) {
    return;
  }

  const locale = stored as SupportedLocale;
  i18n.global.locale.value = locale as typeof i18n.global.locale.value;
  document.documentElement.lang = locale;
};

onMounted(() => {
  restoreLanguagePreference();
});
</script>

<template>
  <RouterView />
</template>
