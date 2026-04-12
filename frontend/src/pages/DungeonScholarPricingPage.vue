<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watchEffect } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import BaseButton from "../components/ui/BaseButton.vue";
import { useTheme, type Theme } from "../composables/useTheme";
import { SUPPORTED_LOCALES, type SupportedLocale } from "../i18n";
import { ROUTES } from "../constants/routes";
import { PRICING_CONFIG, COIN_PACKAGES } from "../config/pricing";
import { useCoinPurchase, type CoinOffer } from "../composables/useCoinPurchase";

const isMenuOpen = ref(false);
const router = useRouter();
const { locale, t } = useI18n();
const { theme, setTheme } = useTheme();
const isRouting = ref(false);
const activeAction = ref<"login" | "sign-up" | "get-started" | null>(null);
const showLangDropdown = ref(false);
const billingCycle = ref<"monthly" | "quarterly" | "yearly">("monthly");

const {
  coinOffers,
  showPurchaseModal,
  selectedOffer,
  isPurchasing,
  purchaseError,
  openPurchaseModal,
  closePurchaseModal,
  confirmPurchase,
} = useCoinPurchase();

const handleSubscribe = (plan: "free" | "pro") => {
  if (plan === "free") {
    alert(t("pricing.alreadyFree", "You are already on the free plan!"));
    return;
  }
  alert(t("pricing.comingSoon", "Pro subscription is coming soon!"));
};

const handleBuyCoins = (coins: number, price: number) => {
  const offer = coinOffers.value.find((o) => o.coin_amount === coins && o.price_usd === price);
  if (offer) {
    openPurchaseModal(offer);
  } else {
    const fallbackOffer: CoinOffer = {
      id: `coin_pack_${coins}`,
      coin_amount: coins,
      price_usd: price,
      label: `${coins} Coins`,
      recommended: false,
    };
    openPurchaseModal(fallbackOffer);
  }
};

const themeCycle: Theme[] = ["light", "dark", "system"];

const languages = computed(() => {
  const _ = locale.value;
  return SUPPORTED_LOCALES.map((code) => ({
    code,
    name: t(`settings.localeNames.${code}`),
  }));
});

const currentLangName = computed(() => {
  return languages.value.find((entry) => entry.code === locale.value)?.name ?? locale.value;
});

const currentThemeLabel = computed(() => {
  const _ = locale.value;
  return t(`settings.preferences.${theme.value}`);
});

const closeHeaderDropdowns = () => {
  showLangDropdown.value = false;
};

const toggleLang = () => {
  showLangDropdown.value = !showLangDropdown.value;
};

const selectLang = (code: SupportedLocale) => {
  locale.value = code;
  showLangDropdown.value = false;
};

const cycleTheme = () => {
  const currentIndex = themeCycle.indexOf(theme.value);
  const nextIndex = (currentIndex + 1) % themeCycle.length;
  setTheme(themeCycle[nextIndex]);
};

onMounted(() => {
  document.addEventListener("click", closeHeaderDropdowns);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", closeHeaderDropdowns);
});

watchEffect(() => {
  document.title = t("pricing.metaTitle");
});

const navItems = computed(() => {
  const _ = locale.value;
  return [
    { label: t("landing.home"), href: ROUTES.landing },
    { label: t("landing.features"), href: ROUTES.features },
    { label: t("landing.pricing"), href: ROUTES.pricing },
    { label: t("landing.community"), href: ROUTES.community },
  ];
});

const footerLinks = computed(() => {
  const _ = locale.value;
  return [
    { text: t("landing.privacyPolicy"), href: "/privacy-policy" },
    { text: t("landing.termsOfService"), href: "/terms-of-service" },
    { text: t("landing.contactUs"), href: "/help-center" },
    { text: t("landing.twitter"), href: "#" },
    { text: t("landing.discord"), href: "#" },
  ];
});

const brandName = computed(() => {
  const _ = locale.value;
  return t("landing.brand");
});

const logoAlt = computed(() => {
  const _ = locale.value;
  return t("landing.logoAlt");
});

const mainNavAria = computed(() => {
  const _ = locale.value;
  return t("landing.mainNavAria");
});

const languageLabel = computed(() => {
  const _ = locale.value;
  return t("landing.languageLabel");
});

const loginLabel = computed(() => {
  const _ = locale.value;
  return t("landing.login");
});

const signUpLabel = computed(() => {
  const _ = locale.value;
  return t("landing.signUp");
});

const mobileNavAria = computed(() => {
  const _ = locale.value;
  return t("landing.mobileNavAria");
});

