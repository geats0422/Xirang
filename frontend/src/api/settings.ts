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
