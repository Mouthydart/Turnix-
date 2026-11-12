import { useQuery } from "@tanstack/react-query";
import type { LucideIcon } from "lucide-react";
import {
  CalendarDays,
  Clock3,
  DollarSign,
  Hourglass,
  LoaderCircle,
  RefreshCw,
  Scissors,
  TrendingUp,
  UserPlus,
  Users,
  UserX,
  Wallet,
} from "lucide-react";
import { type ReactNode, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useCurrentBusiness } from "@/features/business/business-context";
import { getApiErrorMessage } from "@/lib/api/client";
import { getBusinessReports } from "@/lib/api/reports";
import type {
  BusinessReports,
  CustomerSummary,
  ReportsParams,
  RevenueBreakdown,
  WaitlistBreakdown,
  WaitlistStatus,
} from "@/lib/api/types";
import {
  WAITLIST_STATUS_LABELS,
  formatDateOnly,
  formatDateTime,
  formatDuration,
  formatMoney,
  toNumber,
} from "@/lib/format";
import { timezoneLabel } from "@/lib/timezones";
import { cn } from "@/lib/utils";

type Preset = "7d" | "30d" | "month" | "year";

const PRESETS: { key: Preset; label: string }[] = [
  { key: "7d", label: "Últimos 7 días" },
  { key: "30d", label: "Últimos 30 días" },
  { key: "month", label: "Este mes" },
  { key: "year", label: "Este año" },
];

const WAITLIST_ORDER: WaitlistStatus[] = [
  "waiting",
  "offered",
  "booked",
  "expired",
  "cancelled",
];

const WAITLIST_BAR_COLORS: Record<WaitlistStatus, string> = {
  waiting: "bg-gradient-to-r from-amber-400 to-orange-500",
  offered: "bg-gradient-to-r from-indigo-500 to-violet-500",
  booked: "bg-gradient-to-r from-emerald-500 to-teal-500",
  expired: "bg-gradient-to-r from-rose-500 to-red-500",
  cancelled: "bg-gradient-to-r from-slate-400 to-slate-500",
};

function todayInTimezone(timeZone: string): string {
  try {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(new Date());
    const values = Object.fromEntries(
      parts.map((part) => [part.type, part.value]),
    );
    return `${values.year}-${values.month}-${values.day}`;
  } catch {
    const now = new Date();
    const month = `${now.getMonth() + 1}`.padStart(2, "0");
    const day = `${now.getDate()}`.padStart(2, "0");
    return `${now.getFullYear()}-${month}-${day}`;
  }
}

