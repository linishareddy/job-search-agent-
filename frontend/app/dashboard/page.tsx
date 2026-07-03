"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Plus, Radar } from "lucide-react";
import { searchesApi, healthApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SearchCard } from "@/components/search/search-card";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  const { data: searchesRes, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["searches"],
    queryFn: () => searchesApi.list(),
  });

  const { data: sourcesRes } = useQuery({
    queryKey: ["health", "sources"],
    queryFn: () => healthApi.sources(),
  });

  const searches = searchesRes?.data ?? [];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Your searches</h1>
          <p className="text-muted-foreground">AI job agents running on a schedule</p>
        </div>
        <Link href="/dashboard/new">
          <Button className="gap-2">
            <Plus className="h-4 w-4" /> New search
          </Button>
        </Link>
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
            <SearchCardWithCount key={search.id} search={search} />
          ))}
        </div>
      )}
    </div>
  );
}

function SearchCardWithCount({ search }: { search: import("@/lib/types/search").SavedSearch }) {
  const { data } = useQuery({
    queryKey: ["search-results-count", search.id],
    queryFn: () => searchesApi.results(search.id, { page: 1, page_size: 1 }),
  });
  return <SearchCard search={search} resultCount={data?.total} />;
}
