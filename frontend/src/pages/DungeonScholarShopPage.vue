<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  getShopBalance as getBalance,
  listShopItems,
  purchaseShopItem,
  useItem,
  type ShopOffer,
} from "../api/shop";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import ShopHeader from "../components/shop/ShopHeader.vue";
import ShopItemCard from "../components/shop/ShopItemCard.vue";
import CoinPackTopUpModal from "../components/shop/modals/CoinPackTopUpModal.vue";
import ItemUseConfirmModal from "../components/shop/modals/ItemUseConfirmModal.vue";
import { useInventory } from "../composables/useInventory";

type ShopItem = {
  offerId: string;
  name: string;
  rarity: string;
  price: number;
  icon: string;
  description: string;
  accent: "teal" | "violet" | "rose" | "amber";
  itemCode: string;
  isCoinPack?: boolean;
};

const router = useRouter();
const { t, locale } = useI18n();

const walletBalance = ref(0);
const shopItems = ref<ShopItem[]>([]);
const rawOffers = ref<ShopOffer[]>([]);
const purchaseError = ref<string | null>(null);
const isLoading = ref(false);
const isPurchasing = ref(false);
const showTopUpModal = ref(false);
const showBagModal = ref(false);
const selectedItem = ref<ShopItem | null>(null);
const showUseConfirmModal = ref(false);
const selectedInventoryItem = ref<{ itemCode: string; name: string; description: string; quantity: number } | null>(null);

const { inventory, refresh: refreshInventory, quantityOf } = useInventory();

const iconMap: Record<string, string> = {
  streak_freeze: "🛡️",
  xp_boost_1_5x: "⚡",
  xp_boost_2x: "⚡",
  xp_boost_3x: "⚡",
  revival: "🔄",
  time_treasure: "⏳",
  coin_pack: "💎",
};

const rarityAccentMap: Record<string, "teal" | "violet" | "rose" | "amber"> = {
  common: "teal",
  uncommon: "violet",
  rare: "rose",
  legendary: "amber",
};

const rarityLabel = (rarity: string): string => {
  const rarityLower = rarity.toLowerCase();
  if (rarityLower === "uncommon") return t("shop.items.uncommon");
  if (rarityLower === "rare") return t("shop.items.rare");
  if (rarityLower === "legendary") return t("shop.items.rescue");
  return t("shop.items.common");
};

const itemLocalization = (itemCode: string): { name: string; description: string } => {
  const key = itemCode.replace(/_[\d]?x$/, "_boost").replace(/_/g, ".");
  const names: Record<string, string> = {
    "streak.freeze": t("shop.items.streakFreeze.name"),
    "xp.boost": t("shop.items.xpBoost.name"),
    "abyss.revive": t("shop.items.abyssRevive.name"),
    "coin.pack": t("shop.items.coinPack.name"),
  };
  const descs: Record<string, string> = {
    "streak.freeze": t("shop.items.streakFreeze.desc"),
    "xp.boost": t("shop.items.xpBoost.desc"),
    "abyss.revive": t("shop.items.abyssRevive.desc"),
    "coin.pack": t("shop.items.coinPack.desc"),
  };
  return {
    name: names[key] || t(`shop.items.${key.replace(/\./g, "")}.name`) || itemCode,
    description: descs[key] || t(`shop.items.${key.replace(/\./g, "")}.desc`) || "",
  };
};

const mapOfferToShopItem = (offer: ShopOffer): ShopItem => {
  const itemCode = offer.item_code || "";
  const rarityLower = (offer.rarity || "common").toLowerCase();
  const isCoinPack = itemCode.startsWith("coin_pack");
  const localized = itemLocalization(itemCode);
  return {
    offerId: offer.id,
    name: localized.name || offer.display_name || itemCode,
    rarity: rarityLabel(offer.rarity || "common"),
    price: offer.price_amount || 0,
    icon: iconMap[itemCode] || (isCoinPack ? "💎" : "📦"),
    description: localized.description,
    accent: isCoinPack ? "amber" : (rarityAccentMap[rarityLower] || "teal"),
    itemCode,
    isCoinPack,
  };
};

