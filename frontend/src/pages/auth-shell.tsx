import { CalendarCheck2, ChartLine, Clock, Star, Users } from "lucide-react";
import type { ReactNode } from "react";

import { Logo } from "@/components/logo";

const HIGHLIGHTS = [
  {
    icon: CalendarCheck2,
    title: "Agenda sin choques",
    description: "Disponibilidad por servicio y empleado.",
  },
  {
    icon: Users,
    title: "Equipo organizado",
    description: "Cada empleado ve su propia agenda.",
  },
  {
    icon: ChartLine,
    title: "Decisiones con datos",
    description: "Reservas, ingresos y servicios top.",
  },
];

const MOCK_AGENDA = [
  {
    time: "09:00",
    name: "Laura Martínez",
    service: "Corte + barba",
    dot: "bg-amber-300",
    status: "Confirmada",
    statusClass: "bg-white/15 text-white",
  },
  {
    time: "10:30",
    name: "Carlos Ruiz",
    service: "Manicure",
    dot: "bg-emerald-300",
    status: "Completada",
    statusClass: "bg-emerald-400/20 text-emerald-100",
  },
  {
    time: "12:00",
    name: "Ana Gómez",
    service: "Coloración",
    dot: "bg-sky-300",
    status: "Pendiente",
    statusClass: "bg-amber-400/20 text-amber-100",
  },
];

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="bg-brand-gradient relative hidden overflow-hidden p-10 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="bg-grid-white pointer-events-none absolute inset-0 opacity-40 [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]" />
        <div className="pointer-events-none absolute -right-24 -top-24 size-80 rounded-full bg-white/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-20 size-96 rounded-full bg-fuchsia-300/30 blur-3xl" />
        <div className="animate-float pointer-events-none absolute right-16 top-1/3 size-32 rounded-full bg-cyan-300/25 blur-2xl" />
        <div className="animate-float-slow pointer-events-none absolute bottom-40 right-24 size-20 rounded-2xl border border-white/20 bg-white/10 backdrop-blur-sm" />

        <div className="relative">
          <Logo variant="light" />
        </div>

        <div className="relative space-y-8 py-10">
          <div className="space-y-4">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/25 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <Star className="size-3.5 fill-amber-300 text-amber-300" />
              Agenda inteligente
            </span>
            <h1 className="max-w-lg text-4xl font-semibold leading-tight tracking-tight">
              Tu agenda, tus reservas y tu equipo,{" "}
              <span className="relative whitespace-nowrap">
                en un solo lugar
                <span className="absolute inset-x-0 -bottom-1 h-1 rounded-full bg-white/40" />
              </span>
              .
            </h1>
            <p className="max-w-md text-white/75">
              Gestiona la operación diaria de tu negocio y ofrece una
              experiencia de reserva impecable a tus clientes.
            </p>
          </div>

          <div className="max-w-md rounded-2xl border border-white/20 bg-white/10 p-4 shadow-2xl shadow-indigo-950/30 backdrop-blur-md">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex size-7 items-center justify-center rounded-lg bg-white/15">
                  <Clock className="size-3.5" />
                </span>
                <p className="text-sm font-medium">Agenda de hoy</p>
              </div>
              <span className="rounded-full bg-white/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white/80">
                3 citas
              </span>
            </div>
            <div className="space-y-2">
              {MOCK_AGENDA.map((item) => (
                <div
                  key={item.time}
                  className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2"
                >
                  <span className="w-10 text-xs font-semibold text-white/70">
                    {item.time}
                  </span>
                  <span className={`size-2 rounded-full ${item.dot}`} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{item.name}</p>
                    <p className="truncate text-xs text-white/60">
                      {item.service}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${item.statusClass}`}
                  >
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <ul className="grid max-w-md gap-3 sm:grid-cols-3">
            {HIGHLIGHTS.map((item) => (
              <li
                key={item.title}
                className="rounded-xl border border-white/15 bg-white/5 p-3 backdrop-blur-sm"
              >
                <item.icon className="mb-1.5 size-4 text-white/90" />
                <p className="text-xs font-semibold">{item.title}</p>
                <p className="mt-0.5 text-[11px] leading-snug text-white/65">
                  {item.description}
                </p>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-sm text-white/55">
          © {new Date().getFullYear()} Turnix
        </p>
      </div>

      <div className="relative flex items-center justify-center overflow-hidden p-6 sm:p-10">
        <div className="bg-app pointer-events-none absolute inset-0" />
        <div className="pointer-events-none absolute -left-24 top-10 size-72 rounded-full bg-primary/10 blur-3xl" />
        <div className="pointer-events-none absolute -right-20 bottom-0 size-72 rounded-full bg-fuchsia-400/10 blur-3xl" />
        <div className="relative w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>
          <div className="relative overflow-hidden rounded-2xl border border-border/70 bg-card/80 p-6 shadow-xl shadow-primary/5 backdrop-blur-xl sm:p-8">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-brand-gradient" />
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
