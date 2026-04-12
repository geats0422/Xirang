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
    monthly: { free: 0, pro: 35 },
    quarterly: { free: 0, pro: 90 },
    yearly: { free: 0, pro: 300 },
  },
  discounts: {
    quarterly: 10,
    yearly: 20,
  },
  originalPrices: {
    quarterly: 100,
    yearly: 360,
  },
};

export const COIN_PACKAGES: CoinPackage[] = [
  { coins: 60, price: 6, popular: false },
  { coins: 300, price: 30, popular: true },
  { coins: 680, price: 68, popular: false },
];

export const PRICING_FEATURES = {
  showDiscountBadges: true,
  enableQuarterlyBilling: true,
  enableYearlyBilling: true,
  showSaveBadge: true,
  showOriginalPrice: true,
} as const;
