import { useQuery } from "@tanstack/react-query";
import {
  CalendarDays,
  CircleCheck,
  DollarSign,
  Scissors,
  Star,
  UserX,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Spinner } from "@/components/spinner";
import { StatCard } from "@/components/stat-card";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCurrentBusiness } from "@/features/business/business-context";
import { getApiErrorMessage } from "@/lib/api/client";
import { getBusinessStats } from "@/lib/api/stats";
import type {
  BookingStatus,
  BusinessStats,
  StatsParams,
} from "@/lib/api/types";
import {
  BOOKING_STATUS_LABELS,
  formatMoney,
  toDateInput,
} from "@/lib/format";
import { timezoneLabel } from "@/lib/timezones";
import { cn } from "@/lib/utils";

type Preset = "history" | "month" | "30d" | "today";

const PRESETS: { key: Preset; label: string }[] = [
  { key: "history", label: "Histórico" },
  { key: "month", label: "Este mes" },
  { key: "30d", label: "Últimos 30 días" },
  { key: "today", label: "Hoy" },
];

const STATUS_ORDER: BookingStatus[] = [
  "pending",
  "confirmed",
  "completed",
  "no_show",
  "cancelled",
];

const STATUS_BAR_COLORS: Record<BookingStatus, string> = {
  pending: "bg-gradient-to-r from-amber-400 to-orange-500",
  confirmed: "bg-gradient-to-r from-indigo-500 to-violet-500",
  completed: "bg-gradient-to-r from-emerald-500 to-teal-500",
  no_show: "bg-gradient-to-r from-rose-500 to-red-500",
  cancelled: "bg-gradient-to-r from-slate-400 to-slate-500",
};

function buildParams(preset: Preset): StatsParams {
  const today = new Date();

  if (preset === "today") {
    const value = toDateInput(today);
    return { date_from: value, date_to: value };
  }

  if (preset === "month") {
    const first = new Date(today.getFullYear(), today.getMonth(), 1);
    return { date_from: toDateInput(first), date_to: toDateInput(today) };
  }

  if (preset === "30d") {
    const from = new Date(today);
    from.setDate(from.getDate() - 29);
    return { date_from: toDateInput(from), date_to: toDateInput(today) };
  }

  return {};
}

function countOf(stats: BusinessStats, status: BookingStatus): number {
  return stats.bookings_by_status[status] ?? 0;
}

