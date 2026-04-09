<script setup lang="ts">
defineProps<{
  visible: boolean;
  revivalQuantity: number;
  reviveCost: number;
  canAfford: boolean;
  shieldExpiresAt: string | null;
  error?: string;
}>();

const emit = defineEmits<{
  useFromInventory: [];
  buyAndUse: [];
  leave: [];
  close: [];
}>();
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="revive-overlay" @click="emit('close')">
      <div class="revive-modal" role="dialog" @click.stop>
        <p class="revive-modal__eyebrow">{{ $t("endlessAbyss.reviveModal.eyebrow") }}</p>
        <h2>{{ $t("endlessAbyss.reviveModal.title") }}</h2>
        <p>{{ $t("endlessAbyss.reviveModal.description") }}</p>
        <p v-if="shieldExpiresAt" class="revive-modal__buff">
          {{ $t("endlessAbyss.reviveModal.shieldActive", { time: shieldExpiresAt }) }}
        </p>
        <p v-if="error" class="revive-modal__error">{{ error }}</p>
        <div class="revive-modal__actions">
          <button
            v-if="revivalQuantity > 0"
            class="cast-btn"
            type="button"
            @click="emit('useFromInventory')"
          >
            {{ $t("shop.useRevivalFromBag", { n: revivalQuantity }) }}
          </button>
          <button
            v-else-if="canAfford"
            class="cast-btn"
            type="button"
            @click="emit('buyAndUse')"
          >
            {{ $t("shop.buyAndUseRevival", { cost: reviveCost }) }}
          </button>
          <button v-else class="cast-btn" type="button" @click="emit('buyAndUse')">
            {{ $t("shop.buyRevivalAndRecharge", { cost: reviveCost }) }}
          </button>
          <button class="return-btn" type="button" @click="emit('leave')">
            {{ $t("endlessAbyss.reviveModal.leave") }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>
