<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { PRICING_CONFIG } from "../../config/pricing";
import { createCheckout, type PricingRegion } from "../../api/payments";

type CountryOption = {
  code: string;
  name: string;
  region: PricingRegion;
};

const COUNTRY_OPTIONS: CountryOption[] = [
  { code: "CN", name: "中国", region: "standard" },
  { code: "US", name: "美国", region: "premium" },
  { code: "GB", name: "英国", region: "premium" },
  { code: "CA", name: "加拿大", region: "premium" },
  { code: "AU", name: "澳大利亚", region: "premium" },
  { code: "DE", name: "德国", region: "premium" },
  { code: "FR", name: "法国", region: "premium" },
  { code: "JP", name: "日本", region: "premium" },
  { code: "SG", name: "新加坡", region: "premium" },
  { code: "NL", name: "荷兰", region: "premium" },
  { code: "SE", name: "瑞典", region: "premium" },
  { code: "CH", name: "瑞士", region: "premium" },
  { code: "NO", name: "挪威", region: "premium" },
  { code: "DK", name: "丹麦", region: "premium" },
  { code: "FI", name: "芬兰", region: "premium" },
  { code: "IE", name: "爱尔兰", region: "premium" },
  { code: "NZ", name: "新西兰", region: "premium" },
  { code: "BE", name: "比利时", region: "premium" },
  { code: "AT", name: "奥地利", region: "premium" },
  { code: "IT", name: "意大利", region: "premium" },
  { code: "ES", name: "西班牙", region: "premium" },
  { code: "IN", name: "印度", region: "developing" },
  { code: "ID", name: "印度尼西亚", region: "developing" },
  { code: "PH", name: "菲律宾", region: "developing" },
  { code: "VN", name: "越南", region: "developing" },
  { code: "TH", name: "泰国", region: "developing" },
  { code: "MY", name: "马来西亚", region: "developing" },
  { code: "BR", name: "巴西", region: "developing" },
  { code: "MX", name: "墨西哥", region: "developing" },
  { code: "AR", name: "阿根廷", region: "developing" },
  { code: "CO", name: "哥伦比亚", region: "developing" },
  { code: "PE", name: "秘鲁", region: "developing" },
  { code: "EG", name: "埃及", region: "developing" },
  { code: "NG", name: "尼日利亚", region: "developing" },
  { code: "KE", name: "肯尼亚", region: "developing" },
  { code: "PK", name: "巴基斯坦", region: "developing" },
  { code: "BD", name: "孟加拉国", region: "developing" },
  { code: "UA", name: "乌克兰", region: "developing" },
  { code: "RO", name: "罗马尼亚", region: "developing" },
  { code: "BG", name: "保加利亚", region: "developing" },
];

const REGION_LABELS: Record<PricingRegion, string> = {
  premium: "高价地区",
  standard: "标准地区",
  developing: "发展中地区",
};

const props = defineProps<{
  visible: boolean;
  subscriptionStatus: string;
  selectedRegion: PricingRegion;
  regionPrices: Record<string, number>;
}>();

const emit = defineEmits<{
  close: [];
  cancelSubscription: [];
  updateRegion: [region: PricingRegion];
}>();

const { t } = useI18n();
const isUpgrading = ref(false);
const upgradeError = ref<string | null>(null);
const isSubscriptionPausedForValidation = true;

const plans = PRICING_CONFIG.plans;
const currentPlan = props.subscriptionStatus === "active" ? "pro" : "free";

const currentCountry = computed(() => {
  return COUNTRY_OPTIONS.find((c) => c.region === props.selectedRegion) || COUNTRY_OPTIONS[0];
});

const selectedCountryCode = ref(currentCountry.value.code);

const freeFeatures = computed(() => [
  t("pricing.freeFeature1", "基础学习功能"),
  t("pricing.freeFeature2", "每日任务挑战"),
  t("pricing.freeFeature3", "社区排行榜"),
]);

const proFeatures = computed(() => [
  t("pricing.proFeature1", "所有免费功能"),
  t("pricing.proFeature2", "无限文档上传"),
  t("pricing.proFeature3", "高级 AI 分析"),
  t("pricing.proFeature4", "优先客服支持"),
]);

