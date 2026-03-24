<script setup lang="ts">
import { RouterView } from "vue-router";
import { useTheme } from "./composables/useTheme";

const { initTheme } = useTheme();
initTheme();
</script>

<template>
  <RouterView />
</template>