function addDays(value: string, days: number): string {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function rangeForPreset(
  preset: Preset,
  timeZone: string,
): { from: string; to: string } {
  const today = todayInTimezone(timeZone);
  if (preset === "7d") return { from: addDays(today, -6), to: today };
  if (preset === "30d") return { from: addDays(today, -29), to: today };
  if (preset === "month") return { from: `${today.slice(0, 7)}-01`, to: today };
  return { from: `${today.slice(0, 4)}-01-01`, to: today };
}

function changeLabel(value: number | null): string {
  if (value === null) return "Sin periodo anterior comparable";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}% vs. periodo anterior`;
}

function percent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function ReportsPage() {
  const business = useCurrentBusiness();
  const initialRange = useMemo(
    () => rangeForPreset("30d", business.timezone),
    [business.timezone],
  );
  const [dateFrom, setDateFrom] = useState(initialRange.from);
  const [dateTo, setDateTo] = useState(initialRange.to);
  const [preset, setPreset] = useState<Preset | "custom">("30d");

  const params = useMemo<ReportsParams>(() => {
    const result: ReportsParams = {};
    if (dateFrom) result.date_from = dateFrom;
    if (dateTo) result.date_to = dateTo;
    return result;
  }, [dateFrom, dateTo]);

  const query = useQuery({
    queryKey: ["reports", business.id, params],
    queryFn: () => getBusinessReports(business.id, params),
  });

  function applyPreset(key: Preset) {
    const range = rangeForPreset(key, business.timezone);
    setDateFrom(range.from);
    setDateTo(range.to);
    setPreset(key);
  }

  const report = query.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reportes"
        description={`${business.name} · ${timezoneLabel(business.timezone)}`}
        actions={
          <Button
            variant="outline"
            onClick={() => void query.refetch()}
            disabled={query.isFetching}
          >
            {query.isFetching ? (
              <LoaderCircle className="animate-spin" />
            ) : (
              <RefreshCw />
            )}
            Actualizar
          </Button>
        }
      />

      <Card>
        <CardContent className="flex flex-col gap-4 p-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex flex-wrap gap-1 rounded-lg border border-border/70 bg-card/80 p-1 shadow-sm">
            {PRESETS.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => applyPreset(item.key)}
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

          <div className="flex flex-wrap items-end gap-3">
            <label className="space-y-1.5 text-xs font-medium text-muted-foreground">
              Desde
              <Input
                type="date"
                value={dateFrom}
                max={dateTo || undefined}
                onChange={(event) => {
                  setDateFrom(event.target.value);
                  setPreset("custom");
                }}
                className="w-40"
              />
            </label>
            <label className="space-y-1.5 text-xs font-medium text-muted-foreground">
              Hasta
              <Input
                type="date"
                value={dateTo}
                min={dateFrom || undefined}
                onChange={(event) => {
                  setDateTo(event.target.value);
                  setPreset("custom");
                }}
                className="w-40"
              />
            </label>
          </div>
        </CardContent>
      </Card>

      {query.isError ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 p-10 text-center">
            <p className="font-medium">No se pudieron cargar los reportes.</p>
            <p className="text-sm text-muted-foreground">
              {getApiErrorMessage(query.error)}
            </p>
            <Button variant="outline" onClick={() => void query.refetch()}>
              Reintentar
            </Button>
          </CardContent>
        </Card>
      ) : query.isLoading || !report ? (
        <LoadingState />
      ) : (
        <>
          <SummaryCards report={report} />
          <RevenueSection report={report} />
          <OccupancySection report={report} />
          <ProfitabilitySection report={report} />
          <WaitlistSection report={report} />
          <CustomersSection report={report} />
        </>
      )}
    </div>
  );
}

function SummaryCards({ report }: { report: BusinessReports }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <StatCard
        icon={DollarSign}
        label="Ingresos"
        value={formatMoney(report.revenue.total_revenue, report.currency)}
        hint={changeLabel(report.revenue.revenue_change_percent)}
        tone="success"
      />
      <StatCard
        icon={Wallet}
        label="Ticket promedio"
        value={formatMoney(report.revenue.average_ticket, report.currency)}
        hint={changeLabel(report.revenue.average_ticket_change_percent)}
      />
      <StatCard
        icon={CalendarDays}
        label="Ocupación"
        value={percent(report.occupancy.occupancy_rate)}
        hint={`${formatDuration(report.occupancy.booked_minutes)} de ${formatDuration(report.occupancy.available_minutes)}`}
      />
      <StatCard
        icon={Clock3}
        label="Ingreso por hora"
        value={formatMoney(report.profitability.revenue_per_hour, report.currency)}
        hint={`${formatDuration(report.profitability.slot_minutes)} de agenda vendida`}
        tone="warning"
      />
      <StatCard
        icon={Hourglass}
        label="Conversión de lista de espera"
        value={percent(report.waitlist.conversion_rate)}
        hint={`${report.waitlist.total_entries} solicitudes · ${formatMoney(report.waitlist.estimated_value, report.currency)} estimados`}
      />
      <StatCard
        icon={Users}
        label="Retención de clientes"
        value={
          report.customers.retention_rate === null
            ? "—"
            : percent(report.customers.retention_rate)
        }
        hint={`${report.customers.returning_customers} recurrentes · ${report.customers.new_customers} nuevos`}
      />
    </div>
  );
}

function RevenueSection({ report }: { report: BusinessReports }) {
  const days = report.revenue.daily.slice(-14);
  const max = Math.max(...days.map((day) => toNumber(day.revenue)), 0);

  return (
    <Section
      icon={TrendingUp}
      title="Ingresos y ticket promedio"
      description="Solo se incluyen reservas completadas. El comparativo usa el periodo anterior de igual duración."
    >
      <div className="space-y-3">
        <p className="text-sm font-medium">Ingresos por día</p>
        {days.length === 0 ? (
          <EmptyState
            icon={TrendingUp}
            title="Sin ingresos en el periodo"
            description="Marca reservas como completadas para ver su aporte."
            className="border-0 p-6"
          />
        ) : (
          <div className="flex h-40 items-end gap-1.5 rounded-lg border border-border/60 bg-muted/20 p-3">
            {days.map((day) => {
              const value = toNumber(day.revenue);
              const height =
                value > 0 && max > 0 ? Math.max((value / max) * 100, 3) : 0;
              return (
                <div
                  key={day.date}
                  className="group flex min-w-0 flex-1 flex-col items-center gap-2"
                  title={`${formatDateOnly(day.date)} · ${formatMoney(value, report.currency)} · ${day.completed_bookings} reservas`}
                >
                  <div className="flex h-24 w-full items-end">
                    <div
                      className="w-full rounded-t bg-brand-gradient transition-all group-hover:brightness-110"
                      style={{ height: `${height}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    {day.date.slice(8)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <RevenueBreakdownTable
          title="Por servicio"
          items={report.revenue.by_service}
          currency={report.currency}
        />
        <RevenueBreakdownTable
          title="Por empleado"
          items={report.revenue.by_staff}
          currency={report.currency}
        />
      </div>
    </Section>
  );
}

