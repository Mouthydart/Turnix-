import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "success" | "warning" | "destructive";
}

const TONES: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default: "bg-brand-gradient text-white shadow-lg shadow-primary/25",
  success:
    "bg-gradient-to-br from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/20",
  warning:
    "bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-lg shadow-orange-500/20",
  destructive:
    "bg-gradient-to-br from-rose-500 to-red-500 text-white shadow-lg shadow-rose-500/20",
};

export function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  tone = "default",
}: StatCardProps) {
  return (
    <Card className="relative overflow-hidden transition-shadow hover:shadow-md">
      <div className="pointer-events-none absolute -right-8 -top-10 size-24 rounded-full bg-primary/10 blur-2xl" />
      <CardContent className="relative flex items-start gap-4 p-5">
        <span
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-xl",
            TONES[tone],
          )}
        >
          <Icon className="size-5" />
        </span>
        <div className="min-w-0 space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className="truncate text-2xl font-semibold tracking-tight">
            {value}
          </p>
          {hint ? (
            <p className="text-xs text-muted-foreground">{hint}</p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
