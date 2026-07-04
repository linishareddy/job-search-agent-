"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Radar } from "lucide-react";
import { toast } from "sonner";
import { searchesApi, healthApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SearchCard } from "@/components/search/search-card";
import { Badge } from "@/components/ui/badge";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

type PendingDelete =
  | { type: "one"; id: string; name: string }
  | { type: "bulk"; ids: string[]; label: string }
  | { type: "paused"; count: number };

const DELETE_DESCRIPTION =
  "This removes the search, its runs, and all matched results. Jobs saved to your tracker are kept.";

export default function SearchesPage() {
  const queryClient = useQueryClient();
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(null);

  const { data: searchesRes, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["searches"],
    queryFn: () => searchesApi.list(),
  });

  const { data: sourcesRes } = useQuery({
    queryKey: ["health", "sources"],
    queryFn: () => healthApi.sources(),
  });

  const searches = searchesRes?.data ?? [];
  const pausedCount = useMemo(() => searches.filter((s) => !s.is_active).length, [searches]);

  const invalidateSearchQueries = (ids?: string[]) => {
    queryClient.invalidateQueries({ queryKey: ["searches"] });
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
    queryClient.invalidateQueries({ queryKey: ["analytics", "overview"] });
    if (ids) {
      ids.forEach((id) => {
        queryClient.removeQueries({ queryKey: ["search", id] });
        queryClient.removeQueries({ queryKey: ["search-results", id] });
        queryClient.removeQueries({ queryKey: ["search-results-count", id] });
      });
    }
  };

  const deleteMutation = useMutation({
    mutationFn: async (pending: PendingDelete) => {
      if (pending.type === "one") {
        await searchesApi.delete(pending.id);
        return { ids: [pending.id], count: 1 };
      }
      if (pending.type === "paused") {
        const res = await searchesApi.bulkDelete({ only_paused: true });
        return { ids: [] as string[], count: res.data?.deleted ?? 0 };
      }
      const res = await searchesApi.bulkDelete({ ids: pending.ids });
      return { ids: pending.ids, count: res.data?.deleted ?? pending.ids.length };
    },
    onSuccess: (result) => {
      toast.success(`Deleted ${result.count} search${result.count === 1 ? "" : "es"}`);
      invalidateSearchQueries(result.ids.length > 0 ? result.ids : undefined);
      setSelectedIds(new Set());
      setSelectionMode(false);
      setPendingDelete(null);
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const toggleSelected = (id: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const confirmTitle = pendingDelete
    ? pendingDelete.type === "one"
      ? `Delete "${pendingDelete.name}"?`
      : pendingDelete.type === "paused"
        ? `Delete ${pendingDelete.count} paused search${pendingDelete.count === 1 ? "" : "es"}?`
        : pendingDelete.label
    : "";

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Searches</h1>
          <p className="text-muted-foreground">AI job agents running on a schedule</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {searches.length > 0 && (
            <>
              {selectionMode ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectionMode(false);
                      setSelectedIds(new Set());
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={selectedIds.size === 0}
                    onClick={() =>
                      setPendingDelete({
                        type: "bulk",
                        ids: Array.from(selectedIds),
                        label: `Delete ${selectedIds.size} selected search${selectedIds.size === 1 ? "" : "es"}?`,
                      })
                    }
                  >
                    Delete selected ({selectedIds.size})
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="outline" size="sm" onClick={() => setSelectionMode(true)}>
                    Select
                  </Button>
                  {pausedCount > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setPendingDelete({ type: "paused", count: pausedCount })
                      }
                    >
                      Delete paused ({pausedCount})
                    </Button>
                  )}
                </>
              )}
            </>
          )}
          <Link href="/dashboard/new">
            <Button className="gap-2">
              <Plus className="h-4 w-4" /> New search
            </Button>
          </Link>
        </div>
      </div>

      {sourcesRes?.data && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(sourcesRes.data).map(([source, stats]) => (
            <Badge key={source} className="bg-secondary text-secondary-foreground capitalize">
              {source}: {stats.jobs_last_24h} jobs / 24h
            </Badge>
          ))}
        </div>
      )}

      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-44 rounded-xl" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center">
          <p className="font-medium text-destructive">Could not load searches</p>
          <p className="mt-1 text-sm text-muted-foreground">{(error as Error).message}</p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {!isLoading && !isError && searches.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center">
          <Radar className="mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="text-lg font-semibold">No searches yet</h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Describe your ideal job in one sentence and let the AI agent hunt for you.
          </p>
          <Link href="/dashboard/new" className="mt-6">
            <Button>Create your first search</Button>
          </Link>
        </div>
      )}

      {!isLoading && searches.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {searches.map((search) => (
            <SearchCardWithCount
              key={search.id}
              search={search}
              selectable={selectionMode}
              selected={selectedIds.has(search.id)}
              onSelectedChange={(selected) => toggleSelected(search.id, selected)}
              onDelete={
                selectionMode
                  ? undefined
                  : () => setPendingDelete({ type: "one", id: search.id, name: search.name })
              }
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!pendingDelete}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title={confirmTitle}
        description={DELETE_DESCRIPTION}
        confirmLabel="Delete"
        onConfirm={() => pendingDelete && deleteMutation.mutate(pendingDelete)}
      />
    </div>
  );
}

function SearchCardWithCount({
  search,
  onDelete,
  selectable,
  selected,
  onSelectedChange,
}: {
  search: import("@/lib/types/search").SavedSearch;
  onDelete?: () => void;
  selectable?: boolean;
  selected?: boolean;
  onSelectedChange?: (selected: boolean) => void;
}) {
  const { data } = useQuery({
    queryKey: ["search-results-count", search.id],
    queryFn: () => searchesApi.results(search.id, { page: 1, page_size: 1 }),
  });
  return (
    <SearchCard
      search={search}
      resultCount={data?.total}
      onDelete={onDelete}
      selectable={selectable}
      selected={selected}
      onSelectedChange={onSelectedChange}
    />
  );
}
