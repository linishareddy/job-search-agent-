"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const STEPS = [
  "Expand field",
  "Fetch sources",
  "Normalize",
  "Filter noise",
  "Dedup exact",
  "Embed jobs",
  "Dedup semantic",
  "Pre-score",
  "AI enrich",
  "Save results",
  "Notify",
];

export function PipelineProgress({ activeStep = 0 }: { activeStep?: number }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4" role="status" aria-live="polite">
      <p className="mb-3 text-sm font-medium">Pipeline running…</p>
      <div className="flex flex-wrap gap-2">
        {STEPS.map((step, i) => (
          <span
            key={step}
            className={cn(
              "rounded-full px-2.5 py-1 text-xs transition-colors",
              i <= activeStep
                ? "bg-primary/15 text-primary"
                : "bg-muted text-muted-foreground"
            )}
          >
            {i + 1}. {step}
          </span>
        ))}
      </div>
    </div>
  );
}

export function FilterChips<T extends string | number | boolean>({
  options,
  value,
  onChange,
  label,
  "aria-label": ariaLabel,
}: {
  options: { label: string; value: T }[];
  value: T;
  onChange: (v: T) => void;
  label?: string;
  "aria-label"?: string;
}) {
  return (
    <div
      role="group"
      aria-label={ariaLabel ?? label}
      className="flex flex-wrap items-center gap-x-2 gap-y-1.5"
    >
      {label && (
        <span className="w-14 shrink-0 text-sm leading-none text-muted-foreground">{label}</span>
      )}
      <div className="flex flex-wrap items-center gap-1.5">
        {options.map((opt) => (
          <Button
            key={String(opt.value)}
            type="button"
            size="sm"
            className="h-8"
            variant={value === opt.value ? "default" : "outline"}
            aria-pressed={value === opt.value}
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
