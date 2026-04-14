<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  profileName?: string | null;
  profileLevel?: string | null;
}>();

const { t } = useI18n();

const displayName = computed(() => props.profileName?.trim() || "");
const displayLevel = computed(() => props.profileLevel?.trim() || "");

defineEmits<{
  editProfile: [];
}>();
</script>

<template>
  <section class="profile-hero">
    <div class="profile-hero__avatar-wrap">
      <div class="profile-hero__avatar">🧝</div>
      <span class="profile-hero__level">{{ displayLevel }}</span>
    </div>

    <div class="profile-hero__body">
      <div class="profile-hero__name-row">
        <h2>{{ displayName }}</h2>
        <span class="verified">✓</span>
      </div>
      <span class="tier-pill">{{ t("settings.profile.tier") }}</span>
      <p>{{ t("settings.profile.bio") }}</p>
    </div>

    <button class="ghost-btn" type="button" @click="$emit('editProfile')">{{ t("settings.profile.edit") }}</button>
  </section>
</template>

<style scoped>
.profile-hero {
  align-items: flex-start;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: grid;
  gap: 18px;
  grid-template-columns: 96px minmax(0, 1fr) auto;
  margin-top: 18px;
  padding: 18px;
  position: relative;
}

.profile-hero__avatar-wrap {
  position: relative;
}

.profile-hero__avatar {
  align-items: center;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 50%;
  display: inline-flex;
  font-size: 48px;
  height: 96px;
  justify-content: center;
  width: 96px;
}

.profile-hero__level {
  background: var(--color-primary-500);
  border-radius: 999px;
  bottom: -5px;
  color: var(--color-surface);
  font-size: 10px;
  font-weight: 700;
  left: 50%;
  padding: 3px 8px;
  position: absolute;
  transform: translateX(-50%);
}

.profile-hero__name-row {
  align-items: center;
  display: flex;
  gap: 8px;
}

.profile-hero__name-row h2 {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 32px;
  line-height: 1;
  margin: 0;
}

.verified {
  color: var(--color-primary-500);
  font-size: 16px;
  font-weight: 700;
}

.tier-pill {
  background: var(--color-primary-50);
  border-radius: 4px;
  color: var(--color-primary-600);
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  margin-top: 8px;
  padding: 3px 8px;
}

.profile-hero__body p {
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.45;
  margin: 10px 0 0;
  max-width: 470px;
}

.ghost-btn {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  height: 38px;
  padding: 0 16px;
}

@media (max-width: 768px) {
  .profile-hero {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .ghost-btn {
    justify-self: start;
  }
}
</style>
