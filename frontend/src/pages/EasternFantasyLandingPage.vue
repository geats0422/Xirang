<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import BaseButton from "../components/ui/BaseButton.vue";
import FeatureCard from "../components/ui/FeatureCard.vue";

onMounted(() => {
  document.title = "Xi Rang Landing";
});

const isMenuOpen = ref(false);
const router = useRouter();
const isRouting = ref(false);
const activeAction = ref<"login" | "get-started" | null>(null);

const navItems = ["Features", "Pricing", "Community"];

const featureCards = [
  {
    title: "3 Game Modes",
    description:
      "Choose your path to mastery. Engage in rapid-fire duels, long campaigns, or infinite dungeon crawls based on your PDFs.",
    icon: "🗡",
    accent: "green" as const,
  },
  {
    title: "AI Dungeon Master",
    description:
      "An intelligent guide that crafts your learning adventure, generates quizzes on the fly, and adapts to your skill level.",
    icon: "🧠",
    accent: "cyan" as const,
  },
  {
    title: "Zero Friction",
    description:
      "Seamlessly drag and drop your documents. Our engine converts them into playable quests instantly. No setup required.",
    icon: "☁",
    accent: "green" as const,
  },
];

const footerLinks = ["Privacy Policy", "Terms of Service", "Contact Us", "Twitter", "Discord"];

const routeByAuthState = async (action: "login" | "get-started") => {
  if (isRouting.value) {
    return;
  }

  isRouting.value = true;
  activeAction.value = action;

  await new Promise<void>((resolve) => {
    window.setTimeout(() => resolve(), 220);
  });

  const targetPath = action === "get-started" ? "/home" : "/login";
  await router.push(targetPath);

  isRouting.value = false;
  activeAction.value = null;
};
</script>

<template>
  <div class="landing-page" data-node-id="4:1178">
    <header class="site-header" data-node-id="4:1317">
      <div class="container site-header__inner">
        <div class="brand">
          <div class="brand__badge">
            <img src="/taotie-logo.svg" alt="Xi Rang logo" class="brand__logo" />
          </div>
          <p class="brand__name">Xi Rang</p>
        </div>

        <nav class="site-nav" aria-label="Main navigation">
          <a v-for="item in navItems" :key="item" href="#">{{ item }}</a>
        </nav>

        <button
          class="menu-toggle"
          type="button"
          :aria-expanded="isMenuOpen"
          aria-controls="mobile-nav"
          @click="isMenuOpen = !isMenuOpen"
        >
          {{ isMenuOpen ? "Close" : "Menu" }}
        </button>

        <BaseButton
          variant="primary"
          size="sm"
          class="cta-route-btn"
          :class="{ 'cta-route-btn--active': activeAction === 'login' }"
          :disabled="isRouting"
          @click="routeByAuthState('login')"
        >
          Login
        </BaseButton>
      </div>

      <nav id="mobile-nav" class="mobile-nav" :class="{ 'mobile-nav--open': isMenuOpen }" aria-label="Mobile navigation">
        <a v-for="item in navItems" :key="`mobile-${item}`" href="#" @click="isMenuOpen = false">{{ item }}</a>
      </nav>
    </header>

    <main>
      <section class="hero">
        <div class="container hero__inner">
          <div class="hero__content">
            <p class="hero__beta">Now in Open Beta</p>
            <h1 class="hero__title">
              Your Private
              <span>Knowledge</span>
              <span>Dungeon</span>
            </h1>
            <p class="hero__subtitle">
              Turn boring PDFs into dopamine-driven games. Forge your wisdom in the fires of an eastern fantasy RPG world
              powered by AI.
            </p>
            <div class="hero__actions">
              <BaseButton
                class="cta-route-btn"
                :class="{ 'cta-route-btn--active': activeAction === 'get-started' }"
                :disabled="isRouting"
                @click="routeByAuthState('get-started')"
              >
                Get Started →
              </BaseButton>
              <BaseButton variant="ghost">◉ Watch Demo</BaseButton>
            </div>
            <p class="hero__social">👥 Scholars joined this week</p>
          </div>

          <div class="hero__visual" aria-hidden="true">
            <div class="hero__card">
              <div class="hero__stat hero__stat--top">Scroll Decoded<br /><strong>+50 XP</strong></div>
              <div class="hero__mascot">
                <img src="/taotie-hero.svg" alt="Taotie illustration" class="hero__mascot-image" />
              </div>
              <div class="hero__stat hero__stat--bottom">Knowledge<br /><strong>Retained</strong></div>
            </div>
          </div>
        </div>
      </section>

      <section class="features" data-node-id="4:1182">
        <div class="container">
          <div class="section-head">
            <h2>Forge Your Knowledge</h2>
            <p>
              Unlock ancient wisdom with modern tools. Our platform transforms study material into an adventure.
            </p>
          </div>

          <div class="feature-grid">
            <FeatureCard
              v-for="feature in featureCards"
              :key="feature.title"
              :title="feature.title"
              :description="feature.description"
              :accent="feature.accent"
            >
              <template #icon>{{ feature.icon }}</template>
            </FeatureCard>
          </div>
        </div>
      </section>

      <section class="cta" data-node-id="4:1217">
        <div class="cta__overlay" />
        <div class="container cta__inner">
          <p class="cta__badge">✪ Join 10,000+ Scholars</p>
          <h2>Ready to Ascend?</h2>
          <p>
            The path to enlightenment is fraught with peril... and pop quizzes. Equip yourself with the ultimate study
            tool.
          </p>
          <BaseButton>Start Your Journey Free</BaseButton>
        </div>
      </section>
    </main>

    <footer class="site-footer" data-node-id="4:1296">
      <div class="container site-footer__inner">
        <p class="site-footer__brand">✧ Dungeon Scholar</p>

        <nav class="site-footer__links" aria-label="Footer links">
          <a v-for="item in footerLinks" :key="item" href="#">{{ item }}</a>
        </nav>

        <p class="site-footer__copyright">© 2023 Dungeon Scholar. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.landing-page {
  background: radial-gradient(circle at top right, rgba(212, 175, 55, 0.1), transparent 45%), var(--color-page-bg);
}