const footerLinksAria = computed(() => {
  const _ = locale.value;
  return t("landing.footerLinksAria");
});

const footerBrand = computed(() => {
  const _ = locale.value;
  return t("landing.footerBrand");
});

const copyrightLabel = computed(() => {
  const _ = locale.value;
  return t("landing.copyright");
});

const menuLabel = computed(() => {
  const _ = locale.value;
  return t("landing.menu");
});

const closeLabel = computed(() => {
  const _ = locale.value;
  return t("landing.close");
});

const routeByAuthState = async (action: "login" | "sign-up" | "get-started") => {
  if (isRouting.value) {
    return;
  }

  isRouting.value = true;
  activeAction.value = action;

  await new Promise<void>((resolve) => {
    window.setTimeout(() => resolve(), 220);
  });

  const targetPath =
    action === "get-started" ? ROUTES.home : action === "sign-up" ? ROUTES.signUp : ROUTES.login;
  await router.push(targetPath);

  isRouting.value = false;
  activeAction.value = null;
};

const pricingPlans = computed(() => {
  const _ = locale.value;
  const currentPrice = PRICING_CONFIG.plans[billingCycle.value];
  const originalPrice = billingCycle.value !== "monthly" ? PRICING_CONFIG.originalPrices[billingCycle.value] : null;
  const discount = billingCycle.value !== "monthly" ? `${PRICING_CONFIG.discounts[billingCycle.value]}%` : null;

  return {
    free: {
      name: t("pricing.freePlan"),
      price: currentPrice.free,
      period: billingCycle.value === "monthly" ? t("pricing.perMonth") : billingCycle.value === "quarterly" ? t("pricing.perQuarter") : t("pricing.perYear"),
      features: [
        t("pricing.freeFeature1"),
        t("pricing.freeFeature2"),
        t("pricing.freeFeature3"),
        t("pricing.freeFeature4"),
      ],
      cta: t("pricing.startFree"),
      highlighted: false,
    },
    pro: {
      name: t("pricing.proPlan"),
      price: currentPrice.pro,
      originalPrice,
      period: billingCycle.value === "monthly" ? t("pricing.perMonth") : billingCycle.value === "quarterly" ? t("pricing.perQuarter") : t("pricing.perYear"),
      discount,
      features: [
        t("pricing.proFeature1"),
        t("pricing.proFeature2"),
        t("pricing.proFeature3"),
        t("pricing.proFeature4"),
        t("pricing.proFeature5"),
        t("pricing.proFeature6"),
      ],
      cta: t("pricing.upgradePro"),
      highlighted: true,
    },
  };
});

const coinPackages = COIN_PACKAGES;
</script>

