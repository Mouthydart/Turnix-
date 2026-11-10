import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, LoaderCircle, RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
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
import { listBusinessBookings, updateBookingStatus } from "@/lib/api/bookings";
import { getApiErrorMessage } from "@/lib/api/client";
import { listServices } from "@/lib/api/services";
import { listStaff } from "@/lib/api/staff";
import type {
  Booking,
  BookingListParams,
  BookingStatus,
} from "@/lib/api/types";
import {
  BOOKING_STATUS_LABELS,
  formatDateTime,
  formatTime,
} from "@/lib/format";

const PAGE_SIZE = 20;

const STATUS_OPTIONS: BookingStatus[] = [
  "pending",
  "confirmed",
  "completed",
  "no_show",
  "cancelled",
];

interface Filters {
  status: string;
  staffId: string;
  serviceId: string;
  dateFrom: string;
  dateTo: string;
}

const EMPTY_FILTERS: Filters = {
  status: "",
  staffId: "",
  serviceId: "",
  dateFrom: "",
  dateTo: "",
};

interface PendingAction {
  booking: Booking;
  status: BookingStatus;
}

const ACTION_DETAILS: Record<
  BookingStatus,
  { title: string; note: string; confirmLabel: string; destructive: boolean }
> = {
  pending: {
    title: "Marcar como pendiente",
    note: "La reserva volverá a quedar pendiente de confirmación.",
    confirmLabel: "Marcar pendiente",
    destructive: false,
  },
  confirmed: {
    title: "Confirmar reserva",
    note: "La cita pasará a estado confirmado y el cliente la verá como tal.",
    confirmLabel: "Confirmar",
    destructive: false,
  },
  completed: {
    title: "Marcar como completada",
    note: "Se registrará como asistida y el cliente podrá dejar una reseña.",
    confirmLabel: "Completar",
    destructive: false,
  },
  no_show: {
    title: "Registrar inasistencia",
    note: "La cita se marcará como no asistida y no contará como ingreso.",
    confirmLabel: "Registrar no asistencia",
    destructive: true,
  },
  cancelled: {
    title: "Cancelar reserva",
    note: "La cita se cancelará y liberará el horario para otros clientes.",
    confirmLabel: "Cancelar reserva",
    destructive: true,
  },
};

