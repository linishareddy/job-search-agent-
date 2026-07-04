"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { searchesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  fmtUsd,
  makeTooltip,
  SimpleBar,
  useChartColors,
} from "@/components/search/insights-charts";

function KpiCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card className="border-border/80 bg-card/60">
      <CardContent className="p-6">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-2 text-3xl font-bold tracking-tight">{value}</p>
        {sub && <p className="mt-1 text-sm text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export function SearchInsightsDashboard({ searchId }: { searchId: string }) {
  const c = useChartColors();
  const tooltip = makeTooltip(c);
  const searchParams = useSearchParams();
  const postedParam = searchParams.get("posted_days");
  const postedWithinDays = postedParam ? Number(postedParam) : undefined;

  const searchQuery = useQuery({
    queryKey: ["search", searchId],
    queryFn: () => searchesApi.get(searchId),
    enabled: !!searchId,
  });

  const effectivePostedDays =
    postedWithinDays && postedWithinDays > 0
      ? postedWithinDays
      : searchQuery.data?.data?.posted_within_days ?? undefined;

  const analyticsQuery = useQuery({
    queryKey: ["analytics", searchId, effectivePostedDays ?? "all"],
    queryFn: () => searchesApi.analytics(searchId, effectivePostedDays),
    enabled: !!searchId,
  });

  const search = searchQuery.data?.data;
  const a = analyticsQuery.data?.data;
  const isLoading = searchQuery.isLoading || analyticsQuery.isLoading;
  const isError = analyticsQuery.isError;
  const hasJobs = a && a.total_jobs > 0;

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div className="space-y-2">
        <Link
          href={`/dashboard/searches/${searchId}`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" /> Back to results
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">Insights</h1>
        <p className="text-muted-foreground">
          {search?.name
            ? `Market signals for “${search.name}”`
            : "Salary, skills, and market signals for this search"}
          {effectivePostedDays
            ? ` · posted within ${effectivePostedDays} days`
            : " · all stored jobs"}
        </p>
      </div>

      {isLoading && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-28 rounded-xl" />
            ))}
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Skeleton className="h-72 rounded-xl" />
            <Skeleton className="h-72 rounded-xl" />
          </div>
        </div>
      )}

      {isError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
          <p className="text-destructive">{parseApiError(analyticsQuery.error)}</p>
          <Button variant="outline" className="mt-4" onClick={() => analyticsQuery.refetch()}>
            Retry
          </Button>
        </div>
      )}

      {a && !hasJobs && (
        <div className="rounded-2xl border border-dashed border-border py-24 text-center">
          <p className="text-lg font-medium">No jobs to analyze yet</p>
          <p className="mt-2 text-muted-foreground">Run the search to gather results first.</p>
          <Link href={`/dashboard/searches/${searchId}`}>
            <Button className="mt-6">Back to search</Button>
          </Link>
        </div>
      )}

      {a && hasJobs && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Total jobs" value={String(a.total_jobs)} />
            <KpiCard
              label="Median salary"
              value={a.salary.median ? fmtUsd(a.salary.median) : "—"}
              sub={a.salary.average ? `avg ${fmtUsd(a.salary.average)}` : undefined}
            />
            <KpiCard
              label="Salary listed"
              value={`${a.salary.listed_count}/${a.total_jobs}`}
              sub={`${a.salary.unlisted_count} not listed`}
            />
            <KpiCard label="Sources" value={String(a.by_source.length)} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="border-border/80 bg-card/60">
              <CardHeader>
                <CardTitle className="text-base">Salary distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={a.salary.histogram} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                    <CartesianGrid vertical={false} stroke={c.grid} />
                    <XAxis dataKey="label" tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={{ stroke: c.grid }} />
                    <YAxis allowDecimals={false} tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip {...tooltip} />
                    <Bar dataKey="count" name="Jobs" fill={c.series} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="border-border/80 bg-card/60">
              <CardHeader>
                <CardTitle className="text-base">Postings over time</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={a.postings_over_time} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
                    <CartesianGrid vertical={false} stroke={c.grid} />
                    <XAxis dataKey="label" tick={{ fill: c.axis, fontSize: 11 }} tickLine={false} axisLine={{ stroke: c.grid }} />
                    <YAxis allowDecimals={false} tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip {...tooltip} cursor={{ stroke: c.axis, strokeWidth: 1 }} />
                    <Line type="monotone" dataKey="count" name="Jobs posted" stroke={c.series} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card className="border-border/80 bg-card/60">
            <CardHeader>
              <CardTitle className="text-base">Top skills in demand</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={Math.max(240, Math.min(a.top_skills.length, 12) * 32)}>
                <BarChart
                  data={a.top_skills.slice(0, 12)}
                  layout="vertical"
                  margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
                >
                  <CartesianGrid horizontal={false} stroke={c.grid} />
                  <XAxis type="number" allowDecimals={false} tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={{ stroke: c.grid }} />
                  <YAxis type="category" dataKey="label" width={140} tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip {...tooltip} />
                  <Bar dataKey="count" name="Jobs" fill={c.series} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="border-border/80 bg-card/60">
              <CardHeader>
                <CardTitle className="text-base">Jobs by source</CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleBar data={a.by_source} colors={c} tooltip={tooltip} height={220} />
              </CardContent>
            </Card>
            <Card className="border-border/80 bg-card/60">
              <CardHeader>
                <CardTitle className="text-base">Jobs by work mode</CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleBar data={a.by_work_mode} colors={c} tooltip={tooltip} height={220} />
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