<template>
  <div class="pricing-page">
    <header class="site-header">
      <div class="container site-header__inner">
        <div class="brand">
          <div class="brand__badge">
            <img src="/taotie-logo.svg" :alt="logoAlt" class="brand__logo" />
          </div>
          <p class="brand__name">{{ brandName }}</p>
        </div>

        <nav class="site-nav site-nav--centered" :aria-label="mainNavAria">
          <router-link
            v-for="item in navItems"
            :key="item.label"
            :to="item.href"
            class="nav-link"
            :class="{ 'nav-link--active': $route.path === item.href }"
          >
            {{ item.label }}
          </router-link>
        </nav>

        <div class="header-right">
          <div class="header-icon-btn" @click.stop>
            <button
              class="icon-btn"
              type="button"
              :aria-expanded="showLangDropdown"
              :aria-label="`${languageLabel}: ${currentLangName}`"
              @click="toggleLang"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            </button>
            <div v-if="showLangDropdown" class="header-dropdown" role="menu" :aria-label="languageLabel">
              <button
                v-for="lang in languages"
                :key="lang.code"
                class="header-dropdown__item"
                :class="{ 'header-dropdown__item--active': locale === lang.code }"
                type="button"
                role="menuitemradio"
                :aria-checked="locale === lang.code"
                @click="selectLang(lang.code)"
              >
                {{ lang.name }}
              </button>
            </div>
          </div>

          <div class="header-icon-btn" @click.stop>
            <button
              class="icon-btn"
              type="button"
              :aria-label="`${t('settings.preferences.themeLabel')}: ${currentThemeLabel}`"
              @click="cycleTheme"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="12" cy="12" r="5" />
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
              </svg>
            </button>
          </div>

          <div class="header-auth">
            <BaseButton
              variant="primary"
              size="sm"
              class="cta-route-btn"
              :class="{ 'cta-route-btn--active': activeAction === 'login' }"
              :disabled="isRouting"
              @click="routeByAuthState('login')"
            >
              {{ loginLabel }}
            </BaseButton>
            <BaseButton
              variant="ghost"
              size="sm"
              class="cta-route-btn"
              :class="{ 'cta-route-btn--active': activeAction === 'sign-up' }"
              :disabled="isRouting"
              @click="routeByAuthState('sign-up')"
            >
              {{ signUpLabel }}
            </BaseButton>
          </div>
        </div>

        <button
          class="menu-toggle"
          type="button"
          :aria-expanded="isMenuOpen"
          aria-controls="mobile-nav"
          @click="isMenuOpen = !isMenuOpen"
        >
          {{ isMenuOpen ? closeLabel : menuLabel }}
        </button>
      </div>

      <nav id="mobile-nav" class="mobile-nav" :class="{ 'mobile-nav--open': isMenuOpen }" :aria-label="mobileNavAria">
        <router-link
          v-for="item in navItems"
          :key="`mobile-${item.label}`"
          :to="item.href"
          class="mobile-nav-link"
          :class="{ 'mobile-nav-link--active': $route.path === item.href }"
          @click="isMenuOpen = false"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </header>

    <main>
      <!-- Hero Section with Scroll Decoration -->
      <section class="pricing-hero">
        <div class="scroll-decoration scroll-decoration--left" aria-hidden="true">
          <svg viewBox="0 0 100 400" class="scroll-svg">
            <path d="M80,0 Q100,50 80,100 Q60,150 80,200 Q100,250 80,300 Q60,350 80,400" fill="none" stroke="currentColor" stroke-width="2" />
            <circle cx="80" cy="20" r="15" fill="currentColor" opacity="0.1" />
            <circle cx="80" cy="380" r="15" fill="currentColor" opacity="0.1" />
          </svg>
        </div>

        <div class="container pricing-hero__inner">
          <div class="hero-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
            <span>{{ t("pricing.heroBadge") }}</span>
          </div>
          <h1 class="pricing-hero__title">
            {{ t("pricing.heroTitle") }}
            <span class="title-accent">{{ t("pricing.heroTitleAccent") }}</span>
          </h1>
          <p class="pricing-hero__subtitle">{{ t("pricing.heroSubtitle") }}</p>
        </div>

        <div class="scroll-decoration scroll-decoration--right" aria-hidden="true">
          <svg viewBox="0 0 100 400" class="scroll-svg">
            <path d="M20,0 Q0,50 20,100 Q40,150 20,200 Q0,250 20,300 Q40,350 20,400" fill="none" stroke="currentColor" stroke-width="2" />
            <circle cx="20" cy="20" r="15" fill="currentColor" opacity="0.1" />
            <circle cx="20" cy="380" r="15" fill="currentColor" opacity="0.1" />
          </svg>
        </div>
      </section>

      <!-- Billing Cycle Toggle -->
      <section class="billing-toggle-section">
        <div class="container">
          <div class="billing-toggle">
            <button
              :class="{ active: billingCycle === 'monthly' }"
              @click="billingCycle = 'monthly'"
            >
              {{ t("pricing.monthly") }}
            </button>
            <button
              :class="{ active: billingCycle === 'quarterly' }"
              @click="billingCycle = 'quarterly'"
            >
              {{ t("pricing.quarterly") }}
              <span class="discount-badge">-10%</span>
            </button>
            <button
              :class="{ active: billingCycle === 'yearly' }"
              @click="billingCycle = 'yearly'"
            >
              {{ t("pricing.yearly") }}
              <span class="discount-badge">-20%</span>
            </button>
          </div>
        </div>
      </section>

      <!-- Pricing Cards -->
      <section class="pricing-cards-section">
        <div class="container">
          <div class="pricing-grid">
            <!-- Free Plan -->
            <div class="pricing-card" :class="{ 'pricing-card--highlighted': !pricingPlans.free.highlighted }">
              <div class="card-scroll-top" aria-hidden="true">
                <svg viewBox="0 0 300 30" preserveAspectRatio="none">
                  <path d="M0,30 Q150,0 300,30" fill="none" stroke="currentColor" stroke-width="2" />
                  <circle cx="15" cy="25" r="8" fill="currentColor" opacity="0.2" />
                  <circle cx="285" cy="25" r="8" fill="currentColor" opacity="0.2" />
                </svg>
              </div>

              <div class="card-inner">
                <div class="card-header">
                  <div class="plan-icon">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M12 2L2 7l10 5 10-5-10-5z" />
                      <path d="M2 17l10 5 10-5" />
                      <path d="M2 12l10 5 10-5" />
                    </svg>
                  </div>
                  <h3 class="plan-name">{{ pricingPlans.free.name }}</h3>
                  <div class="plan-price">
                    <span class="price-amount">{{ t("pricing.free") }}</span>
                  </div>
                  <p class="plan-desc">{{ t("pricing.freeDesc") }}</p>
                </div>

                <ul class="feature-list">
                  <li v-for="(feature, index) in pricingPlans.free.features" :key="index" class="feature-item">
                    <svg class="feature-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    <span>{{ feature }}</span>
                  </li>
                </ul>

                <div class="card-cta">
                  <BaseButton variant="ghost" size="md" full-width @click="handleSubscribe('free')">
                    {{ pricingPlans.free.cta }}
                  </BaseButton>
                </div>
              </div>

              <div class="card-scroll-bottom" aria-hidden="true">
                <svg viewBox="0 0 300 30" preserveAspectRatio="none">
                  <path d="M0,0 Q150,30 300,0" fill="none" stroke="currentColor" stroke-width="2" />
                  <circle cx="15" cy="5" r="8" fill="currentColor" opacity="0.2" />
                  <circle cx="285" cy="5" r="8" fill="currentColor" opacity="0.2" />
                </svg>
              </div>
            </div>

            <!-- Pro Plan (Highlighted) -->
            <div class="pricing-card pricing-card--pro" :class="{ 'pricing-card--highlighted': pricingPlans.pro.highlighted }">
              <div class="popular-badge">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
                <span>{{ t("pricing.mostPopular") }}</span>
              </div>

              <div class="card-scroll-top" aria-hidden="true">
                <svg viewBox="0 0 300 30" preserveAspectRatio="none">
                  <path d="M0,30 Q150,0 300,30" fill="none" stroke="currentColor" stroke-width="2" />
                  <circle cx="15" cy="25" r="8" fill="currentColor" opacity="0.3" />
                  <circle cx="285" cy="25" r="8" fill="currentColor" opacity="0.3" />
                </svg>
              </div>

              <div class="card-inner">
                <div class="card-header">
                  <div class="plan-icon plan-icon--pro">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M12 2L2 7l10 5 10-5-10-5z" />
                      <path d="M2 17l10 5 10-5" />
                      <path d="M2 12l10 5 10-5" />
                      <circle cx="12" cy="12" r="3" fill="currentColor" />
                    </svg>
                  </div>
                  <h3 class="plan-name">{{ pricingPlans.pro.name }}</h3>
                  <div class="plan-price">
                    <span v-if="pricingPlans.pro.originalPrice" class="price-original">¥{{ pricingPlans.pro.originalPrice }}</span>
                    <span class="price-amount">¥{{ pricingPlans.pro.price }}</span>
                    <span class="price-period">{{ pricingPlans.pro.period }}</span>
                  </div>
                  <div v-if="pricingPlans.pro.discount" class="save-badge">
                    {{ t("pricing.save") }} {{ pricingPlans.pro.discount }}
                  </div>
                  <p class="plan-desc">{{ t("pricing.proDesc") }}</p>
                </div>

                <ul class="feature-list">
                  <li v-for="(feature, index) in pricingPlans.pro.features" :key="index" class="feature-item feature-item--pro">
                    <svg class="feature-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    <span>{{ feature }}</span>
                  </li>
                </ul>

                <div class="card-cta">
                  <BaseButton size="md" full-width @click="handleSubscribe('pro')">
                    {{ pricingPlans.pro.cta }}
                  </BaseButton>
                </div>
              </div>

              <div class="card-scroll-bottom" aria-hidden="true">
                <svg viewBox="0 0 300 30" preserveAspectRatio="none">
                  <path d="M0,0 Q150,30 300,0" fill="none" stroke="currentColor" stroke-width="2" />
                  <circle cx="15" cy="5" r="8" fill="currentColor" opacity="0.3" />
                  <circle cx="285" cy="5" r="8" fill="currentColor" opacity="0.3" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Coin Packages Section -->
      <section class="coins-section">
        <div class="container">
          <div class="section-header">
            <div class="section-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v12M9 9h6M9 15h6" />
              </svg>
            </div>
            <h2 class="section-title">{{ t("pricing.coinsTitle") }}</h2>
            <p class="section-subtitle">{{ t("pricing.coinsSubtitle") }}</p>
          </div>

          <div class="coins-grid">
            <div
              v-for="pkg in coinPackages"
              :key="pkg.coins"
              class="coin-card"
              :class="{ 'coin-card--popular': pkg.popular }"
            >
              <div v-if="pkg.popular" class="coin-popular-badge">
                {{ t("pricing.bestValue") }}
              </div>
              <div class="coin-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 6v12M9 9h6M9 15h6" />
                </svg>
              </div>
              <div class="coin-amount">{{ pkg.coins }}</div>
              <div class="coin-label">{{ t("pricing.coins") }}</div>
              <div class="coin-price">${{ pkg.price }}</div>
              <BaseButton :variant="pkg.popular ? 'primary' : 'ghost'" size="sm" @click="handleBuyCoins(pkg.coins, pkg.price)">
                {{ t("pricing.buyNow") }}
              </BaseButton>
            </div>
          </div>
        </div>
      </section>

      <!-- FAQ Section -->
      <section class="faq-section">
        <div class="container">
          <h2 class="section-title">{{ t("pricing.faqTitle") }}</h2>
          <div class="faq-grid">
            <div class="faq-item">
              <h4>{{ t("pricing.faq1Question") }}</h4>
              <p>{{ t("pricing.faq1Answer") }}</p>
            </div>
            <div class="faq-item">
              <h4>{{ t("pricing.faq2Question") }}</h4>
              <p>{{ t("pricing.faq2Answer") }}</p>
            </div>
            <div class="faq-item">
              <h4>{{ t("pricing.faq3Question") }}</h4>
              <p>{{ t("pricing.faq3Answer") }}</p>
            </div>
            <div class="faq-item">
              <h4>{{ t("pricing.faq4Question") }}</h4>
              <p>{{ t("pricing.faq4Answer") }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- CTA Section -->
      <section class="pricing-cta">
        <div class="cta__overlay" />
        <div class="container cta__inner">
          <div class="cta-decoration" aria-hidden="true">
            <svg viewBox="0 0 100 100" class="cta-cloud">
              <path d="M20,50 Q30,30 50,40 Q70,20 80,40 Q95,35 90,55 Q95,75 75,70 Q60,85 40,70 Q20,80 15,60 Q5,50 20,50" fill="currentColor" opacity="0.1" />
            </svg>
          </div>
          <p class="cta__badge">{{ t("pricing.ctaBadge") }}</p>
          <h2>{{ t("pricing.ctaTitle") }}</h2>
          <p>{{ t("pricing.ctaDesc") }}</p>
          <BaseButton size="md" @click="routeByAuthState('get-started')">
            {{ t("pricing.ctaButton") }}
          </BaseButton>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <div class="container site-footer__inner">
        <p class="site-footer__brand">{{ footerBrand }}</p>
        <nav class="site-footer__links" :aria-label="footerLinksAria">
          <a v-for="item in footerLinks" :key="item.text" :href="item.href">{{ item.text }}</a>
        </nav>
        <p class="site-footer__copyright">{{ copyrightLabel }}</p>
      </div>
    </footer>

    <!-- Purchase Confirmation Modal -->
    <transition name="modal-fade">
      <div
        v-if="showPurchaseModal"
        class="purchase-modal-overlay"
        @click="closePurchaseModal"
      >
        <div class="purchase-modal" @click.stop>
          <div class="purchase-modal__header">
            <h3>{{ t("pricing.confirmPurchase", "确认购买") }}</h3>
            <button class="purchase-modal__close" @click="closePurchaseModal">×</button>
          </div>
          <div class="purchase-modal__body">
            <div v-if="selectedOffer" class="purchase-offer">
              <div class="purchase-offer__icon">🪙</div>
              <div class="purchase-offer__details">
                <div class="purchase-offer__amount">{{ selectedOffer.coin_amount }} {{ t("pricing.coins", "代币") }}</div>
                <div class="purchase-offer__price">${{ selectedOffer.price_usd }}</div>
              </div>
            </div>
            <p class="purchase-modal__note">{{ t("pricing.purchaseNote", "点击确认后将跳转至支付页面") }}</p>
            <div v-if="purchaseError" class="purchase-modal__error">{{ purchaseError }}</div>
          </div>
          <div class="purchase-modal__footer">
            <BaseButton variant="ghost" size="sm" @click="closePurchaseModal">
              {{ t("common.cancel", "取消") }}
            </BaseButton>
            <BaseButton
              variant="primary"
              size="sm"
              :loading="isPurchasing"
              @click="confirmPurchase"
            >
              {{ t("pricing.confirm", "确认购买") }}
            </BaseButton>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.pricing-page {
  background: radial-gradient(circle at top right, rgba(212, 175, 55, 0.08), transparent 45%),
              radial-gradient(circle at bottom left, rgba(16, 185, 129, 0.05), transparent 40%),
              var(--color-page-bg);
  min-height: 100vh;
}

/* Container */
.container {
  margin: 0 auto;
  max-width: 1280px;
  padding: 0 32px;
  width: 100%;
}

/* Header Styles (same as landing page) */
.site-header {
  backdrop-filter: blur(6px);
  background: var(--color-glass-bg);
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
  position: relative;
}

.brand {
  align-items: center;
  display: flex;
  flex-shrink: 0;
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
  color: var(--color-text-primary);
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

.site-nav--centered {
  left: 50%;
  position: absolute;
  transform: translateX(-50%);
}

.header-right {
  align-items: center;
  display: flex;
  flex-shrink: 0;
  gap: var(--space-2);
}

.site-nav--centered .nav-link,
.site-footer__links a {
  color: var(--color-text-tertiary);
  font-size: 14px;
  text-decoration: none;
  position: relative;
  transition: color 0.2s ease;
}

.site-nav--centered .nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--color-primary-500);
  transition: width 0.3s ease, left 0.3s ease;
}

