import { api } from "./client";
import { tokenStore } from "./tokens";
import type {
  LoginInput,
  RegisterInput,
  TokenResponse,
  User,
} from "./types";

export async function login(input: LoginInput): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", input);
  tokenStore.set(data);
  return data;
}

export async function register(input: RegisterInput): Promise<User> {
  const { data } = await api.post<User>("/auth/register", input);
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function logout(): Promise<void> {
  const refreshToken = tokenStore.getRefresh();
  if (refreshToken) {
    try {
      await api.post("/auth/logout", { refresh_token: refreshToken });
    } catch {
      // Si el token ya expiró, igualmente limpiamos la sesión local.
    }
  }
  tokenStore.clear();
}
