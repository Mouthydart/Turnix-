import {
  BarChart3,
  CalendarDays,
  LayoutDashboard,
  LogOut,
  Menu,
  Scissors,
  Settings,
  Users,
  X,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { Logo } from "@/components/logo";
import { FullPageSpinner, Spinner } from "@/components/spinner";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-context";
import { useBusiness } from "@/features/business/business-context";
import { initials } from "@/lib/format";
import { cn } from "@/lib/utils";
import { BusinessSwitcher } from "./business-switcher";
import { NoBusinessScreen } from "./no-business-screen";

const OWNER_NAV_ITEMS = [
  { to: "/app", label: "Resumen", icon: LayoutDashboard, end: true },
  { to: "/app/bookings", label: "Reservas", icon: CalendarDays },
  { to: "/app/reports", label: "Reportes", icon: BarChart3 },
  { to: "/app/services", label: "Servicios", icon: Scissors },
  { to: "/app/staff", label: "Empleados", icon: Users },
  { to: "/app/settings", label: "Ajustes", icon: Settings },
];

const CUSTOMER_NAV_ITEMS = [
  { to: "/cliente", label: "Mis reservas", icon: CalendarDays, end: true },
];

const ROLE_LABELS: Record<string, string> = {
  owner: "Propietario",
  staff: "Empleado",
  customer: "Cliente",
  admin: "Administrador",
};

export function AppLayout() {
  const { user, logout } = useAuth();
  const { businesses, isLoading, isError } = useBusiness();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isCustomer = user?.role === "customer";
  const navItems = isCustomer ? CUSTOMER_NAV_ITEMS : OWNER_NAV_ITEMS;

  if (!isCustomer && isLoading) {
    return <FullPageSpinner />;
  }

  if (!isCustomer && isError) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center">
        <p className="font-medium">No se pudieron cargar tus negocios.</p>
        <p className="text-sm text-muted-foreground">
          Revisa que la API esté disponible e inténtalo de nuevo.
        </p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Reintentar
        </Button>
      </div>
    );
  }

  if (!isCustomer && businesses.length === 0) {
    return <NoBusinessScreen />;
  }

  return (
    <div className="bg-app flex min-h-screen">
      {mobileOpen ? (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      ) : null}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col overflow-hidden border-r bg-card/95 backdrop-blur transition-transform lg:static lg:z-auto lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-primary/10 via-fuchsia-500/5 to-transparent" />
        <div className="relative flex h-16 items-center justify-between border-b px-5">
          <Logo />
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Cerrar menú"
          >
            <X />
          </Button>
        </div>

        <nav className="relative flex-1 space-y-1 p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                  isActive
                    ? "bg-brand-gradient text-white shadow-md shadow-primary/25"
                    : "text-muted-foreground hover:bg-primary/5 hover:text-foreground",
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="relative border-t p-3">
          <div className="flex items-center gap-3 rounded-lg px-2 py-2">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-sm font-semibold text-white shadow-sm shadow-primary/25">
              {initials(user?.full_name ?? "?")}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{user?.full_name}</p>
              <p className="truncate text-xs text-muted-foreground">
                {ROLE_LABELS[user?.role ?? ""] ?? user?.role}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              title="Cerrar sesión"
              onClick={() => void logout()}
            >
              <LogOut />
            </Button>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b bg-card/70 px-4 shadow-sm shadow-slate-900/5 backdrop-blur-xl lg:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Abrir menú"
          >
            <Menu />
          </Button>
          {isCustomer ? (
            <span className="rounded-full bg-brand-soft px-3 py-1 text-xs font-medium text-primary ring-1 ring-primary/10">
              Área de cliente
            </span>
          ) : (
            <BusinessSwitcher />
          )}
          <div className="ml-auto hidden items-center gap-2 text-sm text-muted-foreground sm:flex">
            {user?.is_active ? (
              <>
                <span className="size-2 rounded-full bg-success" />
                Sesión activa
              </>
            ) : (
              <Spinner className="size-4" />
            )}
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8">
          <div className="mx-auto w-full max-w-6xl space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
