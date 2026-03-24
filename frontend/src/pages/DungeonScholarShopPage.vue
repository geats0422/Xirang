<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getShopBalance as getBalance } from "../api/shop";

type ShopItem = {
  name: string;
  rarity: string;
  price: number;
  icon: string;
  description: string;
  accent: "teal" | "violet" | "rose" | "amber";
};

const router = useRouter();

const walletBalance = ref(0);
const isLoading = ref(true);
const showInsufficientModal = ref(false);
const selectedItem = ref<ShopItem | null>(null);

const fetchBalance = async () => {
  isLoading.value = true;
  try {
    const balance = await getBalance();
    const normalizedBalance = balance as { coins?: number; balance?: number };
    walletBalance.value =
      (typeof normalizedBalance.coins === "number" ? normalizedBalance.coins : normalizedBalance.balance) || 0;
  } catch (error) {
    console.error("Failed to fetch balance:", error);
    walletBalance.value = 0;
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  document.title = "Xi Rang Scholar Shop";
  await fetchBalance();
});

const shopItems: ShopItem[] = [
  {
    name: "Streak Freeze Ticket",
    rarity: "Common",
    price: 500,
    icon: "❄",
    description:
      "A magical charm encased in permafrost. Protects your daily learning streak from breaking for exactly one day.",
    accent: "teal",
  },
  {
    name: "XP Boost Potion",
    rarity: "Uncommon",
    price: 200,
    icon: "⚗",
    description:
      "A vial of concentrated knowledge. Drink to double your experience points gain for the next 30 minutes of study.",
    accent: "violet",
  },
  {
    name: "Abyss Revive Token",
    rarity: "Rare",
    price: 800,
    icon: "♡",
    description:
      "A gemstone pulsating with life force. Instantly restores full HP during an 'Endless Abyss' run, cheating death itself.",
    accent: "rose",
  },
];

const topUpItem: ShopItem = {
  name: "Coin Pack",
  rarity: "Rescue",
  price: 199,
  icon: "💎",
  description:
    "Emergency coin pack when you need just a little more. Get 1,000 coins instantly for $1.99.",
  accent: "amber",
};

const goBack = async () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }

  await router.push("/home");
};

const handlePurchase = (item: ShopItem) => {
  if (item.accent === "amber") {
    walletBalance.value += 1000;
    return;
  }

  if (walletBalance.value < item.price) {
    selectedItem.value = item;
    showInsufficientModal.value = true;
    return;
  }

  walletBalance.value -= item.price;
};

const closeInsufficientModal = () => {
  showInsufficientModal.value = false;
  selectedItem.value = null;
};

const buyRescuePack = () => {
  walletBalance.value += 1000;
  if (selectedItem.value && walletBalance.value >= selectedItem.value.price) {
    walletBalance.value -= selectedItem.value.price;
  }
  closeInsufficientModal();
};

defineExpose({
  walletBalance,
});
</script>