.site-nav--centered .nav-link:hover {
  color: var(--color-primary-700);
}

.site-nav--centered .nav-link:hover::after {
  width: 100%;
  left: 0;
}

.site-nav--centered .nav-link--active {
  color: var(--color-primary-600);
  font-weight: 500;
}

.site-nav--centered .nav-link--active::after {
  width: 100%;
  left: 0;
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
  background: var(--color-glass-bg);
  border-bottom: 1px solid var(--color-border);
  display: none;
  flex-direction: column;
  gap: var(--space-2);
  padding: 0 var(--space-8);
}

.mobile-nav .mobile-nav-link {
  color: var(--color-text-tertiary);
  padding: var(--space-2) 0;
  text-decoration: none;
  position: relative;
  transition: color 0.2s ease, padding-left 0.2s ease;
}

.mobile-nav .mobile-nav-link:hover {
  color: var(--color-primary-600);
  padding-left: var(--space-2);
}

.mobile-nav .mobile-nav-link--active {
  color: var(--color-primary-600);
  font-weight: 500;
  padding-left: var(--space-2);
}

.header-icon-btn {
  align-items: center;
  display: inline-flex;
  position: relative;
}

.icon-btn {
  align-items: center;
  background: transparent;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  display: inline-flex;
  height: 36px;
  justify-content: center;
  transition: color 0.2s ease, background-color 0.2s ease;
  width: 36px;
}

