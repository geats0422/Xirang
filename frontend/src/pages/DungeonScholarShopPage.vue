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
  rarityKey: "common" | "uncommon" | "rare" | "legendary";
  price: number;
  icon: string;
  description: string;
  accent: "teal" | "violet" | "rose" | "amber";
  itemCode: string;
  isCoinPack?: boolean;
};

const router = useRouter();
const { t, te, locale } = useI18n();
const isZhLocale = computed(() => locale.value.startsWith("zh"));

const walletBalance = ref(0);
const shopItems = ref<ShopItem[]>([]);
const rawOffers = ref<ShopOffer[]>([]);
const purchaseError = ref<string | null>(null);
const isLoading = ref(false);
const isPurchasing = ref(false);
const showTopUpModal = ref(false);
const showBagModal = ref(false);
const selectedItem = ref<ShopItem | null>(null);
const showPurchaseConfirmModal = ref(false);
const showTopUpConfirmModal = ref(false);
const showUseConfirmModal = ref(false);
const selectedInventoryItem = ref<{ itemCode: string; name: string; description: string; quantity: number } | null>(null);
const selectedTopUpOffer = ref<{ id: string; coin_amount: number; price_usd: number; label: string } | null>(null);

const { inventory, refresh: refreshInventory, quantityOf } = useInventory();

const iconMap: Record<string, string> = {
  streak_freeze: "❄",
  xp_boost: "⚗",
  xp_boost_1_5: "⚗",
  xp_boost_1_5x: "⚗",
  xp_boost_2: "⚗",
  xp_boost_2x: "⚗",
  xp_boost_3: "⚗",
  xp_boost_3x: "⚗",
  abyss_revive: "♡",
  revival: "♡",
  time_treasure: "⌛",
  coin_pack: "◈",
};

const rarityAccentMap: Record<string, "teal" | "violet" | "rose" | "amber"> = {
  common: "teal",
  uncommon: "violet",
  rare: "rose",
  legendary: "amber",
};

const rarityLabel = (rarity: string): string => {
  const rarityLower = rarity.toLowerCase();
  if (rarityLower === "uncommon") return translateOr("shop.items.uncommon", "稀有");
  if (rarityLower === "rare") return translateOr("shop.items.rare", "珍稀");
  if (rarityLower === "legendary") return translateOr("shop.items.legendary", "传说");
  return translateOr("shop.items.common", "普通");
};

function translateOr(key: string, fallback: string): string {
  if (!te(key)) return fallback;
  return t(key);
}

const inventoryCountLabel = (count: number): string => {
  return translateOr("shop.inInventory", `库存 x${count}`).replace("{n}", String(count));
};

const itemCatalog: Record<string, { name: string; description: string }> = {
  streak_freeze: {
    name: "玄霜护印",
    description: "当日未学习时可护住连胜，不中断打卡。",
  },
  xp_boost_1_5: {
    name: "悟道灵液·一阶",
    description: "学习与错题复习经验提升至 1.5 倍，可叠加时长。",
  },
  xp_boost_1_5x: {
    name: "悟道灵液·一阶",
    description: "学习与错题复习经验提升至 1.5 倍，可叠加时长。",
  },
  xp_boost_2: {
    name: "悟道灵液·二阶",
    description: "学习与错题复习经验提升至 2 倍，可叠加时长。",
  },
  xp_boost_2x: {
    name: "悟道灵液·二阶",
    description: "学习与错题复习经验提升至 2 倍，可叠加时长。",
  },
  xp_boost_3: {
    name: "悟道灵液·三阶",
    description: "学习与错题复习经验提升至 3 倍，可叠加时长。",
  },
  xp_boost_3x: {
    name: "悟道灵液·三阶",
    description: "学习与错题复习经验提升至 3 倍，可叠加时长。",
  },
  xp_boost: {
    name: "悟道灵液",
    description: "学习与错题复习经验提升，可叠加时长。",
  },
  time_treasure: {
    name: "时晷灵砂",
    description: "延长当前经验翻倍效果时长，适合即将到期时续时。",
  },
  abyss_revive: {
    name: "归元护符",
    description: "无尽深渊专属：恢复 1HP，并获得 3 分钟免扣血保护。",
  },
  revival: {
    name: "归元护符",
    description: "无尽深渊专属：恢复 1HP，并获得 3 分钟免扣血保护。",
  },
  coin_pack: {
    name: "灵钱宝匣",
    description: "使用现金购买代币，立即到账。",
  },
};

