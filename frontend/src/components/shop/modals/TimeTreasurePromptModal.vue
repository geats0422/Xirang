<script setup lang="ts">
defineProps<{
  visible: boolean;
  currentBoostMultiplier: number;
  remainingSeconds: number;
  timeTreasureQuantity: number;
}>();

const emit = defineEmits<{
  useTimeTreasure: [];
  buyMore: [];
  dismiss: [];
  close: [];
}>();

function fmt(secs: number) {
  return `${Math.floor(secs / 60)}:${(secs % 60).toString().padStart(2, "0")}`;
}
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="time-prompt-overlay" @click="emit('close')">
      <section class="time-prompt-modal" @click.stop>
        <h2>{{ $t("shop.boostExpiringTitle") }}</h2>
        <p>
          {{
            $t("shop.boostExpiringDesc", {
              multiplier: currentBoostMultiplier,
              time: fmt(remainingSeconds),
            })
          }}
        </p>
        <p>{{ $t("shop.timeTreasureAvailable", { n: timeTreasureQuantity }) }}</p>
        <footer class="time-prompt-modal__actions">
          <button class="confirm-btn" type="button" @click="emit('useTimeTreasure')">
            {{ $t("shop.useTimeTreasure") }} ({{ timeTreasureQuantity }})
          </button>
          <button class="secondary-btn" type="button" @click="emit('buyMore')">
            {{ $t("shop.buyMore") }}
          </button>
          <button class="cancel-btn" type="button" @click="emit('dismiss')">
            {{ $t("shop.letItExpire") }}
          </button>
        </footer>
      </section>
    </div>
  </transition>
</template>
