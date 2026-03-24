<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute } from "vue-router";

const route = useRoute();
const { t } = useI18n();

const PRIVACY_POLICY_PATH = "/settings/privacy-policy";
const USER_AGREEMENT_PATH = "/settings/user-agreement";

const pageMeta = computed(() => {
  if (route.path === PRIVACY_POLICY_PATH) {
    return {
      title: t("settingsDoc.privacyPolicy.title"),
      body: t("settingsDoc.privacyPolicy.body"),
    };
  }
  if (route.path === USER_AGREEMENT_PATH) {
    return {
      title: t("settingsDoc.userAgreement.title"),
      body: t("settingsDoc.userAgreement.body"),
    };
  }
  return {
    title: t("settingsDoc.helpCenter.title"),
    body: t("settingsDoc.helpCenter.body"),
  };
});

onMounted(() => {
  document.title = t("settingsDoc.metaTitle", { title: pageMeta.value.title });
});
</script>

<template>
  <main class="doc-page">
    <section class="doc-card">
      <h1>{{ pageMeta.title }}</h1>
      <p>{{ pageMeta.body }}</p>
    </section>
  </main>
</template>

<style scoped>
.doc-page {
  background: linear-gradient(180deg, #f7faf9, #edf3f1);
  min-height: 100vh;
  padding: 26px;
}

.doc-card {
  background: #ffffff;
  border: 1px solid #e2ebe7;
  border-radius: 14px;
  margin: 0 auto;
  max-width: 860px;
  padding: 24px;
}

.doc-card h1 {
  color: #1f2937;
  font-family: var(--font-serif);
  font-size: 36px;
  margin: 0;
}

.doc-card p {
  color: #4b5563;
  font-size: 16px;
  line-height: 1.7;
  margin: 14px 0 0;
}
</style>