const resolveItemBaseCode = (itemCode: string): string => {
  if (itemCode.startsWith("coin_pack")) return "coin_pack";
  return itemCode;
};

const safeItemDisplayName = (itemCode: string): string => {
  const baseCode = resolveItemBaseCode(itemCode);
  const fallback = itemCatalog[itemCode] || itemCatalog[baseCode];
  if (fallback) return fallback.name;
  return itemCode.replace(/_/g, "·");
};

const itemLocalization = (itemCode: string): { name: string; description: string } => {
  const baseCode = resolveItemBaseCode(itemCode);
  const i18nKeys: Record<string, { name: string; description: string }> = {
    streak_freeze: {
      name: "shop.items.streakFreeze.name",
      description: "shop.items.streakFreeze.desc",
    },
    xp_boost_1_5x: {
      name: "shop.items.xpBoost15.name",
      description: "shop.items.xpBoost15.desc",
    },
    xp_boost_1_5: {
      name: "shop.items.xpBoost15.name",
      description: "shop.items.xpBoost15.desc",
    },
    xp_boost_2: {
      name: "shop.items.xpBoost2.name",
      description: "shop.items.xpBoost2.desc",
    },
    xp_boost_2x: {
      name: "shop.items.xpBoost2.name",
      description: "shop.items.xpBoost2.desc",
    },
    xp_boost_3: {
      name: "shop.items.xpBoost3.name",
      description: "shop.items.xpBoost3.desc",
    },
    xp_boost_3x: {
      name: "shop.items.xpBoost3.name",
      description: "shop.items.xpBoost3.desc",
    },
    xp_boost: {
      name: "shop.items.xpBoost.name",
      description: "shop.items.xpBoost.desc",
    },
    time_treasure: {
      name: "shop.items.timeTreasure.name",
      description: "shop.items.timeTreasure.desc",
    },
    abyss_revive: {
      name: "shop.items.abyssRevive.name",
      description: "shop.items.abyssRevive.desc",
    },
    revival: {
      name: "shop.items.revival.name",
      description: "shop.items.revival.desc",
    },
    coin_pack: {
      name: "shop.items.coinPack.name",
      description: "shop.items.coinPack.desc",
    },
  };

  const key = i18nKeys[itemCode] || i18nKeys[baseCode];
  const fallback = itemCatalog[itemCode] || itemCatalog[baseCode] || {
    name: safeItemDisplayName(itemCode),
    description: "",
  };

  if (isZhLocale.value) {
    return fallback;
  }

  return {
    name: key ? translateOr(key.name, fallback.name) : fallback.name,
    description: key ? translateOr(key.description, fallback.description) : fallback.description,
  };
};

const itemIcon = (itemCode: string): string => {
  const baseCode = resolveItemBaseCode(itemCode);
  return iconMap[itemCode] || iconMap[baseCode] || "◉";
};