.container {
  margin: 0 auto;
  max-width: 1280px;
  padding: 0 32px;
  width: 100%;
}

.site-header {
  backdrop-filter: blur(6px);
  background: rgba(252, 251, 247, 0.9);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.site-header__inner {
  align-items: center;
  display: flex;
  justify-content: space-between;
  min-height: 64px;
}

.brand {
  align-items: center;
  display: flex;
  gap: 12px;
}

.brand__badge {
  align-items: center;
  background: rgba(255, 244, 214, 0.28);
  border: 1px solid #f0c95f;
  border-radius: var(--radius-sm);
  display: inline-flex;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.brand__logo {
  display: block;
  height: 30px;
  width: 30px;
}

.brand__name {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin: 0;
}

.site-nav {
  display: flex;
  gap: 32px;
}

.site-nav a,
.site-footer__links a {
  color: var(--color-text-tertiary);
  font-size: 14px;
  text-decoration: none;
}

.menu-toggle {
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  display: none;
  font-size: var(--text-sm);
  min-height: 36px;
  padding: 0 var(--space-3);
}

.mobile-nav {
  background: rgba(252, 251, 247, 0.97);
  border-bottom: 1px solid var(--color-border);
  display: none;
  flex-direction: column;
  gap: var(--space-2);
  padding: 0 var(--space-8);
}

.mobile-nav a {
  color: var(--color-text-tertiary);
  padding: var(--space-2) 0;
  text-decoration: none;
}

.site-nav a:hover,
.site-footer__links a:hover {
  color: var(--color-primary-700);
}

.hero {
  background: linear-gradient(90deg, rgba(212, 177, 130, 0.35) 0 38%, rgba(236, 213, 172, 0.38) 38% 100%);
  min-height: 760px;
  overflow: hidden;
  padding: 64px 0 112px;
}

.hero__inner {
  align-items: center;
  display: grid;
  gap: 40px;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}

.hero__beta {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: var(--radius-pill);
  color: var(--color-primary-700);
  display: inline-block;
  font-size: 14px;
  margin: 0 0 24px;
  padding: 6px 14px;
}

.hero__title {
  font-family: var(--font-serif);
  font-size: clamp(44px, 6vw, 60px);
  font-weight: 700;
  letter-spacing: -1.5px;
  line-height: 1.05;
  margin: 0;
}

.hero__title span {
  background: linear-gradient(90deg, var(--color-primary-600), #0891b2);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  display: block;
}

.hero__subtitle {
  color: var(--color-text-secondary);
  font-size: 18px;
  line-height: 1.8;
  margin: 24px 0 0;
  max-width: 580px;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 24px;
}

.hero__actions :deep(.cta-route-btn),
.site-header__inner :deep(.cta-route-btn) {
  transform-origin: center;
}

.hero__actions :deep(.cta-route-btn--active),
.site-header__inner :deep(.cta-route-btn--active) {
  animation: route-pulse 220ms ease;
}

@keyframes route-pulse {
  0% {
    transform: scale(1);
  }

  45% {
    transform: scale(0.96);
  }

  100% {
    transform: scale(1);
  }
}

.hero__social {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 24px 0 0;
}

.hero__visual {
  align-items: center;
  display: flex;
  justify-content: center;
  min-height: 500px;
}

.hero__card {
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-elevated);
  min-height: 470px;
  padding: 16px;
  position: relative;
  transform: rotate(1deg);
  width: min(624px, 100%);
}

.hero__card::before {
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.12), rgba(16, 185, 129, 0.02));
  border-radius: var(--radius-md);
  content: "";
  inset: 16px;
  position: absolute;
}

