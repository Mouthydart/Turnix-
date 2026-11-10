import { Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { useBusiness } from "@/features/business/business-context";

export function BusinessSwitcher() {
  const { businesses, currentBusiness, setCurrentBusinessId } = useBusiness();
  const navigate = useNavigate();

  if (!currentBusiness) return null;

  return (
    <div className="flex items-center gap-2">
      <Select
        aria-label="Negocio activo"
        className="h-9 w-44 bg-background font-medium sm:w-56"
        value={currentBusiness.id}
        onChange={(event) => setCurrentBusinessId(event.target.value)}
      >
        {businesses.map((business) => (
          <option key={business.id} value={business.id}>
            {business.name}
          </option>
        ))}
      </Select>
      <Button
        variant="outline"
        size="icon"
        title="Crear otro negocio"
        onClick={() => navigate("/app/new-business")}
      >
        <Plus />
      </Button>
    </div>
  );
}