const handleUpgrade = async () => {
  if (isSubscriptionPausedForValidation) return;
  if (isUpgrading.value) return;
  isUpgrading.value = true;
  upgradeError.value = null;
  try {
    const checkout = await createCheckout({ productType: "subscription", plan: "monthly" });
    window.location.href = checkout.checkout_url;
  } catch (error) {
    console.error("Upgrade failed:", error);
    upgradeError.value = error instanceof Error ? error.message : "升级失败，请稍后重试";
  } finally {
    isUpgrading.value = false;
  }
};

const handleCountryChange = (event: Event) => {
  const target = event.target as HTMLSelectElement;
  const country = COUNTRY_OPTIONS.find((c) => c.code === target.value);
  if (country) {
    selectedCountryCode.value = country.code;
    emit("updateRegion", country.region);
  }
};
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="subscription-overlay" @click="emit('close')">
      <section class="subscription-modal" data-testid="subscription-modal" @click.stop>
        <header class="subscription-modal__header">
          <h2>{{ t("settings.subscriptionModal.title", "订阅管理") }}</h2>
          <button class="close-btn" type="button" :aria-label="t('common.closeAria', 'Close')" @click="emit('close')">✕</button>
        </header>

        <div class="subscription-modal__plans">
          <article
            class="plan-card"
            :class="{ 'plan-card--current': currentPlan === 'free' }"
            data-testid="plan-card-free"
          >
            <div v-if="currentPlan === 'free'" class="plan-card__badge">
              {{ t("settings.subscriptionModal.currentPlan", "当前方案") }}
            </div>
            <h3 class="plan-card__name">{{ t("pricing.freePlan") }}</h3>
            <p class="plan-card__price">$0</p>
            <p class="plan-card__desc">{{ t("pricing.freeDesc") }}</p>
            <ul class="plan-card__features">
              <li v-for="(feature, index) in freeFeatures" :key="index">{{ feature }}</li>
            </ul>
          </article>

          <article
            class="plan-card plan-card--pro"
            :class="{ 'plan-card--current': currentPlan === 'pro' }"
            data-testid="plan-card-pro"
          >
            <div v-if="currentPlan === 'pro'" class="plan-card__badge">
              {{ t("settings.subscriptionModal.currentPlan", "当前方案") }}
            </div>
            <h3 class="plan-card__name">{{ t("pricing.proPlan") }}</h3>
            <p class="plan-card__price">${{ regionPrices.monthly || plans.monthly.pro }}<span class="plan-card__period">/{{ t("pricing.monthly") }}</span></p>
            <p class="plan-card__desc">{{ t("pricing.proDesc") }}</p>
            <ul class="plan-card__features">
              <li v-for="(feature, index) in proFeatures" :key="index">{{ feature }}</li>
            </ul>
            <button
              v-if="currentPlan === 'free'"
              class="plan-card__cta plan-card__cta--upgrade"
              type="button"
              :disabled="isSubscriptionPausedForValidation || isUpgrading"
              data-testid="upgrade-pro"
              @click="handleUpgrade"
            >
              {{ isSubscriptionPausedForValidation ? t("pricing.validationPausedTitle") : isUpgrading ? t("common.processing", "处理中...") : t("settings.subscriptionModal.upgradePro", "升级到 Pro") }}
            </button>
            <p v-if="isSubscriptionPausedForValidation" class="plan-card__paused">
              {{ t("pricing.validationPausedBody") }}
            </p>
            <p v-if="upgradeError" class="plan-card__error">{{ upgradeError }}</p>
            <div v-else class="plan-card__active-info">
              <span class="plan-card__status">{{ t("settings.subscriptionModal.statusActive", "已启用") }}</span>
              <button
                class="plan-card__cta plan-card__cta--cancel"
                type="button"
                data-testid="cancel-subscription"
                @click="emit('cancelSubscription')"
              >
                {{ t("settings.subscriptionModal.cancelSubscription", "取消订阅") }}
              </button>
            </div>
          </article>
        </div>

        <div class="subscription-modal__region">
          <h3>{{ t("settings.subscriptionModal.regionTitle", "定价地区") }}</h3>
          <p class="subscription-modal__region-hint">
            {{ t("settings.subscriptionModal.regionHint", "检测到您在") }} {{ currentCountry.name }}
            <span class="subscription-modal__region-tag">({{ REGION_LABELS[selectedRegion] }})</span>
          </p>
          <p class="subscription-modal__region-desc">{{ t("settings.subscriptionModal.regionDesc", "选择您所在的国家/地区，价格将自动更新。") }}</p>
          <div class="region-row">
            <select :value="selectedCountryCode" data-testid="country-select" @change="handleCountryChange">
              <option v-for="country in COUNTRY_OPTIONS" :key="country.code" :value="country.code">
                {{ country.name }}
              </option>
            </select>
          </div>
        </div>
      </section>
    </div>
  </transition>
