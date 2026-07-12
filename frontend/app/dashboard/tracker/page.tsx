"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { ExternalLink, GripVertical, KanbanSquare, Sparkles, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { applicationsApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import type { ApplicationStatus, JobApplication } from "@/lib/types/application";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { NativeSelect } from "@/components/ui/native-select";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { AutoApplyDetailsDialog } from "@/components/tracker/auto-apply-details-dialog";

const COLUMNS: { status: ApplicationStatus; label: string }[] = [
  { status: "saved", label: "Saved" },
  { status: "ready_to_apply", label: "Ready to apply" },
  { status: "applied", label: "Applied" },
  { status: "interviewing", label: "Interviewing" },
  { status: "offer", label: "Offer" },
  { status: "rejected", label: "Rejected" },
];

const COLUMN_ACCENT: Record<ApplicationStatus, string> = {
  saved: "text-muted-foreground",
  ready_to_apply: "text-blue-500 dark:text-blue-400",
  applied: "text-primary",
  interviewing: "text-warning",
  offer: "text-success",
  rejected: "text-destructive",
};

function ApplicationCard({
  app,
  onStatusChange,
  onRequestDelete,
  onViewDetails,
  dragging,
}: {
  app: JobApplication;
  onStatusChange: (status: ApplicationStatus) => void;
  onRequestDelete: () => void;
  onViewDetails: () => void;
  dragging?: boolean;
}) {
  const queryClient = useQueryClient();
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: app.id,
    data: { status: app.status },
  });

  const notesMutation = useMutation({
    mutationFn: (notes: string) => applicationsApi.update(app.id, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      toast.success("Note saved");
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  return (
    <Card
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform) }}
      className={cn("touch-none", (isDragging || dragging) && "opacity-40")}
    >
      <CardContent className="space-y-2 p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-1.5">
            <button
              {...attributes}
              {...listeners}
              aria-label={`Drag to move ${app.job.title}`}
              className="mt-0.5 shrink-0 cursor-grab touch-none text-muted-foreground hover:text-foreground active:cursor-grabbing"
            >
              <GripVertical className="h-4 w-4" />
            </button>
            <p className="text-sm font-medium leading-snug">{app.job.title}</p>
          </div>
          <button
            onClick={onRequestDelete}
            aria-label={`Remove ${app.job.title}`}
            className="shrink-0 text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-muted-foreground">{app.job.company_name}</p>

        {app.auto_prepared && (
          <div className="flex items-center gap-1.5">
            <Badge className="h-5 gap-1 bg-blue-500/15 px-2 text-[10px] text-blue-600 dark:text-blue-400">
              <Sparkles className="h-2.5 w-2.5" />
              Auto-prepared
            </Badge>
            {app.match_score != null && (
              <Badge className="h-5 bg-primary/15 px-2 text-[10px] text-primary">
                {Math.round(app.match_score * 100)}% match
              </Badge>
            )}
          </div>
        )}

        <NativeSelect
          value={app.status}
          onChange={(e) => onStatusChange(e.target.value as ApplicationStatus)}
          className="w-full text-xs"
          aria-label={`Status for ${app.job.title}`}
        >
          {COLUMNS.map((c) => (
            <option key={c.status} value={c.status}>
              {c.label}
            </option>
          ))}
        </NativeSelect>

        <textarea
          defaultValue={app.notes ?? ""}
          placeholder="Notes…"
          onBlur={(e) => {
            if (e.target.value !== (app.notes ?? "")) notesMutation.mutate(e.target.value);
          }}
          className="h-14 w-full resize-none rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />

        <div className="flex items-center justify-between">
          <a
            href={app.job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            Open posting <ExternalLink className="h-3 w-3" />
          </a>
          {(app.cover_letter || app.tailored_resume) && (
            <button onClick={onViewDetails} className="text-xs text-muted-foreground hover:text-foreground hover:underline">
              View details
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function Column({
  status,
  label,
  count,
  isDropTarget,
  children,
}: {
  status: ApplicationStatus;
  label: string;
  count: number;
  isDropTarget: boolean;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "space-y-3 rounded-xl p-2 transition-colors",
        isOver && isDropTarget ? "bg-primary/5 ring-2 ring-primary/40" : "ring-2 ring-transparent"
      )}
    >
      <div className="flex items-center justify-between px-1">
        <h2 className={`text-sm font-semibold ${COLUMN_ACCENT[status]}`}>{label}</h2>
        <span className="text-xs text-muted-foreground">{count}</span>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

export default function TrackerPage() {
  const queryClient = useQueryClient();
  const [activeApp, setActiveApp] = useState<JobApplication | null>(null);
  const [pendingDelete, setPendingDelete] = useState<JobApplication | null>(null);
  const [detailsApp, setDetailsApp] = useState<JobApplication | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
  });

  const applications = data?.data ?? [];
  const byStatus = (status: ApplicationStatus) => applications.filter((a) => a.status === status);

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ApplicationStatus }) =>
      applicationsApi.update(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
    onError: (err) => toast.error(parseApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => applicationsApi.delete(id),
    onSuccess: () => {
      toast.success("Removed from tracker");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  // Keyboard sensor keeps the board operable without a pointer; the per-card
  // native <select> (kept alongside drag) is the fully-accessible fallback.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor)
  );

  function handleDragStart(event: DragStartEvent) {
    const app = applications.find((a) => a.id === event.active.id);
    setActiveApp(app ?? null);
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveApp(null);
    if (!over) return;
    const newStatus = over.id as ApplicationStatus;
    const app = applications.find((a) => a.id === active.id);
    if (app && app.status !== newStatus) {
      statusMutation.mutate({ id: app.id, status: newStatus });
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Application tracker</h1>
        <p className="text-muted-foreground">
          Drag a card between columns, or use its status menu. Add jobs with &quot;Save to tracker&quot; on any result.
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

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6">
          {COLUMNS.map((col) => (
            <Skeleton key={col.status} className="h-24 w-full" />
          ))}
        </div>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6">
            {COLUMNS.map((col) => (
              <Column
                key={col.status}
                status={col.status}
                label={col.label}
                count={byStatus(col.status).length}
                isDropTarget={!!activeApp && activeApp.status !== col.status}
              >
                {byStatus(col.status).map((app) => (
                  <ApplicationCard
                    key={app.id}
                    app={app}
                    dragging={activeApp?.id === app.id}
                    onStatusChange={(status) => statusMutation.mutate({ id: app.id, status })}
                    onRequestDelete={() => setPendingDelete(app)}
                    onViewDetails={() => setDetailsApp(app)}
                  />
                ))}
              </Column>
            ))}
          </div>

          <DragOverlay>
            {activeApp && (
              <Card className="rotate-2 shadow-glow">
                <CardContent className="space-y-1 p-3">
                  <p className="text-sm font-medium leading-snug">{activeApp.job.title}</p>
                  <p className="text-xs text-muted-foreground">{activeApp.job.company_name}</p>
                </CardContent>
              </Card>
            )}
          </DragOverlay>
        </DndContext>
      )}

      <ConfirmDialog
        open={!!pendingDelete}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title={`Remove ${pendingDelete?.job.title} from tracker?`}
        confirmLabel="Remove"
        onConfirm={() => pendingDelete && deleteMutation.mutate(pendingDelete.id)}
      />

      <AutoApplyDetailsDialog
        open={!!detailsApp}
        onOpenChange={(open) => !open && setDetailsApp(null)}
        app={detailsApp}
      />
    </div>
  );
}
