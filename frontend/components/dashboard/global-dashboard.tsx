"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
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
import { analyticsApi, healthApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Badge } from "@/components/ui/badge";
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

function FunnelStep({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-1 flex-col items-center rounded-xl border border-border/60 bg-card/40 px-4 py-5 text-center">
      <p className="text-2xl font-bold">{value}</p>
      <p className="mt-1 text-sm text-muted-foreground">{label}</p>
    </div>
  );
}

export function GlobalDashboard() {
  const c = useChartColors();
  const tooltip = makeTooltip(c);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => analyticsApi.overview(),
  });

  const { data: sourcesRes } = useQuery({
    queryKey: ["health", "sources"],
    queryFn: () => healthApi.sources(),
  });

  const a = data?.data;
  const hasJobs = a && a.jobs.unique > 0;

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Your job hunt at a glance — across all searches</p>
      </div>

      {sourcesRes?.data && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(sourcesRes.data).map(([source, stats]) => (
            <Badge key={source} className="bg-secondary px-3 py-1 text-secondary-foreground capitalize">
              {source}: {stats.jobs_last_24h} jobs / 24h
            </Badge>
          ))}
        </div>
      )}

      {isLoading && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-28 rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-64 rounded-xl" />
          <div className="grid gap-6 lg:grid-cols-2">
            <Skeleton className="h-72 rounded-xl" />
            <Skeleton className="h-72 rounded-xl" />
          </div>
        </div>
      )}

      {isError && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
          <p className="text-destructive">{parseApiError(error)}</p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {a && !hasJobs && (
        <div className="rounded-2xl border border-dashed border-border py-24 text-center">
          <p className="text-lg font-medium">No data yet</p>
          <p className="mt-2 text-muted-foreground">
            Create a search and run it to populate your dashboard.
          </p>
          <Link href="/dashboard/searches">
            <Button className="mt-6">Go to Searches</Button>
          </Link>
        </div>
      )}

      {a && hasJobs && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Unique jobs" value={String(a.jobs.unique)} sub={`${a.jobs.total_matches} total matches`} />
            <KpiCard
              label="Median salary"
              value={a.salary.median ? fmtUsd(a.salary.median) : "—"}
              sub={a.salary.average ? `avg ${fmtUsd(a.salary.average)}` : undefined}
            />
            <KpiCard label="Active searches" value={String(a.searches.active)} sub={`${a.searches.paused} paused`} />
            <KpiCard label="New jobs (7d)" value={String(a.jobs.new_7d)} sub={`${a.jobs.new_24h} in last 24h`} />
          </div>

          <Card className="border-border/80 bg-card/60">
            <CardHeader>
              <CardTitle className="text-base">Application pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <FunnelStep label="Saved" value={a.tracker.saved} />
                <FunnelStep label="Applied" value={a.tracker.applied} />
                <FunnelStep label="Interviewing" value={a.tracker.interviewing} />
                <FunnelStep label="Offer" value={a.tracker.offer} />
                <FunnelStep label="Rejected" value={a.tracker.rejected} />
              </div>
            </CardContent>
          </Card>

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

          {a.by_search.length > 0 && (
            <Card className="border-border/80 bg-card/60">
              <CardHeader>
                <CardTitle className="text-base">Breakdown by search</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="divide-y divide-border/60">
                  {a.by_search.map((s) => (
                    <Link
                      key={s.search_id}
                      href={`/dashboard/searches/${s.search_id}`}
                      className="flex items-center justify-between gap-4 py-4 transition-colors first:pt-0 last:pb-0 hover:text-primary"
                    >
                      <span className="min-w-0 truncate font-medium">{s.name}</span>
                      <span className="shrink-0 text-sm text-muted-foreground">
                        {s.job_count} jobs
                        {s.new_count > 0 && ` · ${s.new_count} new`}
                        {s.median_salary && ` · ${fmtUsd(s.median_salary)} median`}
                      </span>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
