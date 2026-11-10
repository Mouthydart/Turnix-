import { useQuery } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "@/features/auth/auth-context";
import { listBusinesses } from "@/lib/api/businesses";
import type { Business } from "@/lib/api/types";

const STORAGE_KEY = "turnix.current_business";

interface BusinessContextValue {
  businesses: Business[];
  currentBusiness: Business | null;
  isLoading: boolean;
  isError: boolean;
  setCurrentBusinessId: (businessId: string) => void;
}

const BusinessContext = createContext<BusinessContextValue | null>(null);

export function BusinessProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [selectedId, setSelectedId] = useState<string | null>(() =>
    localStorage.getItem(STORAGE_KEY),
  );
  const isCustomer = user?.role === "customer";

  const query = useQuery({
    queryKey: ["businesses"],
    queryFn: listBusinesses,
    enabled: Boolean(user) && !isCustomer,
  });

  const businesses = query.data ?? [];

  useEffect(() => {
    if (businesses.length === 0) return;
    const exists = businesses.some((business) => business.id === selectedId);
    if (!exists) {
      const first = businesses[0].id;
      setSelectedId(first);
      localStorage.setItem(STORAGE_KEY, first);
    }
  }, [businesses, selectedId]);

  const setCurrentBusinessId = useCallback((businessId: string) => {
    setSelectedId(businessId);
    localStorage.setItem(STORAGE_KEY, businessId);
  }, []);

  const currentBusiness =
    businesses.find((business) => business.id === selectedId) ??
    businesses[0] ??
    null;

  const value = useMemo<BusinessContextValue>(
    () => ({
      businesses,
      currentBusiness,
      isLoading: query.isLoading,
      isError: query.isError,
      setCurrentBusinessId,
    }),
    [businesses, currentBusiness, query.isLoading, query.isError, setCurrentBusinessId],
  );

  return (
    <BusinessContext.Provider value={value}>
      {children}
    </BusinessContext.Provider>
  );
}

export function useBusiness(): BusinessContextValue {
  const context = useContext(BusinessContext);
  if (!context) {
    throw new Error("useBusiness debe usarse dentro de BusinessProvider");
  }
  return context;
}

export function useCurrentBusiness(): Business {
  const { currentBusiness } = useBusiness();
  if (!currentBusiness) {
    throw new Error("No hay un negocio seleccionado");
  }
  return currentBusiness;
}