export function DashboardPage() {
  const business = useCurrentBusiness();
  const [preset, setPreset] = useState<Preset>("month");
  const params = useMemo(() => buildParams(preset), [preset]);

  const query = useQuery({
    queryKey: ["stats", business.id, params],
    queryFn: () => getBusinessStats(business.id, params),
  });

  const stats = query.data;
  const total = stats?.total_bookings ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resumen"
        description={`${business.name} · ${timezoneLabel(business.timezone)}`}
        actions={
          <div className="flex flex-wrap gap-1 rounded-lg border border-border/70 bg-card/80 p-1 shadow-sm backdrop-blur">
            {PRESETS.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setPreset(item.key)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                  preset === item.key
                    ? "bg-brand-gradient text-white shadow-sm shadow-primary/25"
                    : "text-muted-foreground hover:bg-primary/5 hover:text-foreground",
                )}
              >
                {item.label}
              </button>
            ))}
          </div>
        }
      />

      {query.isError ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 p-10 text-center">
            <p className="font-medium">No se pudieron cargar las estadísticas.</p>
            <p className="text-sm text-muted-foreground">
              {getApiErrorMessage(query.error)}
            </p>
            <button
              type="button"
              onClick={() => void query.refetch()}
              className="text-sm font-medium text-primary hover:underline"
            >
              Reintentar
            </button>
          </CardContent>
        </Card>
      ) : query.isLoading || !stats ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              icon={CalendarDays}
              label="Reservas"
              value={String(stats.total_bookings)}
              hint="En el periodo seleccionado"
            />
            <StatCard
              icon={DollarSign}
              label="Ingresos"
              value={formatMoney(stats.revenue_completed, stats.currency)}
              hint="Solo reservas completadas"
              tone="success"
            />
            <StatCard
              icon={CircleCheck}
              label="Completadas"
              value={String(countOf(stats, "completed"))}
              hint={
                total > 0
                  ? `${Math.round((countOf(stats, "completed") / total) * 100)}% del total`
                  : "Sin reservas"
              }
              tone="success"
            />
            <StatCard
              icon={UserX}
              label="No asistencias"
              value={String(countOf(stats, "no_show"))}
              hint={
                total > 0
                  ? `${Math.round((countOf(stats, "no_show") / total) * 100)}% del total`
                  : "Sin reservas"
              }
              tone="destructive"
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Reservas por estado</CardTitle>
                <CardDescription>
                  Distribución del periodo seleccionado.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {total === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Todavía no hay reservas en este periodo.
                  </p>
                ) : (
                  STATUS_ORDER.map((status) => {
                    const count = countOf(stats, status);
                    const percent = Math.round((count / total) * 100);
                    return (
                      <div key={status} className="space-y-1.5">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium">
                            {BOOKING_STATUS_LABELS[status]}
                          </span>
                          <span className="text-muted-foreground">
                            {count} · {percent}%
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted/80">
                          <div
                            className={cn(
                              "h-full rounded-full transition-all",
                              STATUS_BAR_COLORS[status],
                            )}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Valoración</CardTitle>
                <CardDescription>Opinión de tus clientes.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-brand-gradient text-4xl font-semibold tracking-tight">
                    {business.rating_avg.toFixed(1)}
                  </span>
                  <div className="space-y-1">
                    <Stars rating={business.rating_avg} />
                    <p className="text-xs text-muted-foreground">
                      {business.rating_count}{" "}
                      {business.rating_count === 1 ? "reseña" : "reseñas"}
                    </p>
                  </div>
                </div>
                <div className="rounded-lg bg-muted/60 p-3 text-xs text-muted-foreground">
                  Las reseñas se habilitan cuando una cita se marca como
                  completada.
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <RankingCard
              title="Servicios más reservados"
              description="Sin contar reservas canceladas."
              icon={Scissors}
              items={stats.top_services}
            />
            <RankingCard
              title="Empleados con más reservas"
              description="Sin contar reservas canceladas."
              icon={Users}
              items={stats.top_staff}
            />
          </div>
        </>
      )}
    </div>
  );
}

function Stars({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, index) => (
        <Star
          key={index}
          className={cn(
            "size-4",
            index < Math.round(rating)
              ? "fill-warning text-warning"
              : "text-muted-foreground/40",
          )}
        />
      ))}
    </div>
  );
}

function RankingCard({
  title,
  description,
  icon: Icon,
  items,
}: {
  title: string;
  description: string;
  icon: typeof Scissors;
  items: { id: string; name: string; count: number }[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyState
            icon={Icon}
            title="Sin datos todavía"
            description="Aparecerán aquí en cuanto registres reservas."
            className="border-0 p-6"
          />
        ) : (
          <ol className="space-y-2">
            {items.map((item, index) => (
              <li
                key={item.id}
                className="flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-primary/5"
              >
                <span
                  className={cn(
                    "flex size-7 items-center justify-center rounded-full text-xs font-semibold",
                    index === 0
                      ? "bg-gradient-to-br from-amber-300 to-yellow-500 text-amber-950 shadow-sm"
                      : index === 1
                        ? "bg-gradient-to-br from-slate-300 to-slate-400 text-slate-800 shadow-sm"
                        : index === 2
                          ? "bg-gradient-to-br from-orange-400 to-rose-400 text-white shadow-sm"
                          : "bg-muted text-muted-foreground",
                  )}
                >
                  {index + 1}
                </span>
                <span className="min-w-0 flex-1 truncate text-sm font-medium">
                  {item.name}
                </span>
                <Badge variant="secondary">
                  {item.count}{" "}
                  {item.count === 1 ? "reserva" : "reservas"}
                </Badge>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}

function LoadingState() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-28 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Skeleton className="h-64 rounded-xl lg:col-span-2" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
      <div className="flex items-center justify-center gap-2 py-4 text-sm text-muted-foreground">
        <Spinner className="size-4" /> Cargando estadísticas…
      </div>
    </div>
  );
}
