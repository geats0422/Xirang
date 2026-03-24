<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
  accent?: "green" | "cyan";
}>();
</script>

<template>
  <article class="feature-card">
    <div class="feature-card__blob" :class="`feature-card__blob--${accent ?? 'green'}`" />
    <div class="feature-card__icon" :class="`feature-card__icon--${accent ?? 'green'}`">
      <slot name="icon">✦</slot>
    </div>
    <h3 class="feature-card__title">{{ title }}</h3>
    <p class="feature-card__description">{{ description }}</p>
  </article>
</template>

<style scoped>
.feature-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  min-height: 256px;
  overflow: hidden;
  padding: 32px;
  position: relative;
}

.feature-card__blob {
  border-radius: var(--radius-pill);
  filter: blur(12px);
  height: 96px;
  position: absolute;
  right: -16px;
  top: -16px;
  width: 96px;
}

.feature-card__blob--green {
  background: var(--color-primary-50);
}

.feature-card__blob--cyan {
  background: var(--color-cyan-50);
}

.feature-card__icon {
  align-items: center;
  border-radius: var(--radius-md);
  color: var(--color-primary-700);
  display: inline-flex;
  font-size: 20px;
  justify-content: center;
  margin-bottom: 32px;
  min-height: 48px;
  min-width: 48px;
  position: relative;
  z-index: 1;
}

.feature-card__icon--green {
  background: var(--color-primary-50);
}

.feature-card__icon--cyan {
  background: var(--color-cyan-50);
}

.feature-card__title {
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
}

.feature-card__description {
  color: var(--color-text-muted);
  font-size: 16px;
  line-height: 1.6;
  margin: 12px 0 0;
}

@media (max-width: 768px) {
  .feature-card {
    min-height: 220px;
    padding: 24px;
  }

  .feature-card__title {
    font-size: 24px;
  }
}
</style>
