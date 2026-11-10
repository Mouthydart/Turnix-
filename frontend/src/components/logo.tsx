import { useId } from "react";

import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  variant?: "default" | "light";
  showWordmark?: boolean;
}

export function LogoMark({ className }: { className?: string }) {
  const rawId = useId();
  const gradientId = `turnix-${rawId.replace(/[:]/g, "")}`;

  return (
    <svg
      viewBox="0 0 40 40"
      role="img"
      aria-label="Turnix"
      className={cn("size-9 shrink-0 drop-shadow-sm", className)}
    >
      <defs>
        <linearGradient
          id={gradientId}
          x1="4"
          y1="2"
          x2="38"
          y2="40"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#6366f1" />
          <stop offset="0.5" stopColor="#8b5cf6" />
          <stop offset="1" stopColor="#ec4899" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="12" fill={`url(#${gradientId})`} />
      <path
        d="M12.5 14.5h15a2 2 0 0 1 2 2v11a3 3 0 0 1-3 3h-13a3 3 0 0 1-3-3v-11a2 2 0 0 1 2-2Z"
        stroke="white"
        strokeWidth="2.2"
        strokeLinejoin="round"
        fill="none"
      />
      <path
        d="M10.5 19.5h19"
        stroke="white"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <path
        d="M16 11v4.5M24 11v4.5"
        stroke="white"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <path
        d="M15.5 24.5l2.8 2.8 6-6"
        stroke="white"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Logo({
  className,
  variant = "default",
  showWordmark = true,
}: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <LogoMark />
      {showWordmark ? (
        <span
          className={cn(
            "text-lg font-semibold tracking-tight",
            variant === "light" ? "text-white" : "text-brand-gradient",
          )}
        >
          Turnix
        </span>
      ) : null}
    </div>
  );
}