<template>
  <main class="shop-page">
    <section class="shop-shell" aria-label="Virtual item shop interface">
      <header class="shop-header">
        <div class="shop-brand">
          <div class="shop-brand__icon">
            <img src="/taotie-logo.svg" alt="" aria-hidden="true" />
          </div>
          <div class="shop-brand__copy">
            <span>XI rang</span>
            <strong>Scholar</strong>
            <span>Shop</span>
          </div>
        </div>

        <div class="shop-wallet-group">
          <div class="wallet-pill">
            <span class="wallet-pill__coin">🪙</span>
            <strong>{{ walletBalance.toLocaleString() }}</strong>
            <small>COINS</small>
          </div>
          <button class="bag-btn" type="button" aria-label="Inventory bag">👜</button>
        </div>
      </header>

      <section class="shop-hero">
        <div>
          <p class="shop-hero__eyebrow">Virtual Item Shop Interface</p>
          <h1>Mystical Artifacts</h1>
          <p>
            Enhance your journey through the Endless Abyss. Acquire potent items to aid your scholarly pursuits and
            protect your progress.
          </p>
        </div>

        <div class="shop-hero__actions">
          <button class="back-btn" type="button" aria-label="Go back" @click="goBack">←</button>

          <div class="shop-filters">
            <span class="filter-chip filter-chip--teal">✦ New Arrivals</span>
            <span class="filter-chip filter-chip--amber">🔥 Hot Items</span>
          </div>
        </div>
      </section>

      <div class="shop-divider" />

      <section class="shop-grid" aria-label="Shop items">
        <!-- Top Up Card -->
        <article class="shop-card shop-card--amber shop-card--topup">
          <div class="shop-card__head">
            <span class="rarity-tag rarity-tag--amber">TOP UP</span>
            <span class="price-tag price-tag--usd">$1.99</span>
          </div>

          <div class="shop-card__icon shop-card__icon--amber">{{ topUpItem.icon }}</div>

          <div class="shop-card__body">
            <h2>{{ topUpItem.name }}</h2>
            <p>{{ topUpItem.description }}</p>
          </div>

          <footer class="shop-card__footer">
            <div>
              <small>TYPE</small>
              <strong class="shop-card__rarity--amber">{{ topUpItem.rarity }}</strong>
            </div>
            <button class="purchase-btn purchase-btn--amber" type="button" @click="handlePurchase(topUpItem)">
              Buy Now →
            </button>
          </footer>
        </article>

        <!-- Regular Shop Items -->
        <article
          v-for="item in shopItems"
          :key="item.name"
          class="shop-card"
          :class="`shop-card--${item.accent}`"
        >
          <div class="shop-card__head">
            <span class="rarity-tag" :class="`rarity-tag--${item.accent}`">{{
              item.accent === "rose" ? "RARE" : ""
            }}</span>
            <span class="price-tag">{{ item.price }} 🪙</span>
          </div>

          <div class="shop-card__icon" :class="`shop-card__icon--${item.accent}`">{{ item.icon }}</div>

          <div class="shop-card__body">
            <h2>{{ item.name }}</h2>
            <p>{{ item.description }}</p>
          </div>

          <footer class="shop-card__footer">
            <div>
              <small>RARITY</small>
              <strong :class="`shop-card__rarity--${item.accent}`">{{ item.rarity }}</strong>
            </div>
            <button
              class="purchase-btn"
              :class="`purchase-btn--${item.accent}`"
              type="button"
              @click="handlePurchase(item)"
            >
              Purchase →
            </button>
          </footer>
        </article>
      </section>

      <!-- Insufficient Balance Modal -->
      <transition name="modal-fade">
        <div v-if="showInsufficientModal" class="insufficient-modal-overlay" @click="closeInsufficientModal">
          <section class="insufficient-modal" @click.stop>
            <header class="insufficient-modal__header">
              <h2>⚠ Insufficient Balance</h2>
            </header>

            <div class="insufficient-modal__body">
              <p>You need more coins to purchase <strong>{{ selectedItem?.name }}</strong>.</p>
              <p class="insufficient-modal__balance">
                Your balance: <span>🪙 {{ walletBalance.toLocaleString() }}</span>
              </p>
              <p class="insufficient-modal__price">
                Item price: <span>🪙 {{ selectedItem?.price }}</span>
              </p>
            </div>

            <footer class="insufficient-modal__actions">
              <button class="rescue-btn" type="button" @click="buyRescuePack">
                💎 Buy Coin Pack ($1.99) →
              </button>
              <button class="cancel-btn" type="button" @click="closeInsufficientModal">Cancel</button>
            </footer>
          </section>
        </div>
      </transition>

      <footer class="shop-footer">
        <small>© 2023 Dungeon Scholar. All rights reserved.</small>
        <nav class="shop-footer__links" aria-label="Footer links">
          <a href="#">Terms of Service</a>
          <a href="#">Privacy Policy</a>
          <a href="#">Support</a>
        </nav>
      </footer>
    </section>
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

.shop-header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  padding: 14px 20px;
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

.shop-brand {
  align-items: center;
  display: flex;
  gap: 12px;
}