.icon-btn:hover {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
}

.header-dropdown {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-elevated);
  min-width: 140px;
  overflow: hidden;
  position: absolute;
  right: 0;
  top: calc(100% + var(--space-2));
  z-index: 100;
}

.header-dropdown__item {
  background: transparent;
  border: 0;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: block;
  font-size: var(--text-sm);
  padding: 10px 14px;
  text-align: left;
  transition: background-color 0.15s ease, color 0.15s ease;
  width: 100%;
}

.header-dropdown__item:hover {
  background: var(--color-primary-50);
  color: var(--color-primary-700);
}

.header-dropdown__item--active {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  font-weight: 600;
}

.header-auth {
  align-items: center;
  display: flex;
  gap: var(--space-2);
}

.cta-route-btn {
  transition: transform 0.2s ease;
}

.cta-route-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.cta-route-btn--active {
  transform: scale(0.97);
}

/* Hero Section */
.pricing-hero {
  padding: 80px 0 60px;
  position: relative;
  overflow: hidden;
}

.pricing-hero__inner {
  text-align: center;
  position: relative;
  z-index: 1;
}

.scroll-decoration {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 100px;
  color: var(--color-primary-200);
  opacity: 0.6;
}

.scroll-decoration--left {
  left: 5%;
}

.scroll-decoration--right {
  right: 5%;
}

