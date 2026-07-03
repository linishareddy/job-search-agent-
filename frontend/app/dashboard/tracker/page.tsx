"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, KanbanSquare, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { applicationsApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import type { ApplicationStatus, JobApplication } from "@/lib/types/application";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

const COLUMNS: { status: ApplicationStatus; label: string }[] = [
  { status: "saved", label: "Saved" },
  { status: "applied", label: "Applied" },
  { status: "interviewing", label: "Interviewing" },
  { status: "offer", label: "Offer" },
  { status: "rejected", label: "Rejected" },
];

const COLUMN_ACCENT: Record<ApplicationStatus, string> = {
  saved: "text-muted-foreground",
  applied: "text-primary",
  interviewing: "text-warning",
  offer: "text-success",
  rejected: "text-destructive",
};

function ApplicationCard({ app }: { app: JobApplication }) {
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (data: { status?: ApplicationStatus; notes?: string }) =>
      applicationsApi.update(app.id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
    onError: (err) => toast.error(parseApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: () => applicationsApi.delete(app.id),
    onSuccess: () => {
      toast.success("Removed from tracker");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  return (
    <Card>
      <CardContent className="space-y-2 p-3">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-medium leading-snug">{app.job.title}</p>
          <button
            onClick={() => {
              if (confirm(`Remove ${app.job.title} from tracker?`)) deleteMutation.mutate();
            }}
            aria-label="Remove"
            className="text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-muted-foreground">{app.job.company_name}</p>

        <select
          value={app.status}
          onChange={(e) => updateMutation.mutate({ status: e.target.value as ApplicationStatus })}
          className="w-full rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {COLUMNS.map((c) => (
            <option key={c.status} value={c.status}>
              {c.label}
            </option>
          ))}
        </select>

        <textarea
          defaultValue={app.notes ?? ""}
          placeholder="Notes…"
          onBlur={(e) => {
            if (e.target.value !== (app.notes ?? "")) updateMutation.mutate({ notes: e.target.value });
          }}
          className="h-14 w-full resize-none rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />

        <a
          href={app.job.apply_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          Open posting <ExternalLink className="h-3 w-3" />
        </a>
      </CardContent>
    </Card>
  );
}

export default function TrackerPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
  });

  const applications = data?.data ?? [];
  const byStatus = (status: ApplicationStatus) => applications.filter((a) => a.status === status);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Application tracker</h1>
        <p className="text-muted-foreground">
          Track jobs from Saved through Offer. Add jobs with &quot;Save to tracker&quot; on any result.
        </p>
      </div>

      {isError && (
        <div className="rounded-xl border border-destructive/30 p-6 text-center">
          <p className="text-destructive">{parseApiError(error)}</p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {!isError && !isLoading && applications.length === 0 && (
        <div className="flex flex-col items-center rounded-xl border border-dashed py-16 text-center">
          <KanbanSquare className="mb-4 h-10 w-10 text-muted-foreground" />
          <p className="font-medium">No tracked applications yet</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Open a search, then click &quot;Save to tracker&quot; on a job to add it here.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {COLUMNS.map((col) => (
          <div key={col.status} className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className={`text-sm font-semibold ${COLUMN_ACCENT[col.status]}`}>{col.label}</h2>
              <span className="text-xs text-muted-foreground">{byStatus(col.status).length}</span>
            </div>
            {isLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : (
              <div className="space-y-2">
                {byStatus(col.status).map((app) => (
                  <ApplicationCard key={app.id} app={app} />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
