<script setup lang="ts">
import WrongAnswerFeedbackCard from "./WrongAnswerFeedbackCard.vue";
import type { MistakeReviewItem } from "../api/runs";

defineProps<{
  visible: boolean;
  items: MistakeReviewItem[];
}>();

const emit = defineEmits<{
  close: [];
}>();
</script>

<template>
  <transition name="mistake-review-fade">
    <div v-if="visible" class="mistake-review-overlay" @click="emit('close')">
      <section class="mistake-review-panel" @click.stop>
        <header class="mistake-review-panel__header">
          <div>
            <h2>Review Mistakes</h2>
            <p>复盘本局答错的题目、正确答案与出处。</p>
          </div>
          <button class="mistake-review-panel__close" type="button" @click="emit('close')">✕</button>
        </header>

        <div v-if="items.length === 0" class="mistake-review-empty">
          本局没有错题。
        </div>

        <ol v-else class="mistake-review-list">
          <li v-for="(item, index) in items" :key="item.question_id" class="mistake-review-item">
            <p class="mistake-review-item__index">错题 {{ index + 1 }}</p>
            <h3 class="mistake-review-item__question">{{ item.question_text }}</h3>
            <p v-if="item.selected_answer_text" class="mistake-review-item__selected">
              你的答案：{{ item.selected_answer_text }}
            </p>
            <WrongAnswerFeedbackCard
              title="查看正确答案与解析"
              :correct-answer-text="item.correct_answer_text"
              :explanation="item.explanation"
              :source-locator="item.source_locator"
              :supporting-excerpt="item.supporting_excerpt"
            />
          </li>
        </ol>
      </section>
    </div>
  </transition>
</template>

<style scoped>
.mistake-review-overlay {
  align-items: center;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  background: rgba(17, 24, 39, 0.44);
  display: flex;
  inset: 0;
  justify-content: center;
  padding: 24px;
  position: fixed;
  z-index: 90;
}

.mistake-review-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  box-shadow: var(--shadow-elevated);
  max-height: min(88vh, 920px);
  max-width: 760px;
  overflow: auto;
  padding: 24px;
  width: min(760px, 100%);
}

.mistake-review-panel__header {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.mistake-review-panel__header h2,
.mistake-review-panel__header p,
.mistake-review-item__index,
.mistake-review-item__question,
.mistake-review-item__selected {
  margin: 0;
}

.mistake-review-panel__header p {
  color: var(--color-text-muted);
  margin-top: 6px;
}

.mistake-review-panel__close {
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 18px;
}

.mistake-review-empty {
  color: var(--color-text-muted);
  padding: 28px 0 8px;
}

.mistake-review-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  list-style: none;
  margin: 20px 0 0;
  padding: 0;
}

.mistake-review-item {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border-soft);
  border-radius: 16px;
  padding: 16px;
}

.mistake-review-item__index {
  color: var(--color-primary-500);
  font-size: 12px;
  font-weight: 700;
}

.mistake-review-item__question {
  color: var(--color-text-primary);
  font-size: 18px;
  margin-top: 8px;
}

.mistake-review-item__selected {
  color: var(--color-text-secondary);
  margin: 12px 0;
}

.mistake-review-fade-enter-active,
.mistake-review-fade-leave-active {
  transition: opacity 0.2s ease;
}

.mistake-review-fade-enter-from,
.mistake-review-fade-leave-to {
  opacity: 0;
}
</style>
