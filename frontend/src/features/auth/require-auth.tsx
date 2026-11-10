import { Navigate, Outlet, useLocation } from "react-router-dom";

import { FullPageSpinner } from "@/components/spinner";
import { useAuth } from "./auth-context";

export function RequireAuth() {
  const { isLoading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullPageSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

export function PublicOnly() {
  const { isLoading, isAuthenticated, user } = useAuth();

  if (isLoading) {
    return <FullPageSpinner />;
  }

  if (isAuthenticated) {
    const destination = user?.role === "customer" ? "/cliente" : "/app";
    return <Navigate to={destination} replace />;
  }

  return <Outlet />;
}

export function OwnerOnly() {
  const { isLoading, user } = useAuth();

  if (isLoading) {
    return <FullPageSpinner />;
  }

  if (user?.role === "customer") {
    return <Navigate to="/cliente" replace />;
  }

  return <Outlet />;
}

export function CustomerOnly() {
  const { isLoading, user } = useAuth();

  if (isLoading) {
    return <FullPageSpinner />;
  }

  if (user && user.role !== "customer") {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}
