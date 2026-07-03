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
    <div className="rounded-xl border border-border bg-card p-4">
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
}: {
  options: { label: string; value: T }[];
  value: T;
  onChange: (v: T) => void;
  label?: string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {label && <span className="text-sm text-muted-foreground">{label}</span>}
      {options.map((opt) => (
        <Button
          key={String(opt.value)}
          type="button"
          size="sm"
          variant={value === opt.value ? "default" : "outline"}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </Button>
      ))}
    </div>
  );
}
