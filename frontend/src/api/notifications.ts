import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type NotificationType = "quest_reward" | "system" | "achievement" | "streak";

export type NotificationItem = {
  id: string;
  type: NotificationType | string;
  title: string;
  body: string | null;
  is_read: boolean;
  related_quest_id: string | null;
  action_url: string | null;
  created_at: string;
};

export type NotificationListResponse = {
  items: NotificationItem[];
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
