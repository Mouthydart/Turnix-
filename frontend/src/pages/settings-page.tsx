import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, LoaderCircle, Star } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { FormField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCurrentBusiness } from "@/features/business/business-context";
import { updateBusiness } from "@/lib/api/businesses";
import { getApiErrorMessage } from "@/lib/api/client";
import type { PlanName } from "@/lib/api/types";
import { WEEKDAY_LABELS } from "@/lib/format";
import { TIMEZONES, buildTimezoneOption } from "@/lib/timezones";

const CURRENCIES = ["COP", "USD", "MXN", "EUR", "ARS", "CLP", "PEN"];

const schema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "El nombre es obligatorio")
    .max(120, "Máximo 120 caracteres"),
  slug: z
    .string()
    .trim()
    .min(2, "Mínimo 2 caracteres")
    .max(60, "Máximo 60 caracteres"),
  timezone: z.string().min(1, "Selecciona una zona horaria"),
  currency: z.string().min(1, "Selecciona una moneda"),
  phone: z.string().trim().max(30, "Máximo 30 caracteres").optional(),
  address: z.string().trim().max(200, "Máximo 200 caracteres").optional(),
  description: z
    .string()
    .trim()
    .max(1000, "Máximo 1000 caracteres")
    .optional(),
  is_active: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

const PLAN_FEATURES: Record<
  PlanName,
  { label: string; features: string[] }
> = {
  freemium: {
    label: "Freemium",
    features: [
      "Hasta 2 empleados",
      "Hasta 5 servicios",
      "100 reservas al mes",
      "Lista de espera no incluida",
    ],
  },
  pro: {
    label: "Pro",
    features: [
      "Hasta 50 empleados",
      "Hasta 100 servicios",
      "10.000 reservas al mes",
      "Lista de espera incluida",
    ],
  },
};

export function SettingsPage() {
  const business = useCurrentBusiness();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: business.name,
      slug: business.slug,
      timezone: business.timezone,
      currency: business.currency,
      phone: business.phone ?? "",
      address: business.address ?? "",
      description: business.description ?? "",
      is_active: business.is_active,
    },
  });

  useEffect(() => {
    reset({
      name: business.name,
      slug: business.slug,
      timezone: business.timezone,
      currency: business.currency,
      phone: business.phone ?? "",
      address: business.address ?? "",
      description: business.description ?? "",
      is_active: business.is_active,
    });
  }, [business, reset]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      updateBusiness(business.id, {
        name: values.name.trim(),
        slug: values.slug.trim(),
        timezone: values.timezone,
        currency: values.currency,
        phone: values.phone?.trim() || null,
        address: values.address?.trim() || null,
        description: values.description?.trim() || null,
        is_active: values.is_active,
      }),
    onSuccess: () => {
      toast.success("Ajustes guardados");
      void queryClient.invalidateQueries({ queryKey: ["businesses"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (error) => {
      toast.error("No se pudieron guardar los ajustes", {
        description: getApiErrorMessage(error),
      });
    },
  });

  const plan = PLAN_FEATURES[business.plan];
  const timezoneOptions = TIMEZONES.some(
    (timezone) => timezone.value === business.timezone,
  )
    ? TIMEZONES
    : [buildTimezoneOption(business.timezone), ...TIMEZONES];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ajustes"
        description="Configura los datos de tu negocio y revisa tu plan."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Datos del negocio</CardTitle>
            <CardDescription>
              Esta información se muestra a tus clientes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={handleSubmit((values) => mutation.mutate(values))}
              className="space-y-4"
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  label="Nombre"
                  htmlFor="settings-name"
                  error={errors.name?.message}
                  required
                >
                  <Input id="settings-name" {...register("name")} />
                </FormField>

                <FormField
                  label="Slug"
                  htmlFor="settings-slug"
                  error={errors.slug?.message}
                  required
                >
                  <Input id="settings-slug" {...register("slug")} />
                </FormField>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  label="Zona horaria"
                  htmlFor="settings-timezone"
                  error={errors.timezone?.message}
                  required
                >
                  <Select id="settings-timezone" {...register("timezone")}>
                    {timezoneOptions.map((timezone) => (
                      <option key={timezone.value} value={timezone.value}>
                        {timezone.label}
                      </option>
                    ))}
                  </Select>
                </FormField>

                <FormField
                  label="Moneda"
                  htmlFor="settings-currency"
                  error={errors.currency?.message}
                  required
                >
                  <Select id="settings-currency" {...register("currency")}>
                    {CURRENCIES.map((currency) => (
                      <option key={currency} value={currency}>
                        {currency}
                      </option>
                    ))}
                  </Select>
                </FormField>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  label="Teléfono"
                  htmlFor="settings-phone"
                  error={errors.phone?.message}
                >
                  <Input id="settings-phone" {...register("phone")} />
                </FormField>

                <FormField
                  label="Dirección"
                  htmlFor="settings-address"
                  error={errors.address?.message}
                >
                  <Input id="settings-address" {...register("address")} />
                </FormField>
              </div>

              <FormField
                label="Descripción"
                htmlFor="settings-description"
                error={errors.description?.message}
              >
                <Textarea
                  id="settings-description"
                  {...register("description")}
                />
              </FormField>

              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="size-4 rounded border-input accent-primary"
                  {...register("is_active")}
                />
                Negocio activo (acepta nuevas reservas)
              </label>

              <div className="flex justify-end">
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <LoaderCircle className="animate-spin" />
                  ) : null}
                  Guardar cambios
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Plan
                <Badge variant={business.plan === "pro" ? "default" : "secondary"}>
                  {plan.label}
                </Badge>
              </CardTitle>
              <CardDescription>
                El plan se gestiona desde tu cuenta de Turnix.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <Check className="mt-0.5 size-4 text-success" />
                    {feature}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Valoración</CardTitle>
              <CardDescription>Promedio de reseñas.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Star className="size-5 fill-warning text-warning" />
                <span className="text-2xl font-semibold">
                  {business.rating_avg.toFixed(1)}
                </span>
                <span className="text-sm text-muted-foreground">
                  · {business.rating_count}{" "}
                  {business.rating_count === 1 ? "reseña" : "reseñas"}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Horario semanal</CardTitle>
          <CardDescription>
            Se usa para calcular la disponibilidad de las reservas. La edición
            de horarios estará disponible próximamente.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {[...business.schedule.days]
              .sort((a, b) => a.weekday - b.weekday)
              .map((day) => (
                <div key={day.weekday} className="rounded-lg border p-3">
                  <p className="text-sm font-medium">
                    {WEEKDAY_LABELS[day.weekday]}
                  </p>
                  {day.is_closed ? (
                    <p className="text-xs text-muted-foreground">Cerrado</p>
                  ) : (
                    <div className="space-y-0.5">
                      {day.intervals.map((interval) => (
                        <p
                          key={`${interval.open}-${interval.close}`}
                          className="text-xs text-muted-foreground"
                        >
                          {interval.open} – {interval.close}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
