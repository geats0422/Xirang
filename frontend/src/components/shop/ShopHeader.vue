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
