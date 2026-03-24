<script setup lang="ts">
import { onMounted } from "vue";
import BaseButton from "../components/ui/BaseButton.vue";

onMounted(() => {
  document.title = "Xi Rang Login";
});

const socialProviders = [
  {
    key: "google",
    label: "Continue with Google",
    icon: "/login-assets/icon-google.svg",
    isSvg: false,
  },
  {
    key: "microsoft",
    label: "Continue with Microsoft",
    icon: "/login-assets/icon-microsoft.svg",
    isSvg: false,
  },
  {
    key: "github",
    label: "Continue with GitHub",
    icon: "/login-assets/icon-github.svg",
    isSvg: true,
  },
] as const;

const bgImage = "/login-assets/bg-pattern.svg";
const mascotImage = "/taotie-main.svg";
const mailIcon = "/login-assets/icon-mail.svg";
const eyeIcon = "/login-assets/icon-eye.svg";
</script>

<template>
  <div class="login-page" data-node-id="4:714">
    <div class="login-page__bg" aria-hidden="true" data-node-id="4:716">
      <img :src="bgImage" alt="" />
    </div>

    <div class="login-page__stripe login-page__stripe--left" aria-hidden="true" />
    <div class="login-page__stripe login-page__stripe--center" aria-hidden="true" />
    <div class="login-page__stripe login-page__stripe--right" aria-hidden="true" />
    <div class="login-page__blob login-page__blob--left" aria-hidden="true" data-node-id="4:777" />
    <div class="login-page__blob login-page__blob--right" aria-hidden="true" data-node-id="4:778" />

    <main class="login-main" data-node-id="4:717">
      <section class="login-card" data-node-id="4:718" aria-label="Dungeon Scholar login">
        <div class="login-card__halo" aria-hidden="true" data-node-id="4:719" />

        <div class="login-card__mascot" aria-hidden="true" data-node-id="4:775">
          <img :src="mascotImage" alt="" data-node-id="7:29961" />
        </div>

        <header class="login-card__header" data-node-id="4:722">
          <h1 data-node-id="4:724">Xi Rang Scholar</h1>
          <p data-node-id="4:726">Log in to continue your magical journey</p>
        </header>

        <div class="social-buttons" data-node-id="4:727">
          <button v-for="provider in socialProviders" :key="provider.key" type="button" class="social-buttons__item">
            <span class="social-buttons__icon" :class="{ 'social-buttons__icon--svg': provider.isSvg }" aria-hidden="true">
              <img :src="provider.icon" alt="" />
            </span>
            <span>{{ provider.label }}</span>
          </button>
        </div>

        <div class="divider" data-node-id="4:738">
          <span data-node-id="4:743">Or continue with email</span>
        </div>

        <form class="email-form" data-node-id="4:745" @submit.prevent>
          <label class="email-form__field">
            <span>Email Address</span>
            <span class="email-form__input-wrap">
              <input type="email" placeholder="scholar@dungeon.com" />
              <img class="email-form__field-icon email-form__field-icon--mail" :src="mailIcon" alt="" aria-hidden="true" />
            </span>
          </label>

          <label class="email-form__field">
            <span>Password</span>
            <span class="email-form__input-wrap">
              <input type="password" placeholder="••••••••" />
              <img class="email-form__field-icon email-form__field-icon--eye" :src="eyeIcon" alt="" aria-hidden="true" />
            </span>
          </label>

          <BaseButton class="email-form__submit" full-width>Enter the Dungeon</BaseButton>
        </form>

        <footer class="card-footer" data-node-id="4:770">
          <a href="#" data-node-id="4:772">Forgot Password?</a>
          <p data-node-id="4:774">New here? <a href="#">Forge your account</a></p>
        </footer>
      </section>
    </main>

    <footer class="page-footer" data-node-id="4:779">
      <p data-node-id="4:781">© 2023 Dungeon Scholar. All rights reserved.</p>
    </footer>
  </div>
</template>

<style scoped>
.login-page {
  --color-primary-500: #108b96;
  --color-primary-600: #0f7e87;
  --color-primary-700: #0d6e76;
  background: #f8fafc;
  isolation: isolate;
  min-height: 100vh;
  overflow: hidden;
  position: relative;
}

.login-page__bg {
  inset: 0;
  opacity: 0.1;
  overflow: hidden;
  position: absolute;
}

.login-page__bg img {
  height: 125%;
  left: 0;
  object-fit: cover;
  position: absolute;
  top: -12.5%;
  width: 100%;
}

.login-page__stripe {
  background: rgba(255, 255, 255, 0.44);
  bottom: 0;
  pointer-events: none;
  position: absolute;
  top: 0;
  width: clamp(160px, 18vw, 230px);
  z-index: 0;
}

.login-page__stripe--left {
  left: 0;
}

.login-page__stripe--center {
  left: 50%;
  transform: translateX(-50%);
}

.login-page__stripe--right {
  right: 0;
}

.login-page__blob {
  backdrop-filter: blur(42px);
  border-radius: var(--radius-pill);
  pointer-events: none;
  position: absolute;
  z-index: 0;
}

.login-page__blob--left {
  background: rgba(113, 202, 211, 0.22);
  height: 95px;
  left: 40px;
  top: 238px;
  width: 96px;
}

