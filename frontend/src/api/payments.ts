import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type PricingRegion = "premium" | "standard" | "developing";

export const createCheckout = async (payload: { productType: string; plan: string }): Promise<{ checkout_url: string; status: string }> => {
  return apiRequest("/api/v1/payments/checkout", {
    method: "POST",
    headers: getAuthHeaders(),
    body: { product_type: payload.productType, plan: payload.plan },
  });
};

export const getSubscription = async (): Promise<{ status: string; tier: string | null; expires_at: string | null }> => {
  return apiRequest("/api/v1/payments/subscription", { headers: getAuthHeaders() });
};

export const cancelSubscription = async (): Promise<{ status: string }> => {
  return apiRequest("/api/v1/payments/subscription/cancel", { method: "POST", headers: getAuthHeaders() });
};

export const getRegion = async (): Promise<{ region: PricingRegion; prices: Record<string, number> }> => {
  return apiRequest("/api/v1/payments/region", { headers: getAuthHeaders() });
};

export const updateRegion = async (region: PricingRegion): Promise<{ region: PricingRegion; prices: Record<string, number> }> => {
  return apiRequest("/api/v1/payments/region", {
    method: "PUT",
    headers: getAuthHeaders(),
    body: { region },
  });
};
