<script setup lang="ts">
defineProps<{
  name: string;
  price: number;
  icon: string;
  accent: "teal" | "violet" | "rose" | "amber";
  itemCode: string;
  priceIsCash?: boolean;
  tag?: string;
  description?: string;
}>();

const emit = defineEmits<{ purchase: [itemCode: string] }>();
</script>

<template>
  <article class="shop-card" :class="`shop-card--${accent}`">
    <div class="shop-card__head">
      <span v-if="tag" class="rarity-tag" :class="`rarity-tag--${accent}`">{{ tag }}</span>
      <span class="price-tag" :class="{ 'price-tag--usd': priceIsCash }">
        {{ priceIsCash ? `$${price}` : `${price} 🪙` }}
      </span>
    </div>
    <div class="shop-card__icon" :class="`shop-card__icon--${accent}`">{{ icon }}</div>
    <div class="shop-card__body">
      <h2>{{ name }}</h2>
      <p>{{ description }}</p>
    </div>
    <footer class="shop-card__footer">
      <button
        class="purchase-btn"
        :class="`purchase-btn--${accent}`"
        type="button"
        @click="emit('purchase', itemCode)"
      >
        {{ priceIsCash ? $t("shop.buyNow") : $t("shop.purchase") }} →
      </button>
    </footer>
  </article>
</template>
