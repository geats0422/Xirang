import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type NotificationType = "quest_reward" | "system" | "achievement" | "streak";

export type NotificationItem = {
  id: string;
  user_id: string;
  notification_type: NotificationType;
  title_i18n_key: string;
  content_i18n_key: string;
  meta: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
};

export type NotificationListResponse = {
  notifications: NotificationItem[];
  unread_count: number;
};

export const getNotifications = async (): Promise<NotificationListResponse> => {
  return apiRequest<NotificationListResponse>("/api/v1/notifications", {
    method: "GET",
    headers: getAuthHeaders(),
  });
};

export const markNotificationAsRead = async (notificationId: string): Promise<void> => {
  await apiRequest<void>(`/api/v1/notifications/${notificationId}/read`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
};

export const markAllNotificationsAsRead = async (): Promise<void> => {
  await apiRequest<void>("/api/v1/notifications/read-all", {
    method: "POST",
    headers: getAuthHeaders(),
  });
};
