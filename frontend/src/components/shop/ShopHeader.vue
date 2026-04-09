<script setup lang="ts">
import ShopActiveEffectsBar from "./ShopActiveEffectsBar.vue";

defineProps<{ walletBalance: number; onOpenBag: () => void }>();
</script>

<template>
  <header class="shop-header">
    <div class="shop-brand">
      <div class="shop-brand__icon"><img src="/taotie-logo.svg" alt="" /></div>
      <div class="shop-brand__copy"><strong>息壤</strong></div>
    </div>
    <div class="shop-wallet-group">
      <div class="wallet-pill">
        <span class="wallet-pill__coin">🪙</span>
        <strong>{{ walletBalance.toLocaleString() }}</strong>
      </div>
      <button class="bag-btn" type="button" aria-label="背包" @click="onOpenBag">👜</button>
    </div>
  </header>
  <ShopActiveEffectsBar />
</template>