.login-page__blob--right {
  background: rgba(126, 152, 255, 0.2);
  height: 127px;
  right: 40px;
  top: 588px;
  width: 128px;
}

.login-main {
  display: flex;
  justify-content: center;
  min-height: calc(100vh - 64px);
  padding: 144px var(--space-4) 72px;
  position: relative;
  z-index: 1;
}

.login-card {
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 14px;
  box-shadow: 0 22px 32px rgba(15, 23, 42, 0.13);
  display: flex;
  flex-direction: column;
  max-width: 448px;
  padding: 80px 32px 40px;
  position: relative;
  width: 100%;
}

.login-card__halo {
  border-radius: 14px;
  box-shadow: 0 30px 40px rgba(15, 23, 42, 0.1);
  inset: 0;
  pointer-events: none;
  position: absolute;
}

.login-card__mascot {
  align-items: center;
  display: flex;
  height: 160px;
  justify-content: center;
  left: 50%;
  position: absolute;
  top: -95px;
  transform: translateX(-50%);
  width: 160px;
}

.login-card__mascot img {
  display: block;
  height: 160px;
  width: 160px;
}

.login-card__header {
  text-align: center;
}

.login-card__header h1 {
  color: #1e293b;
  font-family: var(--font-serif);
  font-size: 48px;
  font-weight: 700;
  letter-spacing: -0.75px;
  line-height: 1.1;
  margin: 0;
}

.login-card__header p {
  color: #64748b;
  font-size: 14px;
  line-height: 20px;
  margin: var(--space-2) 0 0;
}

.social-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: 32px;
}

.social-buttons__item {
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  color: #334155;
  cursor: pointer;
  display: inline-flex;
  font-size: var(--text-sm);
  font-weight: 600;
  gap: var(--space-3);
  justify-content: center;
  min-height: 42px;
  padding: 11px 17px;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
  width: 100%;
}

.social-buttons__item:hover {
  border-color: #cbd5e1;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.social-buttons__icon {
  align-items: center;
  display: inline-flex;
  height: 20px;
  justify-content: center;
  width: 20px;
}

.social-buttons__icon img {
  display: block;
  height: 20px;
  width: 20px;
}

.social-buttons__icon--svg img {
  height: 10px;
  width: 16.67px;
}

.divider {
  align-items: center;
  color: #64748b;
  display: flex;
  font-size: 12px;
  font-weight: 500;
  justify-content: center;
  letter-spacing: 0.02em;
  margin-top: var(--space-6);
  position: relative;
  text-transform: uppercase;
}

.divider::before,
.divider::after {
  border-top: 1px solid #e2e8f0;
  content: "";
  flex: 1;
}

.divider span {
  backdrop-filter: blur(4px);
  background: rgba(255, 255, 255, 0.5);
  padding: 0 var(--space-2);
}

.email-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-top: var(--space-6);
}

.email-form__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.email-form__field > span {
  color: #334155;
  font-size: var(--text-sm);
  font-weight: 500;
  line-height: 20px;
}

.email-form__input-wrap {
  align-items: center;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  height: 47px;
  padding: 0 12px 0 17px;
}

.email-form__input-wrap:focus-within {
  border-color: rgba(16, 139, 150, 0.6);
  box-shadow: 0 0 0 2px rgba(16, 139, 150, 0.15);
}

.email-form__input-wrap input {
  background: transparent;
  border: 0;
  color: #334155;
  flex: 1;
  font-size: var(--text-sm);
  line-height: 1;
  outline: none;
}

.email-form__input-wrap input::placeholder {
  color: #94a3b8;
}

.email-form__field-icon {
  display: block;
  flex: 0 0 auto;
}

.email-form__field-icon--mail {
  height: 12px;
  width: 15px;
}

.email-form__field-icon--eye {
  height: 11.25px;
  width: 16.5px;
}

.email-form__submit {
  margin-top: 2px;
}

.card-footer {
  align-items: center;
  color: #64748b;
  display: flex;
  flex-direction: column;
  font-size: var(--text-sm);
  gap: var(--space-3);
  margin-top: var(--space-8);
  text-align: center;
}

.card-footer a {
  color: #64748b;
  text-decoration: none;
}

.card-footer p {
  margin: 0;
}

.card-footer p a {
  color: var(--color-primary-500);
  font-weight: 600;
}

.card-footer a:hover,
.card-footer p a:hover {
  text-decoration: underline;
}

.page-footer {
  padding: 0 0 24px;
  position: relative;
  text-align: center;
  z-index: 1;
}

.page-footer p {
  color: #94a3b8;
  font-size: 12px;
  line-height: 16px;
  margin: 0;
}

@media (max-width: 768px) {
  .login-main {
    padding-top: 108px;
  }

  .login-card {
    border-radius: var(--radius-lg);
    padding: 76px 20px 28px;
  }

  .login-card__header h1 {
    font-size: clamp(36px, 12vw, 44px);
  }

  .login-card__mascot {
    height: 132px;
    top: -78px;
    width: 132px;
  }

  .login-card__mascot img {
    height: 132px;
    width: 132px;
  }

  .login-page__blob {
    display: none;
  }
}
</style>
