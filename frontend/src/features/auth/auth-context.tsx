import { useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  fetchMe,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
} from "@/lib/api/auth";
import { UNAUTHORIZED_EVENT } from "@/lib/api/client";
import { tokenStore } from "@/lib/api/tokens";
import type { LoginInput, RegisterInput, User } from "@/lib/api/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (input: LoginInput) => Promise<User>;
  register: (input: RegisterInput) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      if (!tokenStore.getAccess() && !tokenStore.getRefresh()) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await fetchMe();
        if (!cancelled) {
          setUser(currentUser);
        }
      } catch {
        tokenStore.clear();
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      queryClient.clear();
    };

    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => {
      window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    };
  }, [queryClient]);

  const login = useCallback(async (input: LoginInput) => {
    await loginRequest(input);
    const currentUser = await fetchMe();
    setUser(currentUser);
    return currentUser;
  }, []);

  const register = useCallback(
    async (input: RegisterInput) => {
      await registerRequest(input);
      await loginRequest({ email: input.email, password: input.password });
      const currentUser = await fetchMe();
      setUser(currentUser);
      return currentUser;
    },
    [],
  );

  const logout = useCallback(async () => {
    await logoutRequest();
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
    }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }
  return context;
}
