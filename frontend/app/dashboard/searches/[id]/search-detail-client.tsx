"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ChevronLeft,
  Loader2,
  Pencil,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { searchesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { JobCard, JobCardSkeleton } from "@/components/jobs/job-card";
import { FilterChips, PipelineProgress } from "@/components/search/search-filters";
import { labelEnum } from "@/lib/utils";

const POSTED_FILTERS = [
  { label: "All", value: -1 },
  { label: "1d", value: 1 },
  { label: "7d", value: 7 },
  { label: "30d", value: 30 },
  { label: "90d", value: 90 },
] as const;

export default function SearchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const [onlyNew, setOnlyNew] = useState(searchParams.get("only_new") === "true");
  const [postedDays, setPostedDays] = useState<number>(-1);
  const [page, setPage] = useState(1);
  const [pipelineStep, setPipelineStep] = useState(0);
  const [isPolling, setIsPolling] = useState(searchParams.get("running") === "1");

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
    queryKey: ["search-results", id, { page, onlyNew, postedDays }],
    queryFn: () =>
      searchesApi.results(id, {
        page,
        page_size: 20,
        only_new: onlyNew,
        posted_within_days: postedDays > 0 ? postedDays : undefined,
      }),
    enabled: !!id,
    refetchInterval: isPolling ? 5000 : false,
  });

  const runMutation = useMutation({
    mutationFn: () => searchesApi.run(id),
    onSuccess: () => {
      toast.success("Pipeline started");
      setIsPolling(true);
      setPipelineStep(0);
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: () => searchesApi.delete(id),
    onSuccess: () => {
      toast.success("Search deleted");
      queryClient.invalidateQueries({ queryKey: ["searches"] });
      router.push("/dashboard");
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

  useEffect(() => {
    if (!isPolling) return;
    const stepTimer = setInterval(() => {
      setPipelineStep((s) => Math.min(s + 1, 10));
    }, 4000);
    return () => clearInterval(stepTimer);
  }, [isPolling]);

  useEffect(() => {
    if (!isPolling) return;
    const total = resultsQuery.data?.total ?? 0;
    if (total > 0 || pipelineStep >= 10) {
      setIsPolling(false);
      queryClient.invalidateQueries({ queryKey: ["search", id] });
    }
    const timeout = setTimeout(() => setIsPolling(false), 180_000);
    return () => clearTimeout(timeout);
  }, [isPolling, resultsQuery.data?.total, pipelineStep, id, queryClient]);

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
        <Link href="/dashboard">
          <Button variant="outline" className="mt-4">
            Back to dashboard
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
            href="/dashboard"
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
          <Link href={`/dashboard/searches/${id}/edit`}>
            <Button variant="outline" size="sm" className="gap-2">
              <Pencil className="h-4 w-4" /> Edit
            </Button>
          </Link>
          <Button
            variant="destructive"
            size="sm"
            className="gap-2"
            onClick={() => {
              if (confirm("Delete this search and all its results?")) deleteMutation.mutate();
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isPolling && <PipelineProgress activeStep={pipelineStep} />}

      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4 sm:flex-row sm:items-center sm:justify-between">
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
          options={POSTED_FILTERS.map((f) => ({ label: f.label, value: f.value }))}
          value={postedDays}
          onChange={(v) => {
            setPostedDays(v);
            setPage(1);
          }}
        />
        <Button
          variant="ghost"
          size="sm"
          className="gap-2"
          onClick={() => resultsQuery.refetch()}
        >
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
      </div>

      <p className="text-sm text-muted-foreground">
        <span className="font-medium text-foreground">{total}</span> matching jobs
      </p>

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
          <JobCard key={result.id} result={result} index={i} />
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
    </div>
  );
}
