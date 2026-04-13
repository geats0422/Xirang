import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type ThemeKey = "light" | "dark" | "system";
export type LeaderboardScope = "global" | "friends";

export type ModelInfo = {
  id: string;
  name: string;
  description: string;
  tags: string[];
  provider: string;
};

export type SettingsResponse = {
  user_id: string;
  theme_key: ThemeKey;
  language_code: string;
  sound_enabled: boolean;
  haptic_enabled: boolean;
  daily_reminder_enabled: boolean;
  leaderboard_scope_default: LeaderboardScope;
  selected_model: string | null;
  updated_at: string;
};

export type SettingsUpdateRequest = Partial<
  Pick<
    SettingsResponse,
    | "theme_key"
    | "language_code"
    | "sound_enabled"
    | "haptic_enabled"
    | "daily_reminder_enabled"
    | "leaderboard_scope_default"
    | "selected_model"
  >
>;

export type AiConfigResponse = {
  model: string;
  temperature: number;
  max_tokens: number;
};

export type AiModelsResponse = {
  available_models: string[];
};

export const getAiConfig = async (): Promise<AiConfigResponse> => {
  return apiRequest<AiConfigResponse>("/api/v1/settings/ai-config", {
    headers: getAuthHeaders(),
  });
};

export const getAiModels = async (): Promise<AiModelsResponse> => {
  return apiRequest<AiModelsResponse>("/api/v1/settings/ai-models", {
    headers: getAuthHeaders(),
  });
};

/** Fetch available LLM models from backend */
export const getAvailableModels = async (): Promise<ModelInfo[]> => {
  return apiRequest<ModelInfo[]>("/api/v1/settings/models");
};

export const getSettings = async (): Promise<SettingsResponse> => {
  return apiRequest<SettingsResponse>("/api/v1/settings", {
    headers: getAuthHeaders(),
  });
};

export const updateSettings = async (
  payload: SettingsUpdateRequest,
): Promise<SettingsResponse> => {
  return apiRequest<SettingsResponse>("/api/v1/settings", {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: payload,
  });
};

export const clearGameData = async (): Promise<void> => {
  return apiRequest<void>("/api/v1/settings/clear-game-data", {
    method: "POST",
    headers: getAuthHeaders(),
  });
};