const rebuildShopItems = () => {
  shopItems.value = rawOffers.value.map(mapOfferToShopItem);
};

const fetchBalance = async () => {
  try {
    const balance = await getBalance();
    const normalizedBalance = balance as { asset_code: string; balance: number };
    walletBalance.value = normalizedBalance.balance || 0;
  } catch (error) {
    console.error("Failed to fetch balance:", error);
    walletBalance.value = 0;
  }
};

const fetchShopItems = async () => {
  isLoading.value = true;
  try {
    const offers = await listShopItems();
    rawOffers.value = offers as ShopOffer[];
    rebuildShopItems();
  } catch (error) {
    console.error("Failed to fetch shop items:", error);
    rawOffers.value = [];
    shopItems.value = [];
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  document.title = t("shop.metaTitle");
  await Promise.all([fetchBalance(), fetchShopItems(), refreshInventory()]);
});

watch(locale, () => {
  document.title = t("shop.metaTitle");
  rebuildShopItems();
});

const goBack = async () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  await router.push("/home");
};

const handlePurchaseItemCode = async (itemCode: string) => {
  const item = shopItems.value.find((i) => i.itemCode === itemCode);
  if (!item) return;
  await handlePurchase(item);
};

const handlePurchase = async (item: ShopItem) => {
  if (isPurchasing.value) return;

  if (item.isCoinPack) {
    showTopUpModal.value = true;
    return;
  }

  if (walletBalance.value < item.price) {
    selectedItem.value = item;
    showTopUpModal.value = true;
    return;
  }

  isPurchasing.value = true;
  purchaseError.value = null;

  try {
    await purchaseShopItem({
      offerId: item.offerId,
      idempotencyKey: "purchase-" + Date.now() + "-" + item.offerId,
    });
    await Promise.all([fetchBalance(), fetchShopItems(), refreshInventory()]);
  } catch (error) {
    console.error("Purchase failed:", error);
    purchaseError.value = t("shop.errors.purchaseFailed");
  } finally {
    isPurchasing.value = false;
  }
};

const handleTopUpPurchase = async (offerId: string) => {
  isPurchasing.value = true;
  try {
    await purchaseShopItem({
      offerId,
      idempotencyKey: "purchase-" + Date.now() + "-" + offerId,
    });
    showTopUpModal.value = false;
    await Promise.all([fetchBalance(), fetchShopItems()]);
  } catch (error) {
    console.error("Top-up failed:", error);
    purchaseError.value = t("shop.errors.purchaseFailed");
  } finally {
    isPurchasing.value = false;
  }
};

const openBag = async () => {
  await refreshInventory();
  showBagModal.value = true;
};

const handleUseItem = (itemCode: string, name: string, description: string) => {
  selectedInventoryItem.value = {
    itemCode,
    name,
    description,
    quantity: quantityOf(itemCode),
  };
  showUseConfirmModal.value = true;
};

const confirmUseItem = async () => {
  if (!selectedInventoryItem.value) return;
  try {
    await useItem({ itemCode: selectedInventoryItem.value.itemCode });
    showUseConfirmModal.value = false;
    selectedInventoryItem.value = null;
    await refreshInventory();
  } catch (error) {
    console.error("Use item failed:", error);
  }
};

const inventoryItems = computed(() => {
  return inventory.value
    .filter((i) => i.quantity > 0)
    .map((i) => {
      const localized = itemLocalization(i.item_code);
      return {
        itemCode: i.item_code,
        name: localized.name || i.item_code,
        description: localized.description,
        quantity: i.quantity,
        icon: iconMap[i.item_code] || "📦",
      };
    });
});

const coinPacks = computed(() => shopItems.value.filter((i) => i.isCoinPack));
const toolItems = computed(() => shopItems.value.filter((i) => !i.isCoinPack));

defineExpose({
  walletBalance,
});
</script>

