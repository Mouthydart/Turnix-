import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Sparkles, Store } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/features/auth/auth-context";
import { listMyBookings } from "@/lib/api/bookings";
import { getApiErrorMessage } from "@/lib/api/client";
import {
  formatDate,
  formatMoney,
  formatTime,
} from "@/lib/format";

export function CustomerHomePage() {
  const { user } = useAuth();
  const firstName = user?.full_name.trim().split(/\s+/)[0] ?? "";

  const query = useQuery({
    queryKey: ["bookings", "mine"],
    queryFn: listMyBookings,
  });

  const bookings = query.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={firstName ? `Hola, ${firstName}` : "Tu cuenta"}
        description="Consulta el estado de tus citas y tu historial en Turnix."
      />

      <Card className="relative overflow-hidden border-primary/20 bg-gradient-to-br from-primary/5 via-card to-fuchsia-500/5">
        <div className="pointer-events-none absolute -right-12 -top-16 size-40 rounded-full bg-primary/10 blur-2xl" />
        <CardContent className="relative flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-brand-soft text-primary ring-1 ring-primary/10">
              <Store className="size-5" />
            </span>
            <div className="space-y-1">
              <p className="font-medium">Explora negocios y reserva en línea</p>
              <p className="max-w-xl text-sm text-muted-foreground">
                Estamos preparando el catálogo público de Turnix. Muy pronto
                podrás descubrir negocios y reservar tus servicios desde aquí.
              </p>
            </div>
          </div>
          <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-brand-soft px-3 py-1 text-xs font-medium text-primary ring-1 ring-primary/10">
            <Sparkles className="size-3.5" />
            Próximamente
          </span>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Mis reservas</CardTitle>
          <CardDescription>
            Tus citas aparecerán aquí con su fecha y estado.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {query.isError ? (
            <div className="flex flex-col items-center gap-3 py-6 text-center">
              <p className="font-medium">No se pudieron cargar tus reservas.</p>
              <p className="text-sm text-muted-foreground">
                {getApiErrorMessage(query.error)}
              </p>
              <Button variant="outline" onClick={() => void query.refetch()}>
                Reintentar
              </Button>
            </div>
          ) : query.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} className="h-20 rounded-lg" />
              ))}
            </div>
          ) : bookings.length === 0 ? (
            <EmptyState
              icon={CalendarDays}
              title="Todavía no tienes reservas"
              description="Cuando reserves una cita, aparecerá aquí con su fecha y estado."
              className="border-0"
            />
          ) : (
            <div className="space-y-3">
              {bookings.map((booking) => (
                <div
                  key={booking.id}
                  className="flex flex-col gap-3 rounded-lg border border-border/70 bg-background/60 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex items-start gap-3">
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft text-primary ring-1 ring-primary/10">
                      <CalendarDays className="size-4" />
                    </span>
                    <div className="space-y-1">
                      <p className="font-medium">
                        {formatDate(booking.start_at)}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {formatTime(booking.start_at)} –{" "}
                        {formatTime(booking.end_at)} ·{" "}
                        {formatMoney(booking.price, booking.currency)}
                      </p>
                      {booking.notes ? (
                        <p className="text-xs text-muted-foreground">
                          {booking.notes}
                        </p>
                      ) : null}
                    </div>
                  </div>
                  <StatusBadge status={booking.status} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
