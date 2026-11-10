import { zodResolver } from "@hookform/resolvers/zod";
import { LoaderCircle } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useAuth } from "@/features/auth/auth-context";
import { getApiErrorMessage } from "@/lib/api/client";
import { AuthShell } from "./auth-shell";

const schema = z.object({
  full_name: z
    .string()
    .trim()
    .min(1, "Ingresa tu nombre")
    .max(120, "Máximo 120 caracteres"),
  email: z.string().trim().email("Ingresa un correo válido"),
  phone: z.string().trim().max(30, "Máximo 30 caracteres").optional(),
  password: z
    .string()
    .min(8, "La contraseña debe tener al menos 8 caracteres")
    .max(128, "Máximo 128 caracteres"),
  role: z.enum(["owner", "customer"]),
});

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const { register: signUp } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      full_name: "",
      email: "",
      phone: "",
      password: "",
      role: "owner",
    },
  });

  async function onSubmit(values: FormValues) {
    try {
      const user = await signUp({
        full_name: values.full_name.trim(),
        email: values.email.trim(),
        password: values.password,
        phone: values.phone?.trim() || null,
        role: values.role,
      });
      toast.success("Cuenta creada");
      const destination = user.role === "customer" ? "/cliente" : "/app";
      navigate(destination, { replace: true });
    } catch (error) {
      toast.error("No se pudo crear la cuenta", {
        description: getApiErrorMessage(error),
      });
    }
  }

  return (
    <AuthShell>
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Crea tu cuenta</h2>
        <p className="text-sm text-muted-foreground">
          Empieza a organizar tu negocio con Turnix.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
        <FormField
          label="Nombre completo"
          htmlFor="full_name"
          error={errors.full_name?.message}
          required
        >
          <Input
            id="full_name"
            autoComplete="name"
            placeholder="Ana Gómez"
            {...register("full_name")}
          />
        </FormField>

        <FormField label="Correo" htmlFor="email" error={errors.email?.message} required>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="tu@correo.com"
            {...register("email")}
          />
        </FormField>

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Teléfono" htmlFor="phone" error={errors.phone?.message}>
            <Input
              id="phone"
              autoComplete="tel"
              placeholder="+57 300 000 0000"
              {...register("phone")}
            />
          </FormField>

          <FormField
            label="Tipo de cuenta"
            htmlFor="role"
            error={errors.role?.message}
            required
          >
            <Select id="role" {...register("role")}>
              <option value="owner">Dueño de negocio</option>
              <option value="customer">Cliente</option>
            </Select>
          </FormField>
        </div>

        <FormField
          label="Contraseña"
          htmlFor="password"
          error={errors.password?.message}
          hint="Mínimo 8 caracteres."
          required
        >
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            {...register("password")}
          />
        </FormField>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? <LoaderCircle className="animate-spin" /> : null}
          Crear cuenta
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        ¿Ya tienes cuenta?{" "}
        <Link to="/login" className="font-medium text-primary hover:underline">
          Inicia sesión
        </Link>
      </p>
    </AuthShell>
  );
}