.scroll-svg {
  height: 100%;
  width: 100%;
}

.hero-badge {
  align-items: center;
  background: linear-gradient(135deg, var(--color-primary-50), rgba(212, 175, 55, 0.1));
  border: 1px solid var(--color-primary-200);
  border-radius: var(--radius-pill);
  color: var(--color-primary-700);
  display: inline-flex;
  gap: 8px;
  margin-bottom: 24px;
  padding: 8px 20px;
  font-size: 14px;
}

.pricing-hero__title {
  font-family: var(--font-serif);
  font-size: clamp(36px, 5vw, 56px);
  font-weight: 700;
  line-height: 1.1;
  margin: 0 0 20px;
}

.title-accent {
  background: linear-gradient(90deg, var(--color-primary-600), #0891b2);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  display: block;
}

.pricing-hero__subtitle {
  color: var(--color-text-secondary);
  font-size: 18px;
  line-height: 1.6;
  margin: 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

/* Billing Toggle */
.billing-toggle-section {
  padding: 0 0 48px;
}

.billing-toggle {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  display: inline-flex;
  gap: 4px;
  margin: 0 auto;
  padding: 4px;
}

.billing-toggle button {
  align-items: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  gap: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.billing-toggle button:hover {
  color: var(--color-text-primary);
  background: var(--color-primary-50);
}

.billing-toggle button.active {
  background: var(--color-primary-600);
  color: white;
  box-shadow: var(--shadow-sm);
}

.discount-badge {
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-sm);
  font-size: 11px;
  padding: 2px 6px;
}

.billing-toggle button:not(.active) .discount-badge {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
}

/* Pricing Cards */
.pricing-cards-section {
  padding: 0 0 80px;
}

.pricing-grid {
  display: grid;
  gap: 32px;
  grid-template-columns: repeat(2, 1fr);
  max-width: 900px;
  margin: 0 auto;
}

.pricing-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.pricing-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-elevated);
}

