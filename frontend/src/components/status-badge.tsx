import { Badge } from "@/components/ui/badge";
import { BOOKING_STATUS_LABELS } from "@/lib/format";
import type { BookingStatus } from "@/lib/api/types";

const VARIANTS: Record<
  BookingStatus,
  "default" | "secondary" | "destructive" | "success" | "warning"
> = {
  pending: "warning",
  confirmed: "default",
  cancelled: "destructive",
  completed: "success",
  no_show: "destructive",
};

export function StatusBadge({ status }: { status: BookingStatus }) {
  return <Badge variant={VARIANTS[status]}>{BOOKING_STATUS_LABELS[status]}</Badge>;
}
