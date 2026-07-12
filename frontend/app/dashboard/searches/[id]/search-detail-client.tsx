"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart3,
  ChevronLeft,
  Loader2,
  Pencil,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { resumesApi, searchesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { JobCard, JobCardSkeleton } from "@/components/jobs/job-card";
import { FilterChips, PipelineProgress } from "@/components/search/search-filters";
import { NativeSelect } from "@/components/ui/native-select";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { labelEnum } from "@/lib/utils";
import { POSTED_RESULT_FILTERS } from "@/lib/constants/filters";

export default function SearchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const [onlyNew, setOnlyNew] = useState(searchParams.get("only_new") === "true");
  const [postedDays, setPostedDays] = useState<number>(-1);
  const [page, setPage] = useState(1);
  const [isPolling, setIsPolling] = useState(searchParams.get("running") === "1");
  const [resumeId, setResumeId] = useState<string>("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const resumesQuery = useQuery({
    queryKey: ["resumes"],
    queryFn: () => resumesApi.list(),
  });
  const resumes = resumesQuery.data?.data ?? [];

  const { data: searchRes, isLoading: searchLoading } = useQuery({
    queryKey: ["search", id],
    queryFn: () => searchesApi.get(id),
    enabled: !!id,
  });

  const search = searchRes?.data;

  useEffect(() => {
    if (search?.posted_within_days && postedDays === -1) {
      setPostedDays(search.posted_within_days);
    }
  }, [search, postedDays]);

  const resultsQuery = useQuery({
    queryKey: ["search-results", id, { page, onlyNew, postedDays, resumeId }],
    queryFn: () =>
      searchesApi.results(id, {
        page,
        page_size: 20,
        only_new: onlyNew,
        posted_within_days: postedDays > 0 ? postedDays : undefined,
        resume_id: resumeId || undefined,
      }),
    enabled: !!id,
    refetchInterval: isPolling ? 5000 : false,
  });

  const runStatusQuery = useQuery({
    queryKey: ["run-status", id],
    queryFn: () => searchesApi.runStatus(id),
    enabled: !!id && isPolling,
    refetchInterval: isPolling ? 3000 : false,
  });

  const runMutation = useMutation({
    mutationFn: () => searchesApi.run(id),
    onSuccess: () => {
      toast.success("Pipeline started");
      setIsPolling(true);
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: () => searchesApi.delete(id),
    onSuccess: () => {
      toast.success("Search deleted");
      queryClient.invalidateQueries({ queryKey: ["searches"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.removeQueries({ queryKey: ["search", id] });
      queryClient.removeQueries({ queryKey: ["search-results", id] });
      router.push("/dashboard/searches");
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (active: boolean) => searchesApi.update(id, { is_active: active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["search", id] });
      toast.success("Search updated");
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  // Real completion signal from the backend — not a client-side guess at timing.
  useEffect(() => {
    const status = runStatusQuery.data?.data?.status;
    if (!isPolling || !status || status === "running") return;
    setIsPolling(false);
    queryClient.invalidateQueries({ queryKey: ["search", id] });
    queryClient.invalidateQueries({ queryKey: ["search-results", id] });
    if (status === "failed") {
      toast.error(runStatusQuery.data?.data?.error_detail || "Pipeline run failed");
    }
  }, [isPolling, runStatusQuery.data, id, queryClient]);

  // Safety net only — stops polling if the status endpoint itself never resolves.
  useEffect(() => {
    if (!isPolling) return;
    const timeout = setTimeout(() => setIsPolling(false), 180_000);
    return () => clearTimeout(timeout);
  }, [isPolling]);

  const results = resultsQuery.data?.data ?? [];
  const total = resultsQuery.data?.total ?? 0;
  const totalPages = Math.ceil(total / 20) || 1;

  if (searchLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-32 animate-pulse rounded-xl bg-muted" />
      </div>
    );
  }

  if (!search) {
    return (
      <div className="py-20 text-center">
        <p className="text-destructive">Search not found</p>
        <Link href="/dashboard/searches">
          <Button variant="outline" className="mt-4">
            Back to searches
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <Link
            href="/dashboard/searches"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" /> Back
          </Link>
          <h1 className="text-2xl font-bold">{search.name}</h1>
          <div className="flex flex-wrap gap-2">
            <Badge className="bg-secondary">{search.job_title}</Badge>
            <Badge className="border border-border bg-transparent">{search.field_domain}</Badge>
            {search.work_mode && (
              <Badge className="bg-primary/10 text-primary">{labelEnum(search.work_mode)}</Badge>
            )}
            {!search.is_active && (
              <Badge className="bg-muted text-muted-foreground">Paused</Badge>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending || isPolling}
          >
            {runMutation.isPending || isPolling ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Run now
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => toggleActiveMutation.mutate(!search.is_active)}
          >
            {search.is_active ? "Pause" : "Resume"}
          </Button>
          <Link
            href={`/dashboard/searches/${id}/insights${
              postedDays > 0 ? `?posted_days=${postedDays}` : ""
            }`}
          >
            <Button variant="outline" size="sm" className="gap-2">
              <BarChart3 className="h-4 w-4" /> Insights
            </Button>
          </Link>
          <Link href={`/dashboard/searches/${id}/edit`}>
            <Button variant="outline" size="sm" className="gap-2">
              <Pencil className="h-4 w-4" /> Edit
            </Button>
          </Link>
          <Button
            variant="destructive"
            size="sm"
            className="gap-2"
            aria-label="Delete search"
            onClick={() => setConfirmDelete(true)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <AnimatePresence>
        {isPolling && (
          <motion.div
            key="pipeline-progress"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.35 }}
          >
            <PipelineProgress activeStep={runStatusQuery.data?.data?.current_stage_index ?? 0} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-6">
          <FilterChips
            label="Show:"
            options={[
              { label: "All jobs", value: false },
              { label: "New only", value: true },
            ]}
            value={onlyNew}
            onChange={(v) => {
              setOnlyNew(v);
              setPage(1);
            }}
          />
          <FilterChips
            label="Posted:"
            options={POSTED_RESULT_FILTERS.map((f) => ({ label: f.label, value: f.value }))}
            value={postedDays}
            onChange={(v) => {
              setPostedDays(v);
              setPage(1);
            }}
          />
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 shrink-0 gap-2 self-start lg:self-auto"
          onClick={() => resultsQuery.refetch()}
        >
          <RefreshCw className="h-3.5 w-3.5 shrink-0" /> Refresh
        </Button>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{total}</span> matching jobs
        </p>
        {resumes.length > 0 && (
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            Match against resume:
            <NativeSelect
              value={resumeId}
              onChange={(e) => {
                setResumeId(e.target.value);
                setPage(1);
              }}
            >
              <option value="">None</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.filename}
                </option>
              ))}
            </NativeSelect>
          </label>
        )}
      </div>

      {resultsQuery.isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <JobCardSkeleton key={i} />
          ))}
        </div>
      )}

      {resultsQuery.isError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center">
          <p className="text-destructive">{parseApiError(resultsQuery.error)}</p>
          <Button variant="outline" className="mt-4" onClick={() => resultsQuery.refetch()}>
            Retry
          </Button>
        </div>
      )}

      {!resultsQuery.isLoading && results.length === 0 && (
        <div className="rounded-xl border border-dashed border-border py-16 text-center">
          <p className="font-medium">No jobs match these filters</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {isPolling
              ? "Pipeline is still running — results will appear shortly."
              : "Try running the search or widening the time filter."}
          </p>
          {!isPolling && (
            <Button className="mt-4" onClick={() => runMutation.mutate()}>
              Run search now
            </Button>
          )}
        </div>
      )}

      <div className="space-y-4">
        {results.map((result, i) => (
          <JobCard
            key={result.id}
            result={result}
            index={i}
            resumeId={resumeId || undefined}
            resumeFilename={resumes.find((r) => r.id === resumeId)?.filename}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete this search and all its results?"
        description="This removes the search, its runs, and all matched results. Jobs saved to your tracker are kept."
        confirmLabel="Delete"
        onConfirm={() => deleteMutation.mutate()}
      />
    </div>
  );
}
