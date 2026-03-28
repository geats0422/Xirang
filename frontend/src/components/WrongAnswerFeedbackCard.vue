<script setup lang="ts">
defineProps<{
  title: string;
  correctAnswerText?: string | null;
  explanation?: string | null;
  sourceLocator?: string | null;
  supportingExcerpt?: string | null;
}>();
</script>

<template>
  <div class="wrong-feedback">
    <p class="wrong-feedback__title">{{ title }}</p>
    <p v-if="correctAnswerText" class="wrong-feedback__line">
      正确答案：{{ correctAnswerText }}
    </p>
    <p v-if="explanation" class="wrong-feedback__line">
      解析：{{ explanation }}
    </p>
    <p v-if="sourceLocator" class="wrong-feedback__meta">
      来源：{{ sourceLocator }}
    </p>
    <p v-if="supportingExcerpt" class="wrong-feedback__meta">
      摘录：{{ supportingExcerpt }}
    </p>
  </div>
</template>

<style scoped>
.wrong-feedback {
  text-align: left;
}

.wrong-feedback__title,
.wrong-feedback__line,
.wrong-feedback__meta {
  margin: 0;
}

.wrong-feedback__line {
  margin-top: 6px;
}

.wrong-feedback__meta {
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  margin-top: 4px;
}
</style>