.shop-brand__icon {
  align-items: center;
  background: transparent;
  border-radius: 14px;
  display: inline-flex;
  height: 36px;
  justify-content: center;
  overflow: hidden;
  width: 36px;
}

.shop-brand__icon img {
  display: block;
  height: 100%;
  width: 100%;
}

.shop-brand__copy {
  align-items: baseline;
  color: #2c3848;
  display: flex;
  font-family: var(--font-serif);
  font-size: 20px;
  gap: 4px;
}

.shop-brand__copy strong {
  color: #1696a2;
}

.shop-wallet-group {
  align-items: center;
  display: flex;
  gap: 10px;
}

.wallet-pill {
  align-items: center;
  background: #ffffff;
  border: 1px solid #dde1e4;
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(32, 45, 64, 0.04);
  display: inline-flex;
  gap: 8px;
  min-height: 42px;
  padding: 0 16px;
}

.wallet-pill__coin {
  font-size: 16px;
}

.wallet-pill strong {
  color: #46556a;
  font-size: 16px;
}

.wallet-pill small {
  color: #9aa4b2;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.bag-btn {
  background: #ffffff;
  border: 1px solid #dde1e4;
  border-radius: 999px;
  cursor: pointer;
  height: 42px;
  width: 42px;
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

.shop-card {
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid #e4e4e1;
  border-radius: 18px;
  box-shadow: 0 8px 20px rgba(31, 41, 55, 0.04);
  min-height: 396px;
  padding: 18px;
}

.shop-card--rose {
  border-color: #f4c7cd;
}

.shop-card__head,
.shop-card__footer {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.rarity-tag {
  min-width: 48px;
}

.rarity-tag--rose {
  background: #fff1f2;
  border-radius: 999px;
  color: #e11d48;
  display: inline-flex;
  font-size: 10px;
  font-weight: 800;
  justify-content: center;
  letter-spacing: 0.08em;
  padding: 4px 8px;
}

.price-tag {
  align-items: center;
  background: #ffffff;
  border-radius: 14px;
  color: #64748b;
  display: inline-flex;
  font-size: 13px;
  font-weight: 700;
  min-height: 30px;
  padding: 0 12px;
}

.shop-card__icon {
  align-items: center;
  background: #ffffff;
  border-radius: 999px;
  box-shadow: 0 16px 24px rgba(31, 41, 55, 0.06);
  display: inline-flex;
  font-size: 54px;
  height: 104px;
  justify-content: center;
  margin: 28px auto 0;
  width: 104px;
}

.shop-card__icon--teal {
  color: #0891b2;
}

.shop-card__icon--violet {
  color: #7c3aed;
}

.shop-card__icon--rose {
  color: #e11d48;
}

.shop-card__body h2 {
  color: #475569;
  font-size: 20px;
  line-height: 1.15;
  margin: 88px 0 0;
}

.shop-card--rose .shop-card__body h2 {
  color: #e11d48;
}

.shop-card__body p {
  color: #7a8089;
  font-size: 13px;
  line-height: 1.45;
  margin: 12px 0 0;
}

.shop-card__footer {
  margin-top: 26px;
}

.shop-card__footer small {
  color: #a1a1aa;
  display: block;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.shop-card__footer strong {
  display: block;
  font-size: 13px;
  margin-top: 4px;
}

.shop-card__rarity--teal {
  color: #0891b2;
}

.shop-card__rarity--violet {
  color: #7c3aed;
}

.shop-card__rarity--rose {
  color: #e11d48;
}

.purchase-btn {
  border: 0;
  border-radius: 999px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 800;
  height: 36px;
  min-width: 110px;
  padding: 0 18px;
}

.purchase-btn--teal {
  background: linear-gradient(90deg, #1098a5, #14b8a6);
}

.purchase-btn--violet {
  background: linear-gradient(90deg, #7c3aed, #6366f1);
}

.purchase-btn--rose {
  background: linear-gradient(90deg, #f43f5e, #ef4444);
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

@media (max-width: 1100px) {
  .shop-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .shop-page {
    padding: 10px;
  }

  .shop-header,
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
