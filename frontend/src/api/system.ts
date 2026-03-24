import { apiRequest } from "./http";

export type HealthResponse = {
  status: string;
  service: string;
};

export const getBackendHealth = async (signal?: AbortSignal): Promise<HealthResponse> => {
  return apiRequest<HealthResponse>("/health", { signal });
};
