import { ref, computed } from "vue";
import { useI18n } from "vue-i18n";
import { purchaseShopItem, type PurchaseShopItemResponse } from "../api/shop";
import { useToast } from "./useToast";

export type CoinOffer = {
  id: string;
  coin_amount: number;
  price_usd: number;
  label: string;
  recommended: boolean;
};

const DEFAULT_OFFERS: CoinOffer[] = [
  { id: "coin_pack_small", coin_amount: 60, price_usd: 6, label: "灵钱宝匣·小", recommended: false },
  { id: "coin_pack_medium", coin_amount: 300, price_usd: 30, label: "灵钱宝匣·中", recommended: true },
  { id: "coin_pack_large", coin_amount: 680, price_usd: 68, label: "灵钱宝匣·大", recommended: false },
];

const showPurchaseModal = ref(false);
const selectedOffer = ref<CoinOffer | null>(null);
const isPurchasing = ref(false);
const purchaseError = ref<string | null>(null);
const lastPurchaseResult = ref<PurchaseShopItemResponse | null>(null);

export function useCoinPurchase() {
  const { t } = useI18n();
  const { success: showSuccess, error: showError } = useToast();

  const coinOffers = computed<CoinOffer[]>(() => DEFAULT_OFFERS);

  const openPurchaseModal = (offer: CoinOffer) => {
    selectedOffer.value = offer;
    purchaseError.value = null;
    showPurchaseModal.value = true;
  };

  const closePurchaseModal = () => {
    showPurchaseModal.value = false;
    selectedOffer.value = null;
    purchaseError.value = null;
  };

  const confirmPurchase = async (): Promise<boolean> => {
    if (!selectedOffer.value) return false;

    isPurchasing.value = true;
    purchaseError.value = null;

    try {
      const result = await purchaseShopItem({
        offerId: selectedOffer.value.id,
        idempotencyKey: `${selectedOffer.value.id}-${Date.now()}`,
      });

      lastPurchaseResult.value = result;
      showPurchaseModal.value = false;
      showSuccess(t("shop.purchaseSuccess", "购买成功！代币已到账"));
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      purchaseError.value = message;
      showError(t("shop.purchaseFailed", "购买失败，请重试"));
      return false;
    } finally {
      isPurchasing.value = false;
    }
  };

  const quickPurchase = async (offerId: string): Promise<boolean> => {
    const offer = coinOffers.value.find((o) => o.id === offerId);
    if (!offer) {
      showError(t("shop.offerNotFound", "找不到该套餐"));
      return false;
    }
    openPurchaseModal(offer);
    return true;
  };

  return {
    coinOffers,
    showPurchaseModal,
    selectedOffer,
    isPurchasing,
    purchaseError,
    lastPurchaseResult,
    openPurchaseModal,
    closePurchaseModal,
    confirmPurchase,
    quickPurchase,
  };
}
