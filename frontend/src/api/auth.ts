import { getAuthHeaders } from "./authHeaders";
import { ApiError, NetworkError, apiRequest } from "./http";

export type AuthUser = {
  id: string;
  username: string;
  email: string;
  status: string;
};

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type AuthResponse = {
  user: AuthUser;
  tokens: AuthTokens;
};

export type AuthMeResponse = {
  id: string;
  username: string;
  email: string;
  status: string;
};

export type LoginInput = {
  identity: string;
  password: string;
};

export type RegisterInput = {
  username: string;
  email: string;
  password: string;
};

export type AuthApiError = {
  detail?: string;
  message?: string;
};

export const isAuthApiError = (error: unknown): error is ApiError => {
  return error instanceof ApiError;
};

export const getAuthErrorMessage = (error: unknown): string => {
  if (isAuthApiError(error)) {
    const apiError = error as ApiError;
    if (apiError.detail) {
      if (typeof apiError.detail === "string") {
        return apiError.detail;
      }
      if (typeof apiError.detail === "object" && apiError.detail !== null) {
        const detail = apiError.detail as Record<string, unknown>;
        if (detail.message) {
          return String(detail.message);
        }
        if (detail.msg) {
          return String(detail.msg);
        }
      }
    }
    if (apiError.status === 401) {
      return "Invalid credentials. Please check your email/username and password.";
    }
    if (apiError.status === 409) {
      return "An account with this email or username already exists.";
    }
    if (apiError.status === 422) {
      return "Invalid input. Please check your information and try again.";
    }
  }
  if (error instanceof NetworkError) {
    return "Cannot reach backend service. Please check your network or dev proxy.";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred. Please try again.";
};

export const loginWithPassword = async (input: LoginInput): Promise<AuthResponse> => {
  return apiRequest<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: {
      identity: input.identity,
      password: input.password,
    },
  });
};

export const registerWithPassword = async (input: RegisterInput): Promise<AuthResponse> => {
  return apiRequest<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    body: {
      username: input.username,
      email: input.email,
      password: input.password,
    },
  });
};

export const persistAuthSession = (payload: AuthResponse): void => {
  if (typeof window === "undefined") {
    return;
  }

  const storage = window.localStorage;
  storage.setItem("xirang:accessToken", payload.tokens.access_token);
  storage.setItem("xirang:token", payload.tokens.access_token);
  storage.setItem("xirang:refreshToken", payload.tokens.refresh_token);
  storage.setItem("xirang:userId", payload.user.id);
  storage.setItem("xirang:username", payload.user.username);
  storage.setItem("xirang:email", payload.user.email);
  storage.setItem("xirang:isAuthenticated", "true");
};

export const getCurrentAuthUser = async (): Promise<AuthMeResponse> => {
  return apiRequest<AuthMeResponse>("/api/v1/auth/me", {
    headers: getAuthHeaders(),
  });
};