.hero__mascot {
  align-items: center;
  display: flex;
  height: 100%;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.hero__mascot-image {
  display: block;
  height: auto;
  max-height: 320px;
  max-width: min(92%, 520px);
  object-fit: contain;
  width: 100%;
}

.hero__stat {
  backdrop-filter: blur(2px);
  background: color-mix(in srgb, var(--color-white) 90%, transparent);
  border: 1px solid var(--color-primary-100);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.4;
  padding: 13px;
  position: absolute;
  z-index: 2;
}

.hero__stat strong {
  color: var(--color-text-strong);
  font-size: 14px;
}

.hero__stat--top {
  right: 32px;
  top: 32px;
}

.hero__stat--bottom {
  bottom: 48px;
  left: 32px;
}

.features {
  background: var(--color-surface-alt);
  padding: 96px 0;
}

.section-head {
  margin: 0 auto;
  max-width: 672px;
  text-align: center;
}

.section-head h2,
.cta h2 {
  font-family: var(--font-serif);
  font-size: clamp(36px, 4vw, 48px);
  margin: 0;
}

.section-head p,
.cta p {
  color: var(--color-text-secondary);
  font-size: 18px;
  line-height: 1.6;
  margin: 16px 0 0;
}

.feature-grid {
  display: grid;
  gap: 32px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 64px;
}

.cta {
  overflow: hidden;
  padding: 80px 0;
  position: relative;
}

.cta__overlay {
  background: linear-gradient(180deg, rgba(252, 251, 247, 0.45), var(--color-surface-alt));
  inset: 0;
  position: absolute;
}

.cta__inner {
  position: relative;
  text-align: center;
}

.cta__badge {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: var(--radius-pill);
  color: var(--color-primary-700);
  display: inline-block;
  font-size: 14px;
  margin: 0;
  padding: 12px 16px;
}

.cta__inner > h2 {
  margin-top: 28px;
}

.cta__inner > p {
  margin: 16px auto 0;
  max-width: 720px;
}

.cta__inner :deep(.base-btn) {
  margin-top: 32px;
  min-height: 56px;
}

.site-footer {
  background: var(--color-page-bg);
  border-top: 1px solid var(--color-border);
  padding: 48px 0;
}

.site-footer__inner {
  text-align: center;
}

.site-footer__brand {
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 700;
  margin: 0;
}

.site-footer__links {
  display: flex;
  flex-wrap: wrap;
  gap: 24px 32px;
  justify-content: center;
  margin-top: 32px;
}

.site-footer__copyright {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 32px 0 0;
  opacity: 0.65;
}

@media (max-width: 1120px) {
  .hero__inner {
    grid-template-columns: 1fr;
  }

  .hero__visual {
    min-height: 380px;
  }

  .feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .container {
    padding: 0 20px;
  }

  .site-nav {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
    margin-left: auto;
    margin-right: var(--space-2);
  }

  .mobile-nav--open {
    display: flex;
    padding-bottom: var(--space-3);
  }

  .hero {
    padding: 48px 0 72px;
  }

  .hero__subtitle,
  .section-head p,
  .cta p {
    font-size: 16px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
    margin-top: 40px;
  }

  .hero__stat {
    padding: 10px;
  }

  .hero__stat--top {
    right: 16px;
    top: 16px;
  }

  .hero__stat--bottom {
    bottom: 20px;
    left: 16px;
  }
}
</style>
