import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { FormField } from "@/components/form-field";
import { createBusiness } from "@/lib/api/businesses";
import { getApiErrorMessage } from "@/lib/api/client";
import type { Business } from "@/lib/api/types";
import { TIMEZONES } from "@/lib/timezones";
import { useBusiness } from "./business-context";

const CURRENCIES = ["COP", "USD", "MXN", "EUR", "ARS", "CLP", "PEN"];

const schema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "El nombre es obligatorio")
    .max(120, "Máximo 120 caracteres"),
  slug: z.string().trim().max(60, "Máximo 60 caracteres").optional(),
  timezone: z.string().min(1, "Selecciona una zona horaria"),
  currency: z.string().min(1, "Selecciona una moneda"),
  phone: z.string().trim().max(30, "Máximo 30 caracteres").optional(),
  address: z.string().trim().max(200, "Máximo 200 caracteres").optional(),
  description: z
    .string()
    .trim()
    .max(1000, "Máximo 1000 caracteres")
    .optional(),
});

type FormValues = z.infer<typeof schema>;

interface BusinessFormProps {
  onCreated?: (business: Business) => void;
  submitLabel?: string;
}

function optional(value: string | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export function BusinessForm({
  onCreated,
  submitLabel = "Crear negocio",
}: BusinessFormProps) {
  const queryClient = useQueryClient();
  const { setCurrentBusinessId } = useBusiness();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      slug: "",
      timezone: "America/Bogota",
      currency: "COP",
      phone: "",
      address: "",
      description: "",
    },
  });

  async function onSubmit(values: FormValues) {
    try {
      const business = await createBusiness({
        name: values.name.trim(),
        slug: optional(values.slug),
        timezone: values.timezone,
        currency: values.currency,
        phone: optional(values.phone),
        address: optional(values.address),
        description: optional(values.description),
      });
      await queryClient.invalidateQueries({ queryKey: ["businesses"] });
      setCurrentBusinessId(business.id);
      toast.success("Negocio creado", {
        description: `${business.name} ya está listo para recibir reservas.`,
      });
      onCreated?.(business);
    } catch (error) {
      toast.error("No se pudo crear el negocio", {
        description: getApiErrorMessage(error),
      });
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <FormField label="Nombre del negocio" htmlFor="name" error={errors.name?.message} required>
        <Input id="name" placeholder="Estética Bella" {...register("name")} />
      </FormField>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Slug"
          htmlFor="slug"
          error={errors.slug?.message}
          hint="Opcional. Se genera desde el nombre."
        >
          <Input id="slug" placeholder="estetica-bella" {...register("slug")} />
        </FormField>

        <FormField label="Teléfono" htmlFor="phone" error={errors.phone?.message}>
          <Input id="phone" placeholder="+57 300 000 0000" {...register("phone")} />
        </FormField>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Zona horaria"
          htmlFor="timezone"
          error={errors.timezone?.message}
          required
        >
          <Select id="timezone" {...register("timezone")}>
            {TIMEZONES.map((timezone) => (
              <option key={timezone.value} value={timezone.value}>
                {timezone.label}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField
          label="Moneda"
          htmlFor="currency"
          error={errors.currency?.message}
          required
        >
          <Select id="currency" {...register("currency")}>
            {CURRENCIES.map((currency) => (
              <option key={currency} value={currency}>
                {currency}
              </option>
            ))}
          </Select>
        </FormField>
      </div>

      <FormField label="Dirección" htmlFor="address" error={errors.address?.message}>
        <Input id="address" placeholder="Cra 10 #20-30" {...register("address")} />
      </FormField>

      <FormField
        label="Descripción"
        htmlFor="description"
        error={errors.description?.message}
      >
        <Textarea
          id="description"
          placeholder="Cuéntale a tus clientes qué haces."
          {...register("description")}
        />
      </FormField>

      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? <LoaderCircle className="animate-spin" /> : null}
        {submitLabel}
      </Button>
    </form>
  );
}
