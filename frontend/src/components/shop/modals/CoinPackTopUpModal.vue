<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  visible: boolean;
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
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="topup-overlay" @click="emit('close')">
      <section class="topup-modal" @click.stop>
        <h2>{{ $t("shop.topUpTitle") }}</h2>
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
              $t("shop.recommended")
            }}</span>
            <strong>{{ offer.coin_amount }} 🪙</strong>
            <span>${{ offer.price_usd }}</span>
            <small>{{ offer.label }}</small>
          </article>
        </div>
        <footer class="topup-modal__actions">
          <button
            class="confirm-btn"
            :disabled="!selected"
            type="button"
            @click="selected && emit('purchase', selected)"
          >
            {{ $t("shop.confirmPurchase") }}
          </button>
          <button class="cancel-btn" type="button" @click="emit('close')">
            {{ $t("common.cancel") }}
          </button>
        </footer>
      </section>
    </div>
  </transition>
</template>