function RevenueBreakdownTable({
  title,
  items,
  currency,
}: {
  title: string;
  items: RevenueBreakdown[];
  currency: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{title}</p>
      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
          Sin reservas completadas.
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead className="text-right">Reservas</TableHead>
              <TableHead className="text-right">Ingresos</TableHead>
              <TableHead className="text-right">Ticket</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="font-medium">{item.name}</TableCell>
                <TableCell className="text-right">{item.completed_bookings}</TableCell>
                <TableCell className="text-right">
                  {formatMoney(item.revenue, currency)}
                </TableCell>
                <TableCell className="text-right">
                  {formatMoney(item.average_ticket, currency)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}

function OccupancySection({ report }: { report: BusinessReports }) {
  const days = report.occupancy.daily.slice(-14);
  const hasStaff = report.occupancy.by_staff.length > 0;

  return (
    <Section
      icon={CalendarDays}
      title="Ocupación real de la agenda"
      description="Minutos reservados sobre la capacidad disponible, descontando bloqueos y ausencias."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          <p className="text-sm font-medium">Ocupación por día</p>
          <div className="flex h-40 items-end gap-1.5 rounded-lg border border-border/60 bg-muted/20 p-3">
            {days.map((day) => {
              const height =
                day.occupancy_rate > 0
                  ? Math.min(Math.max(day.occupancy_rate, 3), 100)
                  : 0;
              return (
                <div
                  key={day.date}
                  className="group flex min-w-0 flex-1 flex-col items-center gap-2"
                  title={`${formatDateOnly(day.date)} · ${percent(day.occupancy_rate)} · ${formatDuration(day.booked_minutes)} ocupados`}
                >
                  <div className="flex h-24 w-full items-end">
                    <div
                      className="w-full rounded-t bg-gradient-to-t from-emerald-500 to-teal-400 transition-all group-hover:brightness-110"
                      style={{ height: `${height}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    {day.date.slice(8)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="space-y-2 rounded-lg border border-border/60 bg-muted/30 p-4 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Disponible</span>
            <span className="font-medium">
              {formatDuration(report.occupancy.available_minutes)}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Reservado</span>
            <span className="font-medium">
              {formatDuration(report.occupancy.booked_minutes)}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Libre</span>
            <span className="font-medium">
              {formatDuration(report.occupancy.idle_minutes)}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">No asistencias</span>
            <span className="font-medium text-destructive">
              {formatDuration(report.occupancy.no_show_minutes)}
            </span>
          </div>
        </div>
      </div>

      {!hasStaff ? (
        <p className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
          Agrega empleados activos para calcular la capacidad disponible.
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Empleado</TableHead>
              <TableHead className="text-right">Disponible</TableHead>
              <TableHead className="text-right">Reservado</TableHead>
              <TableHead className="text-right">No asistió</TableHead>
              <TableHead className="text-right">Ocupación</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.occupancy.by_staff.map((member) => (
              <TableRow key={member.id}>
                <TableCell className="font-medium">{member.name}</TableCell>
                <TableCell className="text-right">
                  {formatDuration(member.available_minutes)}
                </TableCell>
                <TableCell className="text-right">
                  {formatDuration(member.booked_minutes)}
                </TableCell>
                <TableCell className="text-right">
                  {formatDuration(member.no_show_minutes)}
                </TableCell>
                <TableCell className="text-right font-medium">
                  {percent(member.occupancy_rate)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Section>
  );
}

function ProfitabilitySection({ report }: { report: BusinessReports }) {
  return (
    <Section
      icon={Scissors}
      title="Rentabilidad por hora de agenda"
      description="Ingresos por hora ocupada, usando la duración real de cada cita más el margen del servicio."
    >
      {report.profitability.by_service.length === 0 ? (
        <EmptyState
          icon={Scissors}
          title="Sin datos de rentabilidad"
          description="Necesitas reservas completadas para comparar servicios."
          className="border-0 p-6"
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Servicio</TableHead>
              <TableHead className="text-right">Reservas</TableHead>
              <TableHead className="text-right">Ingresos</TableHead>
              <TableHead className="text-right">Agenda vendida</TableHead>
              <TableHead className="text-right">Por hora</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.profitability.by_service.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <div className="space-y-0.5">
                    <p className="font-medium">{item.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDuration(item.duration_minutes)} de servicio
                      {item.buffer_minutes > 0
                        ? ` + ${item.buffer_minutes} min de margen`
                        : ""}
                    </p>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  {item.completed_bookings}
                </TableCell>
                <TableCell className="text-right">
                  {formatMoney(item.revenue, report.currency)}
                </TableCell>
                <TableCell className="text-right">
                  {formatDuration(item.slot_minutes)}
                </TableCell>
                <TableCell className="text-right font-medium text-success">
                  {formatMoney(item.revenue_per_hour, report.currency)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Section>
  );
}

function WaitlistSection({ report }: { report: BusinessReports }) {
  const waitlist = report.waitlist;
  const total = waitlist.total_entries;

  return (
    <Section
      icon={Hourglass}
      title="Lista de espera y demanda no atendida"
      description="Solicitudes recibidas en el periodo. El valor es estimado con el precio actual del servicio."
    >
      <div className="grid gap-4 lg:grid-cols-5">
        <div className="space-y-3 rounded-lg border border-border/60 bg-muted/20 p-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Distribución por estado</p>
            <span className="text-xs text-muted-foreground">
              {total} {total === 1 ? "solicitud" : "solicitudes"}
            </span>
          </div>
          {total === 0 ? (
            <p className="py-4 text-sm text-muted-foreground">
              Sin solicitudes en el periodo.
            </p>
          ) : (
            WAITLIST_ORDER.map((status) => {
              const count = waitlist.by_status[status] ?? 0;
              const share = Math.round((count / total) * 100);
              return (
                <div key={status} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">
                      {WAITLIST_STATUS_LABELS[status]}
                    </span>
                    <span className="text-muted-foreground">
                      {count} · {share}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted/80">
                    <div
                      className={cn("h-full rounded-full", WAITLIST_BAR_COLORS[status])}
                      style={{ width: `${share}%` }}
                    />
                  </div>
                </div>
              );
            })
          )}
          <div className="rounded-lg bg-background/70 p-3 text-xs text-muted-foreground">
            Conversión: <strong>{percent(waitlist.conversion_rate)}</strong> · Pérdida:{" "}
            <strong>{percent(waitlist.lost_rate)}</strong> · Convertido estimado:{" "}
            <strong>{formatMoney(waitlist.estimated_converted_value, report.currency)}</strong>
          </div>
        </div>

        <div className="lg:col-span-3">
          <WaitlistTable
            title="Por servicio"
            items={waitlist.by_service}
            currency={report.currency}
          />
        </div>
      </div>

      <WaitlistTable
        title="Por empleado"
        items={waitlist.by_staff}
        currency={report.currency}
      />
    </Section>
  );
}

function WaitlistTable({
  title,
  items,
  currency,
}: {
  title: string;
  items: WaitlistBreakdown[];
  currency: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{title}</p>
      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
          Sin solicitudes en el periodo.
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead className="text-right">En espera</TableHead>
              <TableHead className="text-right">Convertidas</TableHead>
              <TableHead className="text-right">Conversión</TableHead>
              <TableHead className="text-right">Valor estimado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id ?? "sin-asignar"}>
                <TableCell className="font-medium">{item.name}</TableCell>
                <TableCell className="text-right">{item.total}</TableCell>
                <TableCell className="text-right">{item.waiting}</TableCell>
                <TableCell className="text-right">{item.booked}</TableCell>
                <TableCell className="text-right">
                  {percent(item.conversion_rate)}
                </TableCell>
                <TableCell className="text-right">
                  {formatMoney(item.estimated_value, currency)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}

function CustomersSection({ report }: { report: BusinessReports }) {
  const customers = report.customers;

  return (
    <Section
      icon={Users}
      title="Clientes nuevos, recurrentes y retención"
      description="Actividad basada en reservas no canceladas. Los rankings muestran hasta cinco clientes."
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile
          icon={UserPlus}
          label="Nuevos"
          value={String(customers.new_customers)}
          hint={percent(customers.new_customer_rate)}
        />
        <MetricTile
          icon={TrendingUp}
          label="Recurrentes"
          value={String(customers.returning_customers)}
          hint={
            customers.retention_rate === null
              ? "Sin cartera previa"
              : `${percent(customers.retention_rate)} de retención`
          }
        />
        <MetricTile
          icon={RefreshCw}
          label="Repiten en el periodo"
          value={String(customers.repeat_customers)}
          hint={percent(customers.repeat_rate)}
        />
        <MetricTile
          icon={UserX}
          label="Inactivos"
          value={String(customers.inactive_customers_count)}
          hint="Con historial previo"
        />
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-2 rounded-lg border border-border/60 bg-muted/20 p-4 text-sm text-muted-foreground">
        <span>
          Visitas por cliente:{" "}
          <strong className="text-foreground">
            {customers.average_visits_per_customer.toFixed(1)}
          </strong>
        </span>
        <span>
          Días entre visitas:{" "}
          <strong className="text-foreground">
            {customers.average_days_between_visits === null
              ? "—"
              : customers.average_days_between_visits.toFixed(1)}
          </strong>
        </span>
        <span>
          Clientes activos:{" "}
          <strong className="text-foreground">
            {customers.active_customers}
          </strong>
        </span>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <CustomerTable
          title="Clientes más activos"
          items={customers.top_customers}
          timezone={report.timezone}
          currency={report.currency}
          emptyDescription="Aparecerán aquí cuando haya reservas en el periodo."
        />
        <CustomerTable
          title="Clientes inactivos"
          items={customers.inactive_customers}
          timezone={report.timezone}
          currency={report.currency}
          emptyDescription="No hay clientes con historial previo fuera del periodo."
        />
      </div>
    </Section>
  );
}

function CustomerTable({
  title,
  items,
  timezone,
  currency,
  emptyDescription,
}: {
  title: string;
  items: CustomerSummary[];
  timezone: string;
  currency: string;
  emptyDescription: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{title}</p>
      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
          {emptyDescription}
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Cliente</TableHead>
              <TableHead className="text-right">Visitas</TableHead>
              <TableHead className="text-right">Ingresos</TableHead>
              <TableHead className="text-right">Última visita</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((customer) => (
              <TableRow key={customer.id}>
                <TableCell className="font-medium">{customer.name}</TableCell>
                <TableCell className="text-right">{customer.visits}</TableCell>
                <TableCell className="text-right">
                  {formatMoney(customer.completed_revenue, currency)}
                </TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {customer.last_visit
                    ? formatDateTime(customer.last_visit, timezone)
                    : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}

function MetricTile({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border/60 bg-background/60 p-4">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-primary ring-1 ring-primary/10">
        <Icon className="size-4" />
      </span>
      <div className="min-w-0 space-y-0.5">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <p className="text-xl font-semibold">{value}</p>
        <p className="truncate text-xs text-muted-foreground">{hint}</p>
      </div>
    </div>
  );
}

function Section({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-primary ring-1 ring-primary/10">
            <Icon className="size-4" />
          </span>
          <div className="space-y-1">
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">{children}</CardContent>
    </Card>
  );
}

function LoadingState() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-28 rounded-xl" />
        ))}
      </div>
      {Array.from({ length: 3 }).map((_, index) => (
        <Skeleton key={index} className="h-72 rounded-xl" />
      ))}
      <div className="flex items-center justify-center gap-2 py-4 text-sm text-muted-foreground">
        <LoaderCircle className="size-4 animate-spin" /> Preparando reportes…
      </div>
    </div>
  );
}