.pricing-card--highlighted {
  border-color: var(--color-primary-200);
}

.pricing-card--pro {
  background: linear-gradient(180deg, var(--color-surface) 0%, rgba(16, 185, 129, 0.03) 100%);
  border: 2px solid var(--color-primary-400);
  transform: scale(1.02);
}

.pricing-card--pro:hover {
  transform: scale(1.02) translateY(-4px);
}

.popular-badge {
  align-items: center;
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-600));
  color: white;
  display: flex;
  gap: 6px;
  justify-content: center;
  padding: 10px;
  font-size: 13px;
  font-weight: 600;
}

.card-scroll-top,
.card-scroll-bottom {
  color: var(--color-primary-200);
  height: 30px;
}

.pricing-card--pro .card-scroll-top,
.pricing-card--pro .card-scroll-bottom {
  color: var(--color-primary-400);
}

.card-inner {
  padding: 32px;
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.plan-icon {
  align-items: center;
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: var(--radius-lg);
  display: inline-flex;
  height: 64px;
  justify-content: center;
  margin-bottom: 16px;
  width: 64px;
  color: var(--color-primary-600);
}

.plan-icon--pro {
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-600));
  border: none;
  color: white;
}

.plan-name {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 16px;
}

.plan-price {
  align-items: baseline;
  display: flex;
  gap: 4px;
  justify-content: center;
}

.price-original {
  color: var(--color-text-muted);
  font-size: 18px;
  text-decoration: line-through;
}

.price-amount {
  font-size: 48px;
  font-weight: 700;
  line-height: 1;
}

.price-period {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.save-badge {
  background: var(--color-primary-100);
  border-radius: var(--radius-sm);
  color: var(--color-primary-700);
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  margin-top: 8px;
  padding: 4px 12px;
}

.plan-desc {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 16px 0 0;
}

.feature-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.feature-item {
  align-items: center;
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 14px;
}

.feature-item:last-child {
  border-bottom: none;
}

.feature-icon {
  color: var(--color-primary-500);
  flex-shrink: 0;
}

.feature-item--pro .feature-icon {
  color: var(--color-primary-600);
}

.card-cta {
  margin-top: 32px;
}

/* Coins Section */
.coins-section {
  background: var(--color-surface-alt);
  padding: 80px 0;
}

.section-header {
  text-align: center;
  margin-bottom: 48px;
}

.section-icon {
  align-items: center;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(212, 175, 55, 0.2));
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: var(--radius-xl);
  display: inline-flex;
  height: 80px;
  justify-content: center;
  margin-bottom: 24px;
  width: 80px;
  color: #d4af37;
}

.section-title {
  font-family: var(--font-serif);
  font-size: clamp(28px, 3vw, 36px);
  margin: 0 0 12px;
}

.section-subtitle {
  color: var(--color-text-secondary);
  font-size: 16px;
  margin: 0;
}

.coins-grid {
  display: grid;
  gap: 24px;
  grid-template-columns: repeat(3, 1fr);
  max-width: 900px;
  margin: 0 auto;
}

