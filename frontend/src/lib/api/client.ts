import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { tokenStore } from "./tokens";
import type { TokenResponse } from "./types";

export const API_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export const UNAUTHORIZED_EVENT = "turnix:unauthorized";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = tokenStore.getRefresh();
  if (!refreshToken) {
    throw new Error("No hay token de refresco");
  }

  const response = await axios.post<TokenResponse>(`${API_URL}/auth/refresh`, {
    refresh_token: refreshToken,
  });

  tokenStore.set(response.data);
  return response.data.access_token;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const status = error.response?.status;
    const url = original?.url ?? "";
    const isTokenEndpoint =
      url.includes("/auth/login") ||
      url.includes("/auth/register") ||
      url.includes("/auth/refresh");

    if (status === 401 && original && !original._retry && !isTokenEndpoint) {
      original._retry = true;
      try {
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        const accessToken = await refreshPromise;
        original.headers.Authorization = `Bearer ${accessToken}`;
        return api(original);
      } catch (refreshError) {
        tokenStore.clear();
        window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
        return Promise.reject(refreshError);
      }
    }

    if (import.meta.env.DEV) {
      console.error(
        `[api] ${original?.method?.toUpperCase() ?? "REQUEST"} ${url}`,
        status ?? error.code,
        error.response?.data ?? error.message,
      );
    }

    return Promise.reject(error);
  },
);

interface ValidationDetail {
  msg?: string;
  loc?: (string | number)[];
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)
      ?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = (detail as ValidationDetail[])
        .map((item) => item.msg)
        .filter((message): message is string => Boolean(message));
      if (messages.length > 0) {
        return messages.join(". ");
      }
    }

    if (error.response) {
      return `Error ${error.response.status}. Inténtalo de nuevo.`;
    }

    if (error.code === "ERR_NETWORK") {
      return "No se pudo conectar con el servidor. Verifica que la API esté en marcha.";
    }

    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Ocurrió un error inesperado";
}
