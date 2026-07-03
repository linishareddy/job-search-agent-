"use client";

import type { ParsedSearchIntent } from "@/lib/types/search";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Sparkles } from "lucide-react";
import { formatSalary, labelEnum } from "@/lib/utils";

export function ParsedIntentPreview({ parsed }: { parsed: ParsedSearchIntent }) {
  const confidencePct = Math.round(parsed.confidence * 100);

  return (
    <Card className="border-primary/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4 text-primary" />
          AI understood your search
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Job title" value={parsed.job_title} />
          <Field label="Field / domain" value={parsed.field_domain} />
          <Field label="Search name" value={parsed.name} />
          <Field label="Location" value={parsed.location ?? "United States"} />
          <Field label="Work mode" value={labelEnum(parsed.work_mode)} />
          <Field label="Experience" value={labelEnum(parsed.experience_level)} />
          <Field label="Employment" value={labelEnum(parsed.employment_type)} />
          <Field label="Salary" value={formatSalary(parsed.salary_min, parsed.salary_max)} />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Confidence</span>
            <span className="font-mono font-medium">{confidencePct}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>

        {parsed.ambiguities.length > 0 && (
          <div className="rounded-lg border border-warning/30 bg-warning/5 p-3 text-sm">
            <p className="mb-1 flex items-center gap-1 font-medium text-warning">
              <AlertTriangle className="h-4 w-4" /> AI notes
            </p>
            <ul className="list-inside list-disc space-y-1 text-muted-foreground">
              {parsed.ambiguities.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  );
}
