export type BillingCycle = "monthly" | "quarterly" | "yearly";

export type PlanType = "free" | "pro";

export type PricingConfig = {
  plans: Record<BillingCycle, Record<PlanType, number>>;
  discounts: Record<Exclude<BillingCycle, "monthly">, number>;
  originalPrices: Record<Exclude<BillingCycle, "monthly">, number>;
};

export type CoinPackage = {
  coins: number;
  price: number;
  popular: boolean;
};

export const PRICING_CONFIG: PricingConfig = {
  plans: {
    monthly: { free: 0, pro: 8 },
    quarterly: { free: 0, pro: 20 },
    yearly: { free: 0, pro: 70 },
  },
  discounts: {
    quarterly: 17,
    yearly: 27,
  },
  originalPrices: {
    quarterly: 24,
    yearly: 96,
  },
};

export const COIN_PACKAGES: CoinPackage[] = [
  { coins: 60, price: 6, popular: false },
  { coins: 300, price: 30, popular: true },
  { coins: 680, price: 68, popular: false },
  { coins: 1500, price: 120, popular: false },
  { coins: 3500, price: 245, popular: false },
];

export const PRICING_FEATURES = {
  showDiscountBadges: true,
  enableQuarterlyBilling: true,
  enableYearlyBilling: true,
  showSaveBadge: true,
  showOriginalPrice: true,
} as const;
