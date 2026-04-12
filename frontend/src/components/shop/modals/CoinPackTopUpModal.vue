<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";

defineProps<{
  visible: boolean;
  title?: string;
  offers: Array<{
    id: string;
    coin_amount: number;
    price_usd: number;
    label: string;
    recommended?: boolean;
  }>;
}>();

const emit = defineEmits<{
  purchase: [offerId: string];
  close: [];
}>();

const selected = ref<string | null>(null);

const { t, te } = useI18n();

const translateOr = (key: string, fallback: string): string => {
  if (!te(key)) return fallback;
  return t(key);
};
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="topup-overlay" @click="emit('close')">
      <section class="topup-modal" @click.stop>
        <header class="topup-modal__header">
          <h2>{{ title || translateOr("shop.topUpTitle", "灵钱宝匣充值") }}</h2>
          <button class="close-btn" type="button" @click="emit('close')">✕</button>
        </header>
        <p class="topup-modal__desc">选择一个档位后可继续确认购买（支付接口预留中）。</p>
        <div class="tier-list">
          <article
            v-for="offer in offers"
            :key="offer.id"
            class="tier-option"
            :class="{
              'tier-option--selected': selected === offer.id,
              'tier-option--recommended': offer.recommended,
            }"
            @click="selected = offer.id"
          >
            <span v-if="offer.recommended" class="recommended-badge">{{
              translateOr("shop.recommended", "推荐")
            }}</span>
            <strong>{{ offer.coin_amount }} 🪙</strong>
            <span>${{ offer.price_usd }}</span>
            <small>{{ offer.label }}</small>
            <button class="tier-buy-btn" type="button" @click.stop="emit('purchase', offer.id)">
              购买
            </button>
          </article>
        </div>
      </section>
    </div>
  </transition>
</template>

<style scoped>
.topup-overlay {
  align-items: center;
  background: rgba(15, 23, 42, 0.5);
  inset: 0;
  display: flex;
  justify-content: center;
  padding: 20px;
  position: fixed;
  z-index: 1100;
}

.topup-modal {
  background: #ffffff;
  border: 1px solid #e7e5e4;
  border-radius: 16px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
  max-width: 980px;
  padding: 22px;
  width: min(980px, 100%);
}

.topup-modal__header {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.topup-modal h2 {
  color: #1f2937;
  font-size: 28px;
  margin: 0;
}

.close-btn {
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 999px;
  color: #6b7280;
  cursor: pointer;
  height: 34px;
  width: 34px;
}

.topup-modal__desc {
  color: #6b7280;
  font-size: 14px;
  margin: 8px 0 0;
}

.tier-list {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 16px;
}

.tier-option {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 96px;
  padding: 12px;
  position: relative;
}

.tier-option--selected {
  border-color: #0d9488;
  box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.15);
}

.tier-option--recommended {
  background: #f0fdfa;
}

.recommended-badge {
  background: #0d9488;
  border-radius: 999px;
  color: #ffffff;
  font-size: 11px;
  line-height: 1;
  padding: 4px 8px;
  position: absolute;
  right: 10px;
  top: 10px;
}

.tier-option strong {
  color: #111827;
  font-size: 24px;
  margin-top: 8px;
}

.tier-option span {
  color: #374151;
  font-size: 16px;
}

.tier-option small {
  color: #6b7280;
  font-size: 12px;
}

.tier-buy-btn {
  background: linear-gradient(90deg, #d97706, #ea580c);
  border: 0;
  border-radius: 999px;
  color: #ffffff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  min-height: 40px;
  margin-top: 8px;
  padding: 0 16px;
}

@media (max-width: 640px) {
  .tier-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .tier-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
