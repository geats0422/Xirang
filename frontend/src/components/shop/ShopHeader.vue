<script setup lang="ts">
import ShopActiveEffectsBar from "./ShopActiveEffectsBar.vue";
import { useI18n } from "vue-i18n";

defineProps<{ walletBalance: number; onOpenBag: () => void }>();

const { t } = useI18n();
</script>

<template>
  <header class="shop-header">
    <div class="shop-brand">
      <div class="shop-brand__icon"><img src="/taotie-logo.svg" alt="" /></div>
      <div class="shop-brand__copy"><strong>{{ t("shop.brand") }}</strong></div>
    </div>
    <div class="shop-wallet-group">
      <div class="wallet-pill">
        <span class="wallet-pill__coin">🪙</span>
        <strong>{{ walletBalance.toLocaleString() }}</strong>
      </div>
      <button class="bag-btn" type="button" :aria-label="t('shop.bagAria')" @click="onOpenBag">👜</button>
    </div>
  </header>
  <ShopActiveEffectsBar />
</template>

<style scoped>
.shop-header {
  align-items: center;
  border-bottom: 1px solid #e7e5e4;
  display: flex;
  justify-content: space-between;
  min-height: 80px;
  padding: 17px 25px;
}

.shop-brand {
  align-items: center;
  display: flex;
  gap: 12px;
}

.shop-brand__icon {
  align-items: center;
  background: linear-gradient(180deg, #f0fdfa, #e6fffb);
  border-radius: 999px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  display: inline-flex;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.shop-brand__icon img {
  display: block;
  height: 32px;
  width: 32px;
}

.shop-brand__copy {
  color: #3f3f46;
  font-size: 38px;
  font-weight: 700;
  line-height: 1;
}

.shop-wallet-group {
  align-items: center;
  display: flex;
  gap: 16px;
}

.wallet-pill {
  align-items: center;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #e7e5e4;
  border-radius: 999px;
  color: #3f3f46;
  display: inline-flex;
  gap: 8px;
  min-height: 46px;
  padding: 0 16px;
}

.wallet-pill__coin {
  color: #0f766e;
  font-size: 18px;
}

.wallet-pill strong {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.wallet-pill::after {
  color: #a8a29e;
  content: "COINS";
  font-size: 12px;
  letter-spacing: 0.08em;
  margin-left: 2px;
}

.bag-btn {
  align-items: center;
  background: #ffffff;
  border: 1px solid #d6d3d1;
  border-radius: 999px;
  color: #57534e;
  cursor: pointer;
  display: inline-flex;
  font-size: 18px;
  height: 44px;
  justify-content: center;
  width: 44px;
}

@media (max-width: 768px) {
  .shop-header {
    padding: 14px 16px;
  }

  .shop-brand__copy {
    font-size: 24px;
  }

  .wallet-pill strong {
    font-size: 24px;
  }

  .wallet-pill::after {
    font-size: 11px;
  }
}
</style>
