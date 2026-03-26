const ACCESS_TOKEN_KEY = "xirang:accessToken";
const USER_ID_KEY = "xirang:userId";

const getStorage = (): Storage | null => {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
};

export const ensureAuthIdentity = (): { accessToken: string; userId: string } => {
  const storage = getStorage();
  if (storage === null) {
    return { accessToken: "", userId: "" };
  }

  const storedToken = storage.getItem(ACCESS_TOKEN_KEY)?.trim();
  const storedUserId = storage.getItem(USER_ID_KEY)?.trim();
  const accessToken = storedToken && storedToken.length > 0 ? storedToken : "";
  const userId = storedUserId && storedUserId.length > 0 ? storedUserId : "";
  return { accessToken, userId };
};

export const getAuthHeaders = (): Record<string, string> => {
  const identity = ensureAuthIdentity();
  if (!identity.accessToken || !identity.userId) {
    return {};
  }
  return {
    Authorization: `Bearer ${identity.accessToken}`,
    "X-User-Id": identity.userId,
  };
};
