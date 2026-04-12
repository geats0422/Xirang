<script setup lang="ts">
defineProps<{
  visible: boolean;
  itemName: string;
  itemDescription: string;
  quantity: number;
  actionLabel?: string;
}>();

const emit = defineEmits<{ confirm: []; cancel: []; close: [] }>();
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="item-use-overlay" @click="emit('close')">
      <section class="item-use-modal" @click.stop>
        <h2>{{ itemName }}</h2>
        <p>{{ itemDescription }}</p>
        <p class="item-use-modal__qty">{{ $t("shop.inInventory", { n: quantity }) }}</p>
        <footer class="item-use-modal__actions">
          <button class="confirm-btn" type="button" @click="emit('confirm')">
            {{ actionLabel || $t("shop.useNow") }}
          </button>
          <button class="cancel-btn" type="button" @click="emit('cancel')">
            {{ $t("common.cancel") }}
          </button>
        </footer>
      </section>
    </div>
  </transition>
</template>
