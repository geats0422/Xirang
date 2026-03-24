const ACCESS_TOKEN_KEY = "xirang:accessToken";
const USER_ID_KEY = "xirang:userId";
const DEV_ACCESS_TOKEN = "dev-local-token";
const DEV_USER_ID = "00000000-0000-0000-0000-000000000001";

const getStorage = (): Storage | null => {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
};

export const ensureAuthIdentity = (): { accessToken: string; userId: string } => {
  const storage = getStorage();
  if (storage === null) {
    return { accessToken: DEV_ACCESS_TOKEN, userId: DEV_USER_ID };
  }

  const storedToken = storage.getItem(ACCESS_TOKEN_KEY)?.trim();
  const storedUserId = storage.getItem(USER_ID_KEY)?.trim();
  const accessToken = storedToken && storedToken.length > 0 ? storedToken : DEV_ACCESS_TOKEN;
  const userId = storedUserId && storedUserId.length > 0 ? storedUserId : DEV_USER_ID;

  storage.setItem(ACCESS_TOKEN_KEY, accessToken);
  storage.setItem(USER_ID_KEY, userId);
  return { accessToken, userId };
};

export const getAuthHeaders = (): Record<string, string> => {
  const identity = ensureAuthIdentity();
  return {
    Authorization: `Bearer ${identity.accessToken}`,
    "X-User-Id": identity.userId,
  };
};