.coin-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: 32px 24px;
  text-align: center;
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.coin-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card);
}

.coin-card--popular {
  border-color: var(--color-primary-400);
  background: linear-gradient(180deg, var(--color-surface) 0%, rgba(16, 185, 129, 0.05) 100%);
}

.coin-popular-badge {
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-600));
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  color: white;
  font-size: 12px;
  font-weight: 600;
  left: 50%;
  padding: 6px 16px;
  position: absolute;
  top: 0;
  transform: translateX(-50%);
}

.coin-icon {
  align-items: center;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(212, 175, 55, 0.2));
  border-radius: 50%;
  display: inline-flex;
  height: 80px;
  justify-content: center;
  margin-bottom: 16px;
  width: 80px;
  color: #d4af37;
}

.coin-amount {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.coin-label {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 4px 0 16px;
}

.coin-price {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
}

/* FAQ Section */
.faq-section {
  padding: 80px 0;
}

.faq-section .section-title {
  text-align: center;
  margin-bottom: 48px;
}

.faq-grid {
  display: grid;
  gap: 24px;
  grid-template-columns: repeat(2, 1fr);
  max-width: 900px;
  margin: 0 auto;
}

.faq-item {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.faq-item h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
}

.faq-item p {
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

/* CTA Section */
.pricing-cta {
  overflow: hidden;
  padding: 80px 0;
  position: relative;
}

.cta__overlay {
  background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-700));
  inset: 0;
  position: absolute;
}

.cta__inner {
  position: relative;
  text-align: center;
  z-index: 1;
}

.cta-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.cta-cloud {
  height: 200px;
  width: 200px;
  position: absolute;
  right: 10%;
  top: 20%;
  color: white;
}

.cta__badge {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-pill);
  color: white;
  display: inline-block;
  font-size: 14px;
  margin: 0;
  padding: 8px 20px;
}

.cta__inner h2 {
  color: white;
  font-family: var(--font-serif);
  font-size: clamp(28px, 3vw, 40px);
  margin: 24px 0 16px;
}

.cta__inner p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  margin: 0 0 32px;
}

/* Footer */
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

/* Responsive */
@media (max-width: 1024px) {
  .scroll-decoration {
    display: none;
  }

  .pricing-grid {
    max-width: 500px;
  }

  .coins-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .container {
    padding: 0 20px;
  }

  .site-nav--centered {
    display: none;
  }

  .header-auth {
    display: none;
  }

  .menu-toggle {
    display: block;
  }

  .mobile-nav--open {
    display: flex;
  }

  .pricing-hero {
    padding: 48px 0;
  }

  .billing-toggle {
    flex-direction: column;
    width: 100%;
  }

  .billing-toggle button {
    justify-content: center;
  }

  .pricing-grid {
    grid-template-columns: 1fr;
  }

  .pricing-card--pro {
    transform: none;
  }

  .pricing-card--pro:hover {
    transform: translateY(-4px);
  }

  .coins-grid {
    grid-template-columns: 1fr;
    max-width: 300px;
  }

  .faq-grid {
    grid-template-columns: 1fr;
  }
}

/* Purchase Modal */
.purchase-modal-overlay {
  align-items: center;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  inset: 0;
  justify-content: center;
  position: fixed;
  z-index: 1000;
}

.purchase-modal {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-elevated);
  max-width: 400px;
  width: 90%;
}

.purchase-modal__header {
  align-items: center;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  padding: 20px 24px;
}

.purchase-modal__header h3 {
  font-family: var(--font-serif);
  font-size: 20px;
  margin: 0;
}

.purchase-modal__close {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 24px;
  line-height: 1;
  padding: 0;
}

.purchase-modal__body {
  padding: 24px;
}

.purchase-offer {
  align-items: center;
  background: var(--color-surface-alt);
  border-radius: var(--radius-md);
  display: flex;
  gap: 16px;
  padding: 20px;
}

.purchase-offer__icon {
  font-size: 40px;
}

.purchase-offer__amount {
  font-size: 24px;
  font-weight: 700;
}

.purchase-offer__price {
  color: var(--color-primary-600);
  font-size: 18px;
  font-weight: 600;
}

.purchase-modal__note {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 16px 0 0;
  text-align: center;
}

.purchase-modal__error {
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
  color: #ef4444;
  font-size: 14px;
  margin-top: 12px;
  padding: 12px;
}

.purchase-modal__footer {
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px;
}

/* Modal transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
