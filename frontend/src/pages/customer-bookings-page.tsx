import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Compass } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listMyBookings } from "@/lib/api/bookings";
import { getApiErrorMessage } from "@/lib/api/client";
import { formatDate, formatMoney, formatTime } from "@/lib/format";

export function CustomerBookingsPage() {
  const query = useQuery({
    queryKey: ["bookings", "mine"],
    queryFn: listMyBookings,
  });

  const bookings = query.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Mis reservas"
        description="Consulta el estado de tus citas y tu historial en Turnix."
        actions={
          <Link
            to="/cliente"
            className={buttonVariants({ variant: "outline" })}
          >
            <Compass />
            Explorar negocios
          </Link>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Tus citas</CardTitle>
          <CardDescription>
            Tus reservas aparecerán aquí con su fecha, hora y estado.
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
              description="Explora los negocios disponibles y reserva tu primera cita."
              action={
                <Link to="/cliente" className={buttonVariants()}>
                  Explorar negocios
                </Link>
              }
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