<template>
  <main class="shop-page">
    <section class="shop-shell" :aria-label="t('shop.heroEyebrow')">
      <ShopHeader :wallet-balance="walletBalance" :on-open-bag="openBag" />

      <section class="shop-hero">
        <div>
          <p class="shop-hero__eyebrow">{{ t("shop.heroEyebrow") }}</p>
          <h1>{{ t("shop.heroTitle") }}</h1>
          <p>{{ t("shop.heroDesc") }}</p>
        </div>

        <div class="shop-hero__actions">
          <button class="back-btn" type="button" :aria-label="t('shop.goBack')" @click="goBack">←</button>
          <div class="shop-filters">
            <span class="filter-chip filter-chip--teal">✦ {{ t("shop.newArrivals") }}</span>
            <span class="filter-chip filter-chip--amber">🔥 {{ t("shop.hotItems") }}</span>
          </div>
        </div>
      </section>

      <div class="shop-divider" />

      <section class="shop-grid" :aria-label="t('shop.itemsAria')">
        <ShopItemCard
          v-for="item in coinPacks"
          :key="item.offerId"
          :name="item.name"
          :price="item.price"
          :icon="item.icon"
          :accent="item.accent"
          :item-code="item.itemCode"
          :price-is-cash="true"
          :tag="t('shop.topUp')"
          :description="item.description"
          @purchase="handlePurchaseItemCode"
        />
        <ShopItemCard
          v-for="item in toolItems"
          :key="item.offerId"
          :name="item.name"
          :price="item.price"
          :icon="item.icon"
          :accent="item.accent"
          :item-code="item.itemCode"
          :tag="item.rarity"
          :description="item.description"
          @purchase="handlePurchaseItemCode"
        />
      </section>

      <footer class="shop-footer">
        <small>{{ t("shop.copyright") }}</small>
        <nav class="shop-footer__links" :aria-label="t('shop.footerLinksAria')">
          <a href="#">{{ t("shop.terms") }}</a>
          <a href="#">{{ t("shop.privacy") }}</a>
          <a href="#">{{ t("shop.support") }}</a>
        </nav>
      </footer>
    </section>

    <CoinPackTopUpModal
      :visible="showTopUpModal"
      :offers="coinPacks.map((c) => ({ id: c.offerId, coin_amount: c.price * 10, price_usd: c.price, label: c.name }))"
      @purchase="handleTopUpPurchase"
      @close="showTopUpModal = false"
    />

    <ItemUseConfirmModal
      :visible="showUseConfirmModal"
      :item-name="selectedInventoryItem?.name || ''"
      :item-description="selectedInventoryItem?.description || ''"
      :quantity="selectedInventoryItem?.quantity || 0"
      @confirm="confirmUseItem"
      @cancel="showUseConfirmModal = false"
      @close="showUseConfirmModal = false"
    />

    <transition name="modal-fade">
      <div v-if="showBagModal" class="bag-modal-overlay" @click="showBagModal = false">
        <section class="bag-modal" @click.stop>
          <header class="bag-modal__header">
            <h2>{{ t("shop.inventoryBag") }}</h2>
            <button class="close-btn" type="button" @click="showBagModal = false">✕</button>
          </header>
          <div class="bag-modal__body">
            <div v-if="inventoryItems.length === 0" class="bag-empty">
              <p>{{ t("shop.bagEmpty") }}</p>
            </div>
            <div v-else class="bag-grid">
              <article
                v-for="item in inventoryItems"
                :key="item.itemCode"
                class="bag-item"
              >
                <span class="bag-item__icon">{{ item.icon }}</span>
                <div class="bag-item__info">
                  <strong>{{ item.name }}</strong>
                  <span>{{ t("shop.inInventory", { n: item.quantity }) }}</span>
                </div>
                <button
                  class="use-btn"
                  type="button"
                  @click="handleUseItem(item.itemCode, item.name, item.description)"
                >
                  {{ t("shop.use") }}
                </button>
              </article>
            </div>
          </div>
        </section>
      </div>
    </transition>
  </main>
</template>

<style scoped>
.shop-page {
  background: #f4f4f1;
  min-height: 100vh;
  padding: 16px;
}