const mapOfferToShopItem = (offer: ShopOffer): ShopItem => {
  const itemCode = offer.item_code || "";
  const rarityLower = (offer.rarity || "common").toLowerCase();
  const isCoinPack = itemCode.startsWith("coin_pack");
  const localized = itemLocalization(itemCode);
  return {
    offerId: offer.id,
    name: localized.name || offer.display_name || safeItemDisplayName(itemCode),
    rarity: rarityLabel(offer.rarity || "common"),
    rarityKey:
      rarityLower === "legendary" || rarityLower === "rare" || rarityLower === "uncommon"
        ? rarityLower
        : "common",
    price: offer.price_amount || 0,
    icon: itemIcon(itemCode),
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

const handlePurchase = async (item: ShopItem) => {
  if (isPurchasing.value) return;

  if (item.isCoinPack) {
    selectedItem.value = item;
    showTopUpModal.value = true;
    return;
  }

  selectedItem.value = item;
  showPurchaseConfirmModal.value = true;
};

const confirmPurchaseSelected = async () => {
  if (isPurchasing.value || !selectedItem.value) return;

  const item = selectedItem.value;

  if (walletBalance.value < item.price) {
    showPurchaseConfirmModal.value = false;
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
    showPurchaseConfirmModal.value = false;
    selectedItem.value = null;
    await Promise.all([fetchBalance(), fetchShopItems(), refreshInventory()]);
  } catch (error) {
    console.error("Purchase failed:", error);
    purchaseError.value = t("shop.errors.purchaseFailed");
  } finally {
    isPurchasing.value = false;
  }
};

const handleTopUpPurchase = async (offerId: string) => {
  const offer = topUpOffers.value.find((i) => i.id === offerId);
  if (!offer) return;
  selectedTopUpOffer.value = offer;
  showTopUpConfirmModal.value = true;
};

const confirmTopUpPurchase = async () => {
  if (!selectedTopUpOffer.value) return;
  showTopUpConfirmModal.value = false;
  showTopUpModal.value = false;
  purchaseError.value = "充值接口暂未接入，当前为前端流程占位。";
  window.setTimeout(() => {
    purchaseError.value = null;
  }, 2200);
  selectedTopUpOffer.value = null;
};

const closePurchaseConfirm = () => {
  showPurchaseConfirmModal.value = false;
  selectedItem.value = null;
};

const purchaseModalTitle = computed(() => {
  if (!selectedItem.value) return "购买道具";
  return `购买${selectedItem.value.name}`;
});

const topUpConfirmTitle = computed(() => {
  if (!selectedTopUpOffer.value) return "购买灵钱宝匣";
  return `购买${selectedTopUpOffer.value.label}`;
});

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

const coinPacks = computed(() => {
  const packs = shopItems.value.filter((i) => i.isCoinPack);
  if (packs.length > 0) return packs;
  return [
    {
      offerId: "coin-pack-fallback",
      name: "灵钱宝匣",
      rarity: translateOr("shop.topUp", "充值"),
      rarityKey: "legendary" as const,
      price: 6,
      icon: "◈",
      description: "购买灵钱补给，用于解锁道具与功能。",
      accent: "amber" as const,
      itemCode: "coin_pack",
      isCoinPack: true,
    },
  ];
});

const topUpOffers = computed(() => {
  const realOffers = shopItems.value
    .filter((i) => i.isCoinPack)
    .map((c) => ({
      id: c.offerId,
      coin_amount: c.price * 10,
      price_usd: c.price,
      label: c.name,
      recommended: false,
    }));
  if (realOffers.length > 0) return realOffers;
  return [
    { id: "demo-1", coin_amount: 60, price_usd: 6, label: "灵钱宝匣·小", recommended: false },
    { id: "demo-2", coin_amount: 300, price_usd: 30, label: "灵钱宝匣·中", recommended: true },
    { id: "demo-3", coin_amount: 680, price_usd: 68, label: "灵钱宝匣·大", recommended: false },
  ];
});
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
          :hide-price-tag="true"
          :badge="t('shop.topUp')"
          :description="item.description"
          @purchase="() => handlePurchase(item)"
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
          :badge="item.rarityKey === 'rare' ? t('shop.items.rareTag') : undefined"
          :description="item.description"
          @purchase="() => handlePurchase(item)"
        />
      </section>

      <footer class="shop-footer">
        <small>{{ t("shop.copyright") }}</small>
        <nav class="shop-footer__links" :aria-label="t('shop.footerLinksAria')">
          <router-link to="/settings/user-agreement">{{ t("shop.terms") }}</router-link>
          <router-link to="/privacy-policy">{{ t("shop.privacy") }}</router-link>
          <router-link to="/settings/help-center">{{ t("shop.support") }}</router-link>
        </nav>
      </footer>
    </section>

    <CoinPackTopUpModal
      :visible="showTopUpModal"
      :title="'灵钱宝匣充值'"
      :offers="topUpOffers"
      @purchase="handleTopUpPurchase"
      @close="showTopUpModal = false"
    />

    <transition name="modal-fade">
      <div v-if="showTopUpConfirmModal" class="purchase-modal-overlay" @click="showTopUpConfirmModal = false">
        <section class="purchase-modal" @click.stop>
          <h2>{{ topUpConfirmTitle }}</h2>
          <p v-if="selectedTopUpOffer">将获得 {{ selectedTopUpOffer.coin_amount }} 灵钱。</p>
          <p v-if="selectedTopUpOffer" class="purchase-modal__price">需支付 ${{ selectedTopUpOffer.price_usd }}</p>
          <footer class="purchase-modal__actions">
            <button class="confirm-btn" type="button" @click="confirmTopUpPurchase">确认购买</button>
            <button class="cancel-btn" type="button" @click="showTopUpConfirmModal = false">取消</button>
          </footer>
        </section>
      </div>
    </transition>

    <transition name="modal-fade">
      <div v-if="showPurchaseConfirmModal" class="purchase-modal-overlay" @click="closePurchaseConfirm">
        <section class="purchase-modal" @click.stop>
          <h2>{{ purchaseModalTitle }}</h2>
          <p v-if="selectedItem">{{ selectedItem.description }}</p>
          <p v-if="selectedItem" class="purchase-modal__price">需消耗 {{ selectedItem.price }} 🪙</p>
          <footer class="purchase-modal__actions">
            <button class="confirm-btn" type="button" @click="confirmPurchaseSelected">确认购买</button>
            <button class="cancel-btn" type="button" @click="closePurchaseConfirm">取消</button>
          </footer>
        </section>
      </div>
    </transition>

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
              <p>{{ translateOr("shop.bagEmpty", "暂无可用道具") }}</p>
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
                  <span>{{ inventoryCountLabel(item.quantity) }}</span>
                </div>
                <button
                  class="use-btn"
                  type="button"
                  @click="handleUseItem(item.itemCode, item.name, item.description)"
                >
                  {{ translateOr("shop.use", "使用") }}
                </button>
              </article>
            </div>
          </div>
        </section>
      </div>
    </transition>

    <transition name="modal-fade">
      <div v-if="purchaseError" class="purchase-error-toast">{{ purchaseError }}</div>
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

.purchase-modal-overlay {
  align-items: center;
  background: rgba(15, 23, 42, 0.45);
  bottom: 0;
  display: flex;
  justify-content: center;
  left: 0;
  position: fixed;
  right: 0;
  top: 0;
  z-index: 1200;
}

.purchase-modal {
  background: #ffffff;
  border: 1px solid #e7e5e4;
  border-radius: 16px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
  max-width: 560px;
  padding: 24px;
  width: min(560px, calc(100% - 24px));
}

.purchase-modal h2 {
  color: #1f2937;
  font-size: 36px;
  margin: 0;
}

.purchase-modal p {
  color: #6b7280;
  font-size: 16px;
  line-height: 1.6;
  margin: 12px 0 0;
}

.purchase-modal__price {
  color: #0f766e;
  font-weight: 700;
}

.purchase-modal__actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 18px;
}

.confirm-btn,
.cancel-btn {
  border-radius: 999px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  min-height: 40px;
  padding: 0 16px;
}

.confirm-btn {
  background: linear-gradient(90deg, #0891b2, #0d9488);
  border: 0;
  color: #ffffff;
}

.cancel-btn {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #374151;
}

.purchase-error-toast {
  background: #7f1d1d;
  border-radius: 12px;
  bottom: 20px;
  color: #ffffff;
  left: 50%;
  padding: 10px 14px;
  position: fixed;
  transform: translateX(-50%);
  z-index: 1200;
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
