<script setup lang="ts">
defineEmits<{
  editProfile: [];
}>();
</script>

<template>
  <section class="profile-hero">
    <div class="profile-hero__avatar-wrap">
      <div class="profile-hero__avatar">🧝</div>
      <span class="profile-hero__level">LV 42</span>
    </div>

    <div class="profile-hero__body">
      <div class="profile-hero__name-row">
        <h2>Scholar Li</h2>
        <span class="verified">✓</span>
      </div>
      <span class="tier-pill">Beta Tier</span>
      <p>Master of the Azure Archives. Currently exploring the depths of the Python Caverns.</p>
    </div>

    <button class="ghost-btn" type="button" @click="$emit('editProfile')">Edit Profile</button>
  </section>
</template>

<style scoped>
.profile-hero {
  align-items: flex-start;
  background: #ffffff;
  border: 1px solid #e6ece8;
  border-radius: 8px;
  display: grid;
  gap: 18px;
  grid-template-columns: 96px minmax(0, 1fr) auto;
  margin-top: 18px;
  padding: 18px;
  position: relative;
}

.profile-hero__avatar-wrap {
  position: relative;
}

.profile-hero__avatar {
  align-items: center;
  background: linear-gradient(180deg, #f6f8f9, #dee7e6);
  border: 1px solid #cad9d5;
  border-radius: 50%;
  display: inline-flex;
  font-size: 48px;
  height: 96px;
  justify-content: center;
  width: 96px;
}

.profile-hero__level {
  background: #1f9aa4;
  border-radius: 999px;
  bottom: -5px;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  left: 50%;
  padding: 3px 8px;
  position: absolute;
  transform: translateX(-50%);
}

.profile-hero__name-row {
  align-items: center;
  display: flex;
  gap: 8px;
}

.profile-hero__name-row h2 {
  color: #273742;
  font-family: var(--font-serif);
  font-size: 32px;
  line-height: 1;
  margin: 0;
}

.verified {
  color: #2aa6b1;
  font-size: 16px;
  font-weight: 700;
}

.tier-pill {
  background: #d7f1f2;
  border-radius: 4px;
  color: #2f95a0;
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  margin-top: 8px;
  padding: 3px 8px;
}

.profile-hero__body p {
  color: #5f7a88;
  font-size: 13px;
  line-height: 1.45;
  margin: 10px 0 0;
  max-width: 470px;
}

.ghost-btn {
  background: #fafaf8;
  border: 1px solid #d3dad7;
  border-radius: 8px;
  color: #51606b;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  height: 38px;
  padding: 0 16px;
}

@media (max-width: 768px) {
  .profile-hero {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .ghost-btn {
    justify-self: start;
  }
}
</style>