.shop-shell {
  background: linear-gradient(180deg, #f7f7f5, #f4f4f1);
  border: 1px solid #dddeda;
  min-height: calc(100vh - 32px);
}

.back-btn {
  align-items: center;
  background: #ffffff;
  border: 1px solid #dde1e4;
  border-radius: 12px;
  color: #5b6b78;
  cursor: pointer;
  display: inline-flex;
  font-size: 20px;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.shop-hero {
  align-items: end;
  display: flex;
  justify-content: space-between;
  padding: 22px 38px 0;
}

.shop-hero__actions {
  align-items: flex-end;
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 184px;
}

.shop-hero__eyebrow {
  color: #b2b7bb;
  font-size: 12px;
  margin: 0 0 10px;
}

.shop-hero h1 {
  color: #15979f;
  font-size: clamp(50px, 5vw, 66px);
  letter-spacing: -0.04em;
  line-height: 0.95;
  margin: 0;
}

.shop-hero p {
  color: #6f7782;
  font-size: 16px;
  line-height: 1.45;
  margin: 16px 0 0;
  max-width: 620px;
}

.shop-filters {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-bottom: 14px;
  width: 100%;
}

.filter-chip {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  font-size: 12px;
  font-weight: 700;
  justify-content: center;
  line-height: 1;
  min-height: 36px;
  min-width: 108px;
  padding: 0 16px;
  white-space: nowrap;
}

.filter-chip--teal {
  background: #dcfce7;
  color: #0f766e;
}

.filter-chip--amber {
  background: #ffedd5;
  color: #ea580c;
}

.shop-divider {
  border-top: 1px solid #d8dddf;
  margin: 26px 38px 0;
}

.shop-grid {
  display: grid;
  gap: 22px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 38px;
}

.shop-footer {
  align-items: center;
  border-top: 1px solid #d8dddf;
  color: #8a8f98;
  display: flex;
  font-size: 12px;
  justify-content: space-between;
  margin-top: 46px;
  padding: 20px 18px 26px;
}

.shop-footer__links {
  display: flex;
  gap: 22px;
}

.shop-footer__links a {
  color: inherit;
  text-decoration: none;
}

.bag-modal-overlay {
  align-items: center;
  background: rgba(0, 0, 0, 0.5);
  bottom: 0;
  display: flex;
  justify-content: center;
  left: 0;
  position: fixed;
  right: 0;
  top: 0;
  z-index: 1000;
}

.bag-modal {
  background: #ffffff;
  border-radius: 18px;
  max-width: 480px;
  padding: 24px;
  width: 90%;
}

.bag-modal__header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.bag-modal__header h2 {
  color: #2c3848;
  font-size: 20px;
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  color: #9aa4b2;
  cursor: pointer;
  font-size: 20px;
}

.bag-modal__body {
  max-height: 400px;
  overflow-y: auto;
}

.bag-empty {
  color: #9aa4b2;
  padding: 40px;
  text-align: center;
}

.bag-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bag-item {
  align-items: center;
  background: #f7f7f5;
  border-radius: 12px;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
}

.bag-item__icon {
  font-size: 32px;
}

.bag-item__info {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.bag-item__info strong {
  color: #2c3848;
  font-size: 14px;
}

.bag-item__info span {
  color: #9aa4b2;
  font-size: 12px;
}

.use-btn {
  background: linear-gradient(90deg, #1098a5, #14b8a6);
  border: none;
  border-radius: 999px;
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 16px;
}

@media (max-width: 1100px) {
  .shop-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .shop-page {
    padding: 10px;
  }

  .shop-hero,
  .shop-grid {
    padding-left: 16px;
    padding-right: 16px;
  }

  .shop-hero {
    align-items: start;
    flex-direction: column;
    gap: 16px;
  }

  .shop-hero__actions {
    align-items: start;
    width: auto;
  }

  .shop-filters {
    justify-content: flex-start;
  }

  .shop-divider {
    margin-left: 16px;
    margin-right: 16px;
  }

  .shop-footer {
    align-items: start;
    flex-direction: column;
    gap: 12px;
  }
}
</style>
