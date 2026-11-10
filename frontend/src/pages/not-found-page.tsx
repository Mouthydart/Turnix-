import { Link } from "react-router-dom";

import { buttonVariants } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      <p className="text-5xl font-semibold tracking-tight">404</p>
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">Página no encontrada</h1>
        <p className="text-sm text-muted-foreground">
          La ruta que buscas no existe o fue movida.
        </p>
      </div>
      <Link to="/app" className={buttonVariants()}>
        Volver al panel
      </Link>
    </div>
  );
}
