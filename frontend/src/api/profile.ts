import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type ProfileResponse = {
  user_id: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  verified_badge: boolean;
  tier_label: string | null;
  created_at: string;
  updated_at: string;
};

export const getMyProfile = async (): Promise<ProfileResponse> => {
  return apiRequest<ProfileResponse>("/api/v1/profile/me", {
    headers: getAuthHeaders(),
  });
};
