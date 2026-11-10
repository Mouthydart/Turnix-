import { Check, LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Logo } from "@/components/logo";
import { BusinessForm } from "@/features/business/business-form";
import { useAuth } from "@/features/auth/auth-context";
import { initials } from "@/lib/format";

const PERKS = [
  "Agenda centralizada con disponibilidad en tiempo real.",
  "Servicios y empleados con sus propios horarios.",
  "Estadísticas de reservas e ingresos.",
];

const PREVIEW_ROWS = [
  { time: "09:00", label: "Corte + barba", dot: "bg-indigo-500" },
  { time: "10:30", label: "Manicure", dot: "bg-emerald-500" },
  { time: "12:00", label: "Coloración", dot: "bg-amber-500" },
];

export function NoBusinessScreen() {
  const { user, logout } = useAuth();

  return (
    <div className="bg-app relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute -right-32 -top-32 size-96 rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -left-24 size-96 rounded-full bg-fuchsia-400/10 blur-3xl" />

      <header className="relative border-b bg-card/70 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <Logo />
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium">{user?.full_name}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <span className="flex size-9 items-center justify-center rounded-full bg-brand-gradient text-sm font-semibold text-white shadow-sm shadow-primary/25">
              {initials(user?.full_name ?? "?")}
            </span>
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
      </header>

      <main className="relative mx-auto grid max-w-5xl gap-10 px-4 py-10 lg:grid-cols-[1fr_440px] lg:items-start lg:py-16">
        <div className="space-y-5">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-soft px-3 py-1 text-xs font-medium text-primary ring-1 ring-primary/10">
            Primer paso
          </span>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Bienvenido a{" "}
            <span className="text-brand-gradient">Turnix</span>
          </h1>
          <p className="max-w-prose text-muted-foreground">
            Crea tu negocio para empezar a gestionar servicios, empleados y
            reservas desde un solo lugar. Podrás configurar el horario y la
            disponibilidad después.
          </p>
          <ul className="space-y-3 text-sm text-muted-foreground">
            {PERKS.map((perk) => (
              <li key={perk} className="flex items-center gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-soft text-primary ring-1 ring-primary/10">
                  <Check className="size-3.5" />
                </span>
                {perk}
              </li>
            ))}
          </ul>

          <div className="max-w-md rounded-2xl border border-border/70 bg-card/80 p-4 shadow-sm shadow-slate-900/5 backdrop-blur">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-medium">Tu agenda de hoy</p>
              <span className="rounded-full bg-brand-soft px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-primary">
                Vista previa
              </span>
            </div>
            <div className="space-y-2">
              {PREVIEW_ROWS.map((row) => (
                <div
                  key={row.time}
                  className="flex items-center gap-3 rounded-lg border border-border/60 bg-background/60 px-3 py-2"
                >
                  <span className={`size-2 rounded-full ${row.dot}`} />
                  <span className="text-xs font-medium text-muted-foreground">
                    {row.time}
                  </span>
                  <span className="truncate text-sm">{row.label}</span>
                  <span className="ml-auto h-1.5 w-12 rounded-full bg-muted" />
                </div>
              ))}
            </div>
          </div>
        </div>

        <Card className="relative overflow-hidden border-primary/20 shadow-lg shadow-primary/5">
          <div className="pointer-events-none absolute -right-10 -top-12 size-32 rounded-full bg-primary/10 blur-2xl" />
          <CardHeader className="relative">
            <CardTitle>Datos del negocio</CardTitle>
            <CardDescription>
              Completa la información básica. Podrás editarla más tarde.
            </CardDescription>
          </CardHeader>
          <CardContent className="relative">
            <BusinessForm />
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
