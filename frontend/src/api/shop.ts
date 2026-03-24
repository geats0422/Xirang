import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type QuotaType = "unlimited" | "personal_cap" | "auto_refill";

export type ItemType = "coin_pack" | "streak_freeze" | "time_treasure" | "revival";

export type TierRequired = "free" | "super";

export type ShopOffer = {
  id: string;
  item_code: string;
  display_name: string;
  rarity: string;
  price_asset_code: string;
  price_amount: number;
  is_active: boolean;
  active_from: string | null;
  active_to: string | null;
  purchase_limit_per_user: number | null;
  quota_type: QuotaType;
  max_capacity: number | null;
  refill_days: number | null;
  tier_required: TierRequired;
  experiment_flag: string | null;
  item_type: ItemType;
};

export type ShopBalance = {
  asset_code: string;
  balance: number;
};

export type ShopLedgerEntry = {
  id: string;
  asset_code: string;
  delta: number;
  balance_after: number;
  reason_code: string;
  source_type: string | null;
  source_id: string | null;
  created_at: string;
};

export type PurchaseShopItemInput = {
  offerId: string;
  idempotencyKey?: string;
};

export type PurchaseShopItemResponse = {
  id: string;
  user_id: string;
  offer_id: string | null;
  item_code: string;
  price_asset_code: string;
  price_amount: number;
  status: "pending" | "completed" | "failed" | "refunded";
  purchased_at: string;
};

export type ShopInventoryItem = {
  user_id: string;
  item_code: string;
  quantity: number;
  updated_at: string;
  quota_max: number | null;
  refill_days: number | null;
  last_refill_at: string | null;
  next_refill_at: string | null;
};

export type ShopInventoryResponse = {
  items: ShopInventoryItem[];
};

export type ListShopItemsParams = {
  userTier?: TierRequired;
  experimentFlags?: string[];
};

export const listShopItems = async (params: ListShopItemsParams = {}): Promise<ShopOffer[]> => {
  const query = new URLSearchParams();
  if (params.userTier) {
    query.set("user_tier", params.userTier);
  }
  if (params.experimentFlags && params.experimentFlags.length > 0) {
    query.set("experiment_flags", params.experimentFlags.join(","));
  }
  const qs = query.toString();
  const path = qs ? `/api/v1/shop/items?${qs}` : "/api/v1/shop/items";
  return apiRequest<ShopOffer[]>(path);
};

export const getShopBalance = async (): Promise<ShopBalance> => {
  return apiRequest<ShopBalance>("/api/v1/shop/balance", {
    headers: getAuthHeaders(),
  });
};

export const purchaseShopItem = async (
  input: PurchaseShopItemInput,
): Promise<PurchaseShopItemResponse> => {
  return apiRequest<PurchaseShopItemResponse>("/api/v1/shop/purchase", {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      offer_id: input.offerId,
      idempotency_key: input.idempotencyKey,
    },
  });
};

export const getShopInventory = async (): Promise<ShopInventoryItem[]> => {
  const response = await apiRequest<ShopInventoryResponse>("/api/v1/shop/inventory", {
    headers: getAuthHeaders(),
  });
  return response.items;
};

export const getShopLedger = async (): Promise<ShopLedgerEntry[]> => {
  return apiRequest<ShopLedgerEntry[]>("/api/v1/shop/ledger", {
    headers: getAuthHeaders(),
  });
};