</template>

<style scoped>
.subscription-overlay {
  align-items: center;
  background: rgba(15, 23, 42, 0.5);
  inset: 0;
  display: flex;
  justify-content: center;
  padding: 20px;
  position: fixed;
  z-index: 1100;
}

.subscription-modal {
  background: #ffffff;
  border: 1px solid #e7e5e4;
  border-radius: 16px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
  max-width: 780px;
  padding: 24px;
  width: min(780px, 100%);
  max-height: 90vh;
  overflow-y: auto;
}

.subscription-modal__header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.subscription-modal__header h2 {
  color: #1f2937;
  font-family: var(--font-serif);
  font-size: 28px;
  margin: 0;
}

.close-btn {
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 999px;
  color: #6b7280;
  cursor: pointer;
  height: 34px;
  width: 34px;
  font-size: 16px;
}

.subscription-modal__plans {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 24px;
}

.plan-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  position: relative;
  transition: border-color 0.2s;
}

.plan-card--current {
  border-color: #0d9488;
  background: #f0fdfa;
}

.plan-card--pro {
  border-color: #d4af37;
}

.plan-card--pro.plan-card--current {
  border-color: #0d9488;
}

.plan-card__badge {
  background: #0d9488;
  border-radius: 999px;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  position: absolute;
  right: 12px;
  top: 12px;
}

.plan-card__name {
  color: #1f2937;
  font-family: var(--font-serif);
  font-size: 22px;
  margin: 0 0 8px;
}

.plan-card__price {
  color: #111827;
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px;
}

.plan-card__period {
  color: #6b7280;
  font-size: 14px;
  font-weight: 400;
}

.plan-card__desc {
  color: #6b7280;
  font-size: 13px;
  margin: 0 0 12px;
}

.plan-card__features {
  color: #374151;
  font-size: 13px;
  list-style: none;
  margin: 0 0 16px;
  padding: 0;
}

.plan-card__features li {
  padding: 3px 0;
}

.plan-card__features li::before {
  content: "✓ ";
  color: #0d9488;
  font-weight: 700;
}

.plan-card__cta {
  border: 0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  min-height: 40px;
  padding: 0 20px;
  width: 100%;
}

.plan-card__cta--upgrade {
  background: linear-gradient(90deg, #d97706, #ea580c);
  color: #ffffff;
}

.plan-card__cta--upgrade:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.plan-card__error {
  color: #ef4444;
  font-size: 12px;
  margin: 8px 0 0;
  text-align: center;
}

.plan-card__paused {
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.5;
  margin: 8px 0 0;
  text-align: center;
}

.plan-card__cta--cancel {
  background: transparent;
  border: 1px solid #ef4444;
  color: #ef4444;
  margin-top: 8px;
}

.plan-card__active-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.plan-card__status {
  color: #15803d;
  font-size: 13px;
  font-weight: 700;
}

.subscription-modal__region {
  border-top: 1px solid #e5e7eb;
  padding-top: 20px;
}

.subscription-modal__region h3 {
  color: #1f2937;
  font-size: 16px;
  margin: 0 0 4px;
}

.subscription-modal__region-hint {
  color: #0d9488;
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 4px;
}

.subscription-modal__region-tag {
  color: #6b7280;
  font-weight: 400;
}

.subscription-modal__region-desc {
  color: #6b7280;
  font-size: 13px;
  margin: 0 0 12px;
}

.region-row {
  align-items: center;
  display: flex;
  gap: 10px;
}

.region-row select {
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  color: #1f2937;
  font: inherit;
  min-height: 36px;
  min-width: 200px;
  padding: 0 10px;
}

@media (max-width: 640px) {
  .subscription-modal__plans {
    grid-template-columns: 1fr;
  }

  .region-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