export function BookingsPage() {
  const business = useCurrentBusiness();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [page, setPage] = useState(0);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(
    null,
  );

  const params = useMemo<BookingListParams>(() => {
    const result: BookingListParams = {
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    };
    if (filters.status) result.status = filters.status as BookingStatus;
    if (filters.staffId) result.staff_id = filters.staffId;
    if (filters.serviceId) result.service_id = filters.serviceId;
    if (filters.dateFrom) result.date_from = filters.dateFrom;
    if (filters.dateTo) result.date_to = filters.dateTo;
    return result;
  }, [filters, page]);

  const bookingsQuery = useQuery({
    queryKey: ["bookings", business.id, params],
    queryFn: () => listBusinessBookings(business.id, params),
  });

  const servicesQuery = useQuery({
    queryKey: ["services", business.id],
    queryFn: () => listServices(business.id),
  });

  const staffQuery = useQuery({
    queryKey: ["staff", business.id],
    queryFn: () => listStaff(business.id),
  });

  const serviceNames = useMemo(
    () => new Map(servicesQuery.data?.map((item) => [item.id, item.name])),
    [servicesQuery.data],
  );

  const staffNames = useMemo(
    () =>
      new Map(staffQuery.data?.map((item) => [item.id, item.display_name])),
    [staffQuery.data],
  );

  const statusMutation = useMutation({
    mutationFn: ({ booking, status }: PendingAction) =>
      updateBookingStatus(business.id, booking.id, { status }),
    onSuccess: (_data, variables) => {
      toast.success(
        `Reserva ${BOOKING_STATUS_LABELS[variables.status].toLowerCase()}`,
        {
          description: `Cliente: ${variables.booking.customer_name ?? "Sin nombre"}.`,
        },
      );
      setPendingAction(null);
      void queryClient.invalidateQueries({ queryKey: ["bookings"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (error) => {
      toast.error("No se pudo actualizar la reserva", {
        description: getApiErrorMessage(error),
      });
    },
  });

  const bookings = bookingsQuery.data ?? [];
  const hasFilters = Object.values(filters).some(Boolean);
  const actionDetails = pendingAction
    ? ACTION_DETAILS[pendingAction.status]
    : null;

  function updateFilter<K extends keyof Filters>(key: K, value: Filters[K]) {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(0);
  }

  function resetFilters() {
    setFilters(EMPTY_FILTERS);
    setPage(0);
  }

  function actionsFor(booking: Booking): BookingStatus[] {
    if (booking.status === "pending") return ["confirmed", "cancelled"];
    if (booking.status === "confirmed")
      return ["completed", "no_show", "cancelled"];
    return [];
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reservas"
        description="Consulta, filtra y actualiza el estado de las citas."
        actions={
          <Button
            variant="outline"
            onClick={() => void bookingsQuery.refetch()}
            disabled={bookingsQuery.isFetching}
          >
            {bookingsQuery.isFetching ? (
              <LoaderCircle className="animate-spin" />
            ) : (
              <RefreshCw />
            )}
            Actualizar
          </Button>
        }
      />

      <Card>
        <CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Estado
            </span>
            <Select
              value={filters.status}
              onChange={(event) => updateFilter("status", event.target.value)}
            >
              <option value="">Todos</option>
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {BOOKING_STATUS_LABELS[status]}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Empleado
            </span>
            <Select
              value={filters.staffId}
              onChange={(event) => updateFilter("staffId", event.target.value)}
            >
              <option value="">Todos</option>
              {staffQuery.data?.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.display_name}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Servicio
            </span>
            <Select
              value={filters.serviceId}
              onChange={(event) =>
                updateFilter("serviceId", event.target.value)
              }
            >
              <option value="">Todos</option>
              {servicesQuery.data?.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Desde
            </span>
            <Input
              type="date"
              value={filters.dateFrom}
              onChange={(event) =>
                updateFilter("dateFrom", event.target.value)
              }
            />
          </div>

          <div className="space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Hasta
            </span>
            <Input
              type="date"
              value={filters.dateTo}
              onChange={(event) => updateFilter("dateTo", event.target.value)}
            />
          </div>

          {hasFilters ? (
            <div className="lg:col-span-5">
              <Button variant="ghost" size="sm" onClick={resetFilters}>
                Limpiar filtros
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        {bookingsQuery.isError ? (
          <CardContent className="flex flex-col items-center gap-3 p-10 text-center">
            <p className="font-medium">No se pudieron cargar las reservas.</p>
            <p className="text-sm text-muted-foreground">
              {getApiErrorMessage(bookingsQuery.error)}
            </p>
            <Button variant="outline" onClick={() => void bookingsQuery.refetch()}>
              Reintentar
            </Button>
          </CardContent>
        ) : bookingsQuery.isLoading ? (
          <CardContent className="space-y-3 p-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} className="h-12 rounded-lg" />
            ))}
          </CardContent>
        ) : bookings.length === 0 ? (
          <CardContent className="p-6">
            <EmptyState
              icon={CalendarDays}
              title="No hay reservas"
              description={
                hasFilters
                  ? "Prueba con otros filtros o limpia la búsqueda."
                  : "Cuando tus clientes reserven, las citas aparecerán aquí."
              }
              className="border-0"
            />
          </CardContent>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Servicio</TableHead>
                  <TableHead>Empleado</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bookings.map((booking) => (
                  <TableRow key={booking.id}>
                    <TableCell>
                      <div className="space-y-0.5">
                        <p className="font-medium">
                          {booking.customer_name ?? "Cliente"}
                        </p>
                        {booking.customer_phone ? (
                          <p className="text-xs text-muted-foreground">
                            {booking.customer_phone}
                          </p>
                        ) : null}
                      </div>
                    </TableCell>
                    <TableCell>
                      {serviceNames.get(booking.service_id) ?? "—"}
                    </TableCell>
                    <TableCell>
                      {staffNames.get(booking.staff_id) ?? "—"}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-0.5">
                        <p>{formatDateTime(booking.start_at, business.timezone)}</p>
                        <p className="text-xs text-muted-foreground">
                          hasta {formatTime(booking.end_at, business.timezone)}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={booking.status} />
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap justify-end gap-1">
                        {actionsFor(booking).length === 0 ? (
                          <span className="text-xs text-muted-foreground">
                            —
                          </span>
                        ) : (
                          actionsFor(booking).map((status) => {
                            const details = ACTION_DETAILS[status];
                            return (
                              <Button
                                key={status}
                                size="sm"
                                variant={
                                  status === "cancelled"
                                    ? "ghost"
                                    : status === "no_show"
                                      ? "outline"
                                      : "secondary"
                                }
                                className={
                                  status === "cancelled"
                                    ? "text-destructive hover:text-destructive"
                                    : undefined
                                }
                                onClick={() =>
                                  setPendingAction({ booking, status })
                                }
                              >
                                {details.confirmLabel}
                              </Button>
                            );
                          })
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            <div className="flex flex-col items-center justify-between gap-3 border-t p-4 sm:flex-row">
              <p className="text-xs text-muted-foreground">
                Página {page + 1} · {bookings.length}{" "}
                {bookings.length === 1 ? "reserva" : "reservas"} mostradas
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0 || bookingsQuery.isFetching}
                  onClick={() => setPage((current) => Math.max(0, current - 1))}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={
                    bookings.length < PAGE_SIZE || bookingsQuery.isFetching
                  }
                  onClick={() => setPage((current) => current + 1)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>

      <ConfirmDialog
        open={Boolean(pendingAction)}
        onOpenChange={(open) => {
          if (!open && !statusMutation.isPending) {
            setPendingAction(null);
          }
        }}
        title={actionDetails?.title ?? ""}
        description={
          pendingAction
            ? `${pendingAction.booking.customer_name ?? "Cliente"} · ${
                serviceNames.get(pendingAction.booking.service_id) ?? "Servicio"
              }`
            : ""
        }
        note={actionDetails?.note}
        confirmLabel={actionDetails?.confirmLabel}
        destructive={actionDetails?.destructive}
        isLoading={statusMutation.isPending}
        onConfirm={() => {
          if (pendingAction) {
            statusMutation.mutate(pendingAction);
          }
        }}
      />
    </div>
  );
}
