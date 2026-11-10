import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, Pencil, Plus, Scissors, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { EmptyState } from "@/components/empty-state";
import { FormField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
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
import {
  createService,
  deleteService,
  listServices,
  updateService,
} from "@/lib/api/services";
import type { Service } from "@/lib/api/types";
import { formatDuration, formatMoney } from "@/lib/format";

const schema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "El nombre es obligatorio")
    .max(120, "Máximo 120 caracteres"),
  description: z.string().trim().max(1000, "Máximo 1000 caracteres").optional(),
  duration_minutes: z
    .number({ invalid_type_error: "Ingresa un número" })
    .int("Debe ser un número entero")
    .min(1, "Mínimo 1 minuto")
    .max(1440, "Máximo 24 horas"),
  buffer_minutes: z
    .number({ invalid_type_error: "Ingresa un número" })
    .int("Debe ser un número entero")
    .min(0, "No puede ser negativo")
    .max(1440, "Máximo 24 horas"),
  price: z
    .number({ invalid_type_error: "Ingresa un número" })
    .min(0, "No puede ser negativo"),
  is_active: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

const DEFAULTS: FormValues = {
  name: "",
  description: "",
  duration_minutes: 60,
  buffer_minutes: 0,
  price: 0,
  is_active: true,
};

export function ServicesPage() {
  const business = useCurrentBusiness();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Service | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Service | null>(null);

  const servicesQuery = useQuery({
    queryKey: ["services", business.id],
    queryFn: () => listServices(business.id),
  });

  const deleteMutation = useMutation({
    mutationFn: (service: Service) => deleteService(business.id, service.id),
    onSuccess: (_data, service) => {
      toast.success("Servicio eliminado", { description: service.name });
      setDeleteTarget(null);
      void queryClient.invalidateQueries({
        queryKey: ["services", business.id],
      });
    },
    onError: (error) => {
      toast.error("No se pudo eliminar el servicio", {
        description: getApiErrorMessage(error),
      });
    },
  });

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(service: Service) {
    setEditing(service);
    setFormOpen(true);
  }

  const services = servicesQuery.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Servicios"
        description="Define qué ofreces, cuánto dura y cuánto cuesta."
        actions={
          <Button onClick={openCreate}>
            <Plus /> Nuevo servicio
          </Button>
        }
      />

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">
            {services.length}{" "}
            {services.length === 1 ? "servicio" : "servicios"}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {servicesQuery.isError ? (
            <div className="flex flex-col items-center gap-3 p-10 text-center">
              <p className="font-medium">No se pudieron cargar los servicios.</p>
              <p className="text-sm text-muted-foreground">
                {getApiErrorMessage(servicesQuery.error)}
              </p>
              <Button
                variant="outline"
                onClick={() => void servicesQuery.refetch()}
              >
                Reintentar
              </Button>
            </div>
          ) : servicesQuery.isLoading ? (
            <div className="space-y-3 p-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} className="h-12 rounded-lg" />
              ))}
            </div>
          ) : services.length === 0 ? (
            <EmptyState
              icon={Scissors}
              title="Aún no tienes servicios"
              description="Crea tu primer servicio para empezar a recibir reservas."
              action={
                <Button onClick={openCreate}>
                  <Plus /> Crear servicio
                </Button>
              }
              className="m-6 border-dashed"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Servicio</TableHead>
                  <TableHead>Duración</TableHead>
                  <TableHead>Precio</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {services.map((service) => (
                  <TableRow key={service.id}>
                    <TableCell>
                      <div className="space-y-0.5">
                        <p className="font-medium">{service.name}</p>
                        {service.description ? (
                          <p className="line-clamp-1 max-w-md text-xs text-muted-foreground">
                            {service.description}
                          </p>
                        ) : null}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-0.5">
                        <p>{formatDuration(service.duration_minutes)}</p>
                        {service.buffer_minutes > 0 ? (
                          <p className="text-xs text-muted-foreground">
                            + {service.buffer_minutes} min de margen
                          </p>
                        ) : null}
                      </div>
                    </TableCell>
                    <TableCell>
                      {formatMoney(service.price, business.currency)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={service.is_active ? "success" : "secondary"}>
                        {service.is_active ? "Activo" : "Inactivo"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Editar"
                          onClick={() => openEdit(service)}
                        >
                          <Pencil />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Eliminar"
                          className="text-destructive hover:text-destructive"
                          onClick={() => setDeleteTarget(service)}
                        >
                          <Trash2 />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <ServiceFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        service={editing}
      />

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => {
          if (!open && !deleteMutation.isPending) setDeleteTarget(null);
        }}
        title="Eliminar servicio"
        description={deleteTarget?.name ?? ""}
        note="Las reservas existentes conservarán su información histórica."
        confirmLabel="Eliminar"
        isLoading={deleteMutation.isPending}
        onConfirm={() => {
          if (deleteTarget) deleteMutation.mutate(deleteTarget);
        }}
      />
    </div>
  );
}

function ServiceFormDialog({
  open,
  onOpenChange,
  service,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  service: Service | null;
}) {
  const business = useCurrentBusiness();
  const queryClient = useQueryClient();
  const isEdit = Boolean(service);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: DEFAULTS,
  });

  useEffect(() => {
    if (!open) return;
    reset(
      service
        ? {
            name: service.name,
            description: service.description ?? "",
            duration_minutes: service.duration_minutes,
            buffer_minutes: service.buffer_minutes,
            price: Number(service.price),
            is_active: service.is_active,
          }
        : DEFAULTS,
    );
  }, [open, service, reset]);

  async function onSubmit(values: FormValues) {
    const payload = {
      name: values.name.trim(),
      description: values.description?.trim() || null,
      duration_minutes: values.duration_minutes,
      buffer_minutes: values.buffer_minutes,
      price: values.price,
      is_active: values.is_active,
    };

    try {
      if (service) {
        await updateService(business.id, service.id, payload);
        toast.success("Servicio actualizado");
      } else {
        await createService(business.id, payload);
        toast.success("Servicio creado");
      }
      await queryClient.invalidateQueries({
        queryKey: ["services", business.id],
      });
      onOpenChange(false);
    } catch (error) {
      toast.error(
        isEdit ? "No se pudo actualizar el servicio" : "No se pudo crear el servicio",
        { description: getApiErrorMessage(error) },
      );
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Editar servicio" : "Nuevo servicio"}
      description={
        isEdit
          ? "Actualiza los datos del servicio."
          : "Define el servicio que podrán reservar tus clientes."
      }
      footer={
        <>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="service-form"
            disabled={isSubmitting}
          >
            {isSubmitting ? <LoaderCircle className="animate-spin" /> : null}
            {isEdit ? "Guardar cambios" : "Crear servicio"}
          </Button>
        </>
      }
    >
      <form
        id="service-form"
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-4"
      >
        <FormField
          label="Nombre"
          htmlFor="service-name"
          error={errors.name?.message}
          required
        >
          <Input
            id="service-name"
            placeholder="Corte de cabello"
            {...register("name")}
          />
        </FormField>

        <FormField
          label="Descripción"
          htmlFor="service-description"
          error={errors.description?.message}
        >
          <Textarea
            id="service-description"
            placeholder="Detalles del servicio (opcional)."
            {...register("description")}
          />
        </FormField>

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            label="Duración (min)"
            htmlFor="service-duration"
            error={errors.duration_minutes?.message}
            required
          >
            <Input
              id="service-duration"
              type="number"
              min={1}
              {...register("duration_minutes", { valueAsNumber: true })}
            />
          </FormField>

          <FormField
            label="Margen (min)"
            htmlFor="service-buffer"
            error={errors.buffer_minutes?.message}
            hint="Tiempo de limpieza o preparación."
          >
            <Input
              id="service-buffer"
              type="number"
              min={0}
              {...register("buffer_minutes", { valueAsNumber: true })}
            />
          </FormField>
        </div>

        <FormField
          label={`Precio (${business.currency})`}
          htmlFor="service-price"
          error={errors.price?.message}
          required
        >
          <Input
            id="service-price"
            type="number"
            min={0}
            step="0.01"
            {...register("price", { valueAsNumber: true })}
          />
        </FormField>

        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="checkbox"
            className="size-4 rounded border-input accent-primary"
            {...register("is_active")}
          />
          Servicio activo (visible para reservas)
        </label>
      </form>
    </Dialog>
  );
}
