import { useNavigate } from "react-router-dom";

import { PageHeader } from "@/components/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { BusinessForm } from "@/features/business/business-form";

export function NewBusinessPage() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Nuevo negocio"
        description="Crea otro negocio dentro de tu cuenta de Turnix."
      />

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Datos del negocio</CardTitle>
          <CardDescription>
            Podrás ajustar el horario y los servicios después de crearlo.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BusinessForm
            submitLabel="Crear negocio"
            onCreated={() => navigate("/app")}
          />
        </CardContent>
      </Card>
    </div>
  );
}
