import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CalendarDays,
  Check,
  Clock,
  LoaderCircle,
  MapPin,
  Phone,
  Star,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { EmptyState } from "@/components/empty-state";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { createBooking, getAvailability } from "@/lib/api/bookings";
import { getCatalogBusiness } from "@/lib/api/catalog";
import { getApiErrorMessage } from "@/lib/api/client";
import type { Service, Staff } from "@/lib/api/types";
import {
  formatDateOnly,
  formatDuration,
  formatMoney,
  formatTime,
  initials,
  toDateInput,
} from "@/lib/format";
import { cn } from "@/lib/utils";

function defaultBookingDate(): string {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return toDateInput(tomorrow);
}

function StepTitle({ step, title }: { step: number; title: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex size-7 items-center justify-center rounded-full bg-brand-soft text-xs font-semibold text-primary ring-1 ring-primary/10">
        {step}
      </span>
      <CardTitle>{title}</CardTitle>
    </div>
  );
}

export function CustomerBusinessPage() {
  const { businessId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [serviceId, setServiceId] = useState("");
  const [staffId, setStaffId] = useState("");
  const [date, setDate] = useState(defaultBookingDate);
  const [slotStartAt, setSlotStartAt] = useState("");
  const [notes, setNotes] = useState("");

  const businessQuery = useQuery({
    queryKey: ["catalog", "business", businessId],
    queryFn: () => getCatalogBusiness(businessId),
    enabled: Boolean(businessId),
  });

  const business = businessQuery.data;
  const services = business?.services ?? [];
  const staff = business?.staff ?? [];

  const selectedService = services.find((service) => service.id === serviceId);
  const selectedStaff = staff.find((member) => member.id === staffId);
  const availableStaff = useMemo(
    () =>
      serviceId
        ? staff.filter((member) => member.services.includes(serviceId))
        : [],
    [serviceId, staff],
  );

  const availabilityQuery = useQuery({
    queryKey: ["availability", businessId, serviceId, staffId, date],
    queryFn: () =>
      getAvailability(businessId, {
        service_id: serviceId,
        staff_id: staffId,
        date,
      }),
    enabled: Boolean(businessId && serviceId && staffId && date),
    retry: false,
  });

  const slots = useMemo(
    () =>
      (availabilityQuery.data?.slots ?? []).filter(
        (slot) => new Date(slot.start_at).getTime() > Date.now(),
      ),
    [availabilityQuery.data],
  );

  const selectedSlot = slots.find((slot) => slot.start_at === slotStartAt);

  useEffect(() => {
    if (slotStartAt && !slots.some((slot) => slot.start_at === slotStartAt)) {
      setSlotStartAt("");
    }
  }, [slotStartAt, slots]);

  function chooseService(service: Service) {
    setServiceId(service.id);
    setSlotStartAt("");
    setNotes("");
    setStaffId((current) => {
      const matching = staff.filter((member) =>
        member.services.includes(service.id),
      );
      return matching.some((member) => member.id === current)
        ? current
        : (matching[0]?.id ?? "");
    });
  }

  function chooseStaff(member: Staff) {
    setStaffId(member.id);
    setSlotStartAt("");
  }

  const bookingMutation = useMutation({
    mutationFn: () =>
      createBooking(businessId, {
        service_id: serviceId,
        staff_id: staffId,
        start_at: slotStartAt,
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      toast.success("Reserva creada", {
        description:
          "Tu cita quedó pendiente de confirmación por el negocio.",
      });
      void queryClient.invalidateQueries({ queryKey: ["bookings", "mine"] });
      void queryClient.invalidateQueries({ queryKey: ["availability"] });
      navigate("/cliente/bookings");
    },
    onError: (error) => {
      toast.error("No se pudo crear la reserva", {
        description: getApiErrorMessage(error),
      });
    },
  });

  if (businessQuery.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-32 rounded-xl" />
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <Skeleton className="h-96 rounded-xl" />
          <Skeleton className="h-72 rounded-xl" />
        </div>
      </div>
    );
  }

  if (businessQuery.isError || !business) {
    return (
      <div className="space-y-6">
        <Link
          to="/cliente"
          className={cn(
            buttonVariants({ variant: "ghost", size: "sm" }),
            "-ml-3",
          )}
        >
          <ArrowLeft />
          Volver a explorar
        </Link>
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <p className="font-medium">No se pudo cargar el negocio.</p>
            <p className="text-sm text-muted-foreground">
              {businessQuery.isError
                ? getApiErrorMessage(businessQuery.error)
                : "El negocio no está disponible."}
            </p>
            <Button
              variant="outline"
              onClick={() => void businessQuery.refetch()}
            >
              Reintentar
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const today = toDateInput();

  return (
    <div className="space-y-6">
      <Link
        to="/cliente"
        className={cn(
          buttonVariants({ variant: "ghost", size: "sm" }),
          "-ml-3",
        )}
      >
        <ArrowLeft />
        Volver a explorar
      </Link>

      <Card className="relative overflow-hidden border-primary/20 bg-gradient-to-br from-primary/5 via-card to-fuchsia-500/5">
        <div className="pointer-events-none absolute -right-16 -top-20 size-48 rounded-full bg-primary/10 blur-3xl" />
        <CardContent className="relative flex flex-col gap-4 p-6 sm:flex-row sm:items-start">
          <span className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-brand-gradient text-xl font-semibold text-white shadow-md shadow-primary/25">
            {business.name.charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0 flex-1 space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight">
              {business.name}
            </h1>
            {business.description ? (
              <p className="max-w-2xl text-sm text-muted-foreground">
                {business.description}
              </p>
            ) : null}
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Star className="size-4 fill-warning text-warning" />
                {business.rating_count > 0
                  ? `${business.rating_avg.toFixed(1)} (${business.rating_count})`
                  : "Nuevo en Turnix"}
              </span>
              {business.address ? (
                <span className="flex items-center gap-1.5">
                  <MapPin className="size-4" />
                  {business.address}
                </span>
              ) : null}
              {business.phone ? (
                <span className="flex items-center gap-1.5">
                  <Phone className="size-4" />
                  {business.phone}
                </span>
              ) : null}
            </div>
          </div>
        </CardContent>
      </Card>

      {services.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="Este negocio aún no tiene servicios disponibles"
          description="Vuelve a explorar otros negocios o inténtalo de nuevo más tarde."
          action={
            <Link to="/cliente" className={buttonVariants()}>
              Explorar otros negocios
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <StepTitle step={1} title="Elige un servicio" />
                <CardDescription>
                  Selecciona el servicio que quieres reservar.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-2 sm:grid-cols-2">
                {services.map((service) => {
                  const isSelected = service.id === serviceId;
                  return (
                    <button
                      key={service.id}
                      type="button"
                      onClick={() => chooseService(service)}
                      className={cn(
                        "rounded-lg border p-4 text-left transition-colors",
                        isSelected
                          ? "border-primary bg-primary/5 ring-1 ring-primary/20"
                          : "border-border/70 bg-background/60 hover:border-primary/40",
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <span className="font-medium">{service.name}</span>
                        <span className="shrink-0 text-sm font-medium text-primary">
                          {formatMoney(service.price, business.currency)}
                        </span>
                      </div>
                      {service.description ? (
                        <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                          {service.description}
                        </p>
                      ) : null}
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="size-3.5" />
                          {formatDuration(service.duration_minutes)}
                        </span>
                        {service.buffer_minutes > 0 ? (
                          <span>
                            + {formatDuration(service.buffer_minutes)} de margen
                          </span>
                        ) : null}
                      </div>
                    </button>
                  );
                })}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <StepTitle step={2} title="Elige un profesional" />
                <CardDescription>
                  Solo verás profesionales disponibles para el servicio.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!serviceId ? (
                  <p className="text-sm text-muted-foreground">
                    Primero elige un servicio.
                  </p>
                ) : availableStaff.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No hay profesionales disponibles para este servicio.
                  </p>
                ) : (
                  <div className="grid gap-2 sm:grid-cols-2">
                    {availableStaff.map((member) => {
                      const isSelected = member.id === staffId;
                      return (
                        <button
                          key={member.id}
                          type="button"
                          onClick={() => chooseStaff(member)}
                          className={cn(
                            "flex items-center gap-3 rounded-lg border p-3 text-left transition-colors",
                            isSelected
                              ? "border-primary bg-primary/5 ring-1 ring-primary/20"
                              : "border-border/70 bg-background/60 hover:border-primary/40",
                          )}
                        >
                          <span
                            className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-soft text-sm font-semibold text-primary ring-1 ring-primary/10"
                            style={
                              member.color
                                ? { backgroundColor: member.color }
                                : undefined
                            }
                          >
                            {initials(member.display_name)}
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block truncate font-medium">
                              {member.display_name}
                            </span>
                            <span className="block truncate text-sm text-muted-foreground">
                              {member.title ?? "Profesional"}
                            </span>
                          </span>
                          {isSelected ? (
                            <Check className="size-4 shrink-0 text-primary" />
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <StepTitle step={3} title="Elige fecha y hora" />
                <CardDescription>
                  Los horarios se muestran en la zona del negocio.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="max-w-xs space-y-1.5">
                  <label
                    htmlFor="booking-date"
                    className="text-sm font-medium"
                  >
                    Fecha
                  </label>
                  <Input
                    id="booking-date"
                    type="date"
                    min={today}
                    value={date}
                    onChange={(event) => {
                      setDate(event.target.value);
                      setSlotStartAt("");
                    }}
                  />
                </div>

                {!serviceId || !staffId ? (
                  <p className="text-sm text-muted-foreground">
                    Elige un servicio y un profesional para ver la
                    disponibilidad.
                  </p>
                ) : availabilityQuery.isLoading ? (
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
                    {Array.from({ length: 10 }).map((_, index) => (
                      <Skeleton key={index} className="h-9 rounded-md" />
                    ))}
                  </div>
                ) : availabilityQuery.isError ? (
                  <div className="flex flex-col items-start gap-2">
                    <p className="text-sm text-muted-foreground">
                      {getApiErrorMessage(availabilityQuery.error)}
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => void availabilityQuery.refetch()}
                    >
                      Reintentar
                    </Button>
                  </div>
                ) : slots.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No hay horarios disponibles para esta fecha. Prueba con
                    otro día u otro profesional.
                  </p>
                ) : (
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
                    {slots.map((slot) => {
                      const isSelected = slot.start_at === slotStartAt;
                      return (
                        <button
                          key={slot.start_at}
                          type="button"
                          onClick={() => setSlotStartAt(slot.start_at)}
                          className={cn(
                            "rounded-md border px-2 py-2 text-sm font-medium transition-colors",
                            isSelected
                              ? "border-primary bg-brand-gradient text-white shadow-sm shadow-primary/25"
                              : "border-border/70 bg-background hover:border-primary/40",
                          )}
                        >
                          {formatTime(slot.start_at, business.timezone)}
                        </button>
                      );
                    })}
                  </div>
                )}

                <div className="space-y-1.5">
                  <label
                    htmlFor="booking-notes"
                    className="text-sm font-medium"
                  >
                    Notas (opcional)
                  </label>
                  <Textarea
                    id="booking-notes"
                    maxLength={1000}
                    placeholder="Indicaciones para el negocio o el profesional"
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="h-fit lg:sticky lg:top-24">
            <CardHeader>
              <CardTitle>Tu reserva</CardTitle>
              <CardDescription>Revisa los detalles antes de confirmar.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 text-sm">
                <SummaryRow label="Negocio" value={business.name} />
                <SummaryRow
                  label="Servicio"
                  value={selectedService?.name ?? "Sin elegir"}
                />
                <SummaryRow
                  label="Profesional"
                  value={selectedStaff?.display_name ?? "Sin elegir"}
                />
                <SummaryRow
                  label="Fecha"
                  value={date ? formatDateOnly(date) : "Sin elegir"}
                />
                <SummaryRow
                  label="Hora"
                  value={
                    selectedSlot
                      ? `${formatTime(selectedSlot.start_at, business.timezone)} – ${formatTime(selectedSlot.end_at, business.timezone)}`
                      : "Sin elegir"
                  }
                />
                <SummaryRow
                  label="Duración"
                  value={
                    selectedService
                      ? formatDuration(selectedService.duration_minutes)
                      : "—"
                  }
                />
                <SummaryRow
                  label="Precio"
                  value={
                    selectedService
                      ? formatMoney(selectedService.price, business.currency)
                      : "—"
                  }
                />
              </div>

              <Button
                type="button"
                className="w-full"
                size="lg"
                disabled={!selectedSlot || bookingMutation.isPending}
                onClick={() => bookingMutation.mutate()}
              >
                {bookingMutation.isPending ? (
                  <LoaderCircle className="animate-spin" />
                ) : null}
                Confirmar reserva
              </Button>
              <p className="text-xs text-muted-foreground">
                La reserva queda pendiente hasta que el negocio la confirme.
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
