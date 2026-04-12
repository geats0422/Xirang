<script setup lang="ts">
defineProps<{
  name: string;
  price: number;
  icon: string;
  accent: "teal" | "violet" | "rose" | "amber";
  itemCode: string;
  priceIsCash?: boolean;
  hidePriceTag?: boolean;
  tag?: string;
  badge?: string;
  description?: string;
}>();

const emit = defineEmits<{ purchase: [itemCode: string] }>();
</script>

<template>
  <article class="shop-card" :class="`shop-card--${accent}`">
    <span v-if="badge" class="shop-card__badge" :class="`shop-card__badge--${accent}`">{{ badge }}</span>
    <div class="shop-card__head">
      <span v-if="tag" class="rarity-tag" :class="`rarity-tag--${accent}`">{{ tag }}</span>
      <span
        v-if="!hidePriceTag && !(priceIsCash && tag)"
        class="price-tag"
        :class="{ 'price-tag--usd': priceIsCash }"
      >
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

<style scoped>
.shop-card {
  background: #ffffff;
  border: 1px solid #e7e5e4;
  border-radius: 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  min-height: 500px;
  overflow: hidden;
  padding: 16px;
  position: relative;
}

.shop-card--rose {
  border-color: #fecdd3;
  box-shadow: 0 0 0 1px #ffe4e6, 0 1px 2px rgba(0, 0, 0, 0.05);
}

.shop-card__head {
  align-items: center;
  display: flex;
  justify-content: flex-end;
  min-height: 24px;
}

.shop-card__badge {
  backdrop-filter: blur(2px);
  border: 1px solid #d6d3d1;
  border-radius: 8px;
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
  left: 16px;
  letter-spacing: 1px;
  line-height: 15px;
  padding: 3px 9px;
  position: absolute;
  text-transform: uppercase;
  top: 12px;
}

.shop-card__badge--rose {
  background: #fff1f2;
  border-color: #ffe4e6;
  color: #e11d48;
}

.shop-card__badge--amber {
  background: #fff7ed;
  border-color: #ffedd5;
  color: #ea580c;
}

.rarity-tag {
  color: #a8a29e;
  font-size: 12px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.rarity-tag--teal {
  color: #0891b2;
}

.rarity-tag--violet {
  color: #9333ea;
}

.rarity-tag--rose {
  color: #e11d48;
}

.rarity-tag--amber {
  color: #d97706;
}

.price-tag {
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #f5f5f4;
  border-radius: 16px;
  color: #3f3f46;
  display: inline-flex;
  font-size: 16px;
  font-weight: 700;
  gap: 4px;
  line-height: 24px;
  min-height: 38px;
  padding: 7px 13px;
}

.price-tag--usd {
  color: #0f766e;
}

.shop-card__icon {
  align-items: center;
  background: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 999px;
  color: #0891b2;
  display: inline-flex;
  font-size: 50px;
  font-weight: 500;
  height: 96px;
  justify-content: center;
  margin: 90px auto 0;
  text-shadow: 0 8px 30px rgba(34, 211, 238, 0.2);
  width: 96px;
}

.shop-card__icon--teal {
  color: #0891b2;
  text-shadow: 0 8px 30px rgba(34, 211, 238, 0.2);
}

.shop-card__icon--violet {
  color: #9333ea;
  text-shadow: 0 8px 30px rgba(168, 85, 247, 0.2);
}

.shop-card__icon--rose {
  color: #e11d48;
  text-shadow: 0 8px 30px rgba(239, 68, 68, 0.2);
}

.shop-card__icon--amber {
  color: #d97706;
  text-shadow: 0 8px 30px rgba(245, 158, 11, 0.2);
}

.shop-card__body {
  margin-top: 86px;
}

.shop-card__body h2 {
  color: #3f3f46;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
}

.shop-card--rose .shop-card__body h2 {
  color: #be123c;
}

.shop-card__body p {
  color: #71717a;
  font-size: 14px;
  line-height: 1.62;
  margin: 14px 0 0;
}

.shop-card__footer {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 24px;
}

.purchase-btn {
  align-items: center;
  border: 0;
  border-radius: 24px;
  color: #ffffff;
  cursor: pointer;
  display: inline-flex;
  font-size: 16px;
  font-weight: 700;
  gap: 8px;
  line-height: 24px;
  min-height: 44px;
  padding: 10px 24px;
  transition: filter 150ms ease;
}

.purchase-btn:hover {
  filter: brightness(1.05);
}

.purchase-btn--teal {
  background: linear-gradient(90deg, #0891b2, #0d9488);
}

.purchase-btn--violet {
  background: linear-gradient(90deg, #9333ea, #4f46e5);
}

.purchase-btn--rose {
  background: linear-gradient(90deg, #e11d48, #dc2626);
}

.purchase-btn--amber {
  background: linear-gradient(90deg, #d97706, #ea580c);
}

@media (max-width: 1280px) {
  .shop-card {
    min-height: 420px;
  }

  .shop-card__body h2 {
    font-size: 22px;
  }

  .shop-card__body p {
    font-size: 13px;
    line-height: 1.5;
  }
}

@media (max-width: 768px) {
  .shop-card {
    min-height: 360px;
  }

  .shop-card__icon {
    margin-top: 44px;
  }

  .shop-card__body {
    margin-top: 46px;
  }

  .shop-card__body h2 {
    font-size: 20px;
  }

  .shop-card__body p {
    font-size: 13px;
  }
}
</style>
