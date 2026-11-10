import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, Pencil, Plus, Star, Trash2, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
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
import { listServices } from "@/lib/api/services";
import {
  createStaff,
  deleteStaff,
  listStaff,
  updateStaff,
} from "@/lib/api/staff";
import type { Staff } from "@/lib/api/types";

const schema = z.object({
  display_name: z
    .string()
    .trim()
    .min(1, "El nombre es obligatorio")
    .max(120, "Máximo 120 caracteres"),
  title: z.string().trim().max(120, "Máximo 120 caracteres").optional(),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, "Usa un color hexadecimal válido"),
  services: z.array(z.string()),
  is_active: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

const DEFAULTS: FormValues = {
  display_name: "",
  title: "",
  color: "#6366f1",
  services: [],
  is_active: true,
};

export function StaffPage() {
  const business = useCurrentBusiness();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Staff | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Staff | null>(null);

  const staffQuery = useQuery({
    queryKey: ["staff", business.id],
    queryFn: () => listStaff(business.id),
  });

  const servicesQuery = useQuery({
    queryKey: ["services", business.id],
    queryFn: () => listServices(business.id),
  });

  const serviceNames = useMemo(
    () => new Map(servicesQuery.data?.map((item) => [item.id, item.name])),
    [servicesQuery.data],
  );

  const deleteMutation = useMutation({
    mutationFn: (member: Staff) => deleteStaff(business.id, member.id),
    onSuccess: (_data, member) => {
      toast.success("Empleado eliminado", {
        description: member.display_name,
      });
      setDeleteTarget(null);
      void queryClient.invalidateQueries({ queryKey: ["staff", business.id] });
    },
    onError: (error) => {
      toast.error("No se pudo eliminar el empleado", {
        description: getApiErrorMessage(error),
      });
    },
  });

  const staff = staffQuery.data ?? [];

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(member: Staff) {
    setEditing(member);
    setFormOpen(true);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Empleados"
        description="Gestiona tu equipo y los servicios que puede prestar cada uno."
        actions={
          <Button onClick={openCreate}>
            <Plus /> Nuevo empleado
          </Button>
        }
      />

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">
            {staff.length} {staff.length === 1 ? "empleado" : "empleados"}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {staffQuery.isError ? (
            <div className="flex flex-col items-center gap-3 p-10 text-center">
              <p className="font-medium">No se pudieron cargar los empleados.</p>
              <p className="text-sm text-muted-foreground">
                {getApiErrorMessage(staffQuery.error)}
              </p>
              <Button
                variant="outline"
                onClick={() => void staffQuery.refetch()}
              >
                Reintentar
              </Button>
            </div>
          ) : staffQuery.isLoading ? (
            <div className="space-y-3 p-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} className="h-12 rounded-lg" />
              ))}
            </div>
          ) : staff.length === 0 ? (
            <EmptyState
              icon={Users}
              title="Aún no tienes empleados"
              description="Agrega a tu equipo para asignarles servicios y horarios."
              action={
                <Button onClick={openCreate}>
                  <Plus /> Agregar empleado
                </Button>
              }
              className="m-6 border-dashed"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Empleado</TableHead>
                  <TableHead>Servicios</TableHead>
                  <TableHead>Valoración</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {staff.map((member) => {
                  const names = member.services
                    .map((serviceId) => serviceNames.get(serviceId))
                    .filter((name): name is string => Boolean(name));
                  const visible = names.slice(0, 2);
                  const rest = names.length - visible.length;

                  return (
                    <TableRow key={member.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <span
                            className="size-9 shrink-0 rounded-full border"
                            style={{
                              backgroundColor: member.color ?? "#6366f1",
                            }}
                          />
                          <div className="space-y-0.5">
                            <p className="font-medium">{member.display_name}</p>
                            {member.title ? (
                              <p className="text-xs text-muted-foreground">
                                {member.title}
                              </p>
                            ) : null}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {names.length === 0 ? (
                          <span className="text-xs text-muted-foreground">
                            Sin servicios
                          </span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {visible.map((name) => (
                              <Badge key={name} variant="secondary">
                                {name}
                              </Badge>
                            ))}
                            {rest > 0 ? (
                              <Badge variant="outline">+{rest}</Badge>
                            ) : null}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {member.rating_count > 0 ? (
                          <div className="flex items-center gap-1">
                            <Star className="size-4 fill-warning text-warning" />
                            <span className="font-medium">
                              {member.rating_avg.toFixed(1)}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              ({member.rating_count})
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={member.is_active ? "success" : "secondary"}>
                          {member.is_active ? "Activo" : "Inactivo"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Editar"
                            onClick={() => openEdit(member)}
                          >
                            <Pencil />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Eliminar"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setDeleteTarget(member)}
                          >
                            <Trash2 />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <StaffFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        member={editing}
        services={servicesQuery.data ?? []}
      />

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => {
          if (!open && !deleteMutation.isPending) setDeleteTarget(null);
        }}
        title="Eliminar empleado"
        description={deleteTarget?.display_name ?? ""}
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

function StaffFormDialog({
  open,
  onOpenChange,
  member,
  services,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  member: Staff | null;
  services: { id: string; name: string }[];
}) {
  const business = useCurrentBusiness();
  const queryClient = useQueryClient();
  const isEdit = Boolean(member);

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
      member
        ? {
            display_name: member.display_name,
            title: member.title ?? "",
            color: member.color ?? "#6366f1",
            services: member.services,
            is_active: member.is_active,
          }
        : DEFAULTS,
    );
  }, [open, member, reset]);

  async function onSubmit(values: FormValues) {
    const payload = {
      display_name: values.display_name.trim(),
      title: values.title?.trim() || null,
      color: values.color,
      services: values.services,
      is_active: values.is_active,
    };

    try {
      if (member) {
        await updateStaff(business.id, member.id, payload);
        toast.success("Empleado actualizado");
      } else {
        await createStaff(business.id, payload);
        toast.success("Empleado agregado");
      }
      await queryClient.invalidateQueries({ queryKey: ["staff", business.id] });
      onOpenChange(false);
    } catch (error) {
      toast.error(
        isEdit ? "No se pudo actualizar el empleado" : "No se pudo agregar el empleado",
        { description: getApiErrorMessage(error) },
      );
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Editar empleado" : "Nuevo empleado"}
      description={
        isEdit
          ? "Actualiza los datos del miembro del equipo."
          : "Agrega un miembro del equipo y asígnale servicios."
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
          <Button type="submit" form="staff-form" disabled={isSubmitting}>
            {isSubmitting ? <LoaderCircle className="animate-spin" /> : null}
            {isEdit ? "Guardar cambios" : "Agregar empleado"}
          </Button>
        </>
      }
    >
      <form
        id="staff-form"
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-4"
      >
        <div className="grid gap-4 sm:grid-cols-[1fr_auto]">
          <FormField
            label="Nombre visible"
            htmlFor="staff-name"
            error={errors.display_name?.message}
            required
          >
            <Input
              id="staff-name"
              placeholder="Laura Martínez"
              {...register("display_name")}
            />
          </FormField>

          <FormField
            label="Color"
            htmlFor="staff-color"
            error={errors.color?.message}
          >
            <Input
              id="staff-color"
              type="color"
              className="h-9 w-16 cursor-pointer p-1"
              {...register("color")}
            />
          </FormField>
        </div>

        <FormField
          label="Cargo"
          htmlFor="staff-title"
          error={errors.title?.message}
        >
          <Input
            id="staff-title"
            placeholder="Estilista senior"
            {...register("title")}
          />
        </FormField>

        <div className="space-y-2">
          <p className="text-sm font-medium">Servicios que puede prestar</p>
          {services.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              Primero crea servicios para poder asignarlos.
            </p>
          ) : (
            <div className="grid gap-2 rounded-lg border p-3 sm:grid-cols-2">
              {services.map((service) => (
                <label
                  key={service.id}
                  className="flex cursor-pointer items-center gap-2 text-sm"
                >
                  <input
                    type="checkbox"
                    value={service.id}
                    className="size-4 rounded border-input accent-primary"
                    {...register("services")}
                  />
                  {service.name}
                </label>
              ))}
            </div>
          )}
        </div>

        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="checkbox"
            className="size-4 rounded border-input accent-primary"
            {...register("is_active")}
          />
          Empleado activo (recibe reservas)
        </label>
      </form>
    </Dialog>
  );
}
