import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type ThemeKey = "light" | "dark" | "system";
export type LeaderboardScope = "global" | "friends";

export type SettingsResponse = {
  user_id: string;
  theme_key: ThemeKey;
  language_code: string;
  sound_enabled: boolean;
  haptic_enabled: boolean;
  daily_reminder_enabled: boolean;
  leaderboard_scope_default: LeaderboardScope;
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
  >
>;

export type AiConfigResponse = {
  provider: string;
  base_url: string | null;
  model: string;
  configured: boolean;
};

export const getSettings = async (): Promise<SettingsResponse> => {
  return apiRequest<SettingsResponse>("/api/v1/settings", {
    headers: getAuthHeaders(),
  });
};

export const getAiConfig = async (): Promise<AiConfigResponse> => {
  return apiRequest<AiConfigResponse>("/api/v1/settings/ai-config", {
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
