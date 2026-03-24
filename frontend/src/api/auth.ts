import { apiRequest } from "./http";

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

export type LoginInput = {
  identity: string;
  password: string;
};

export type RegisterInput = {
  username: string;
  email: string;
  password: string;
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
  storage.setItem("xirang:isAuthenticated", "true");
};
