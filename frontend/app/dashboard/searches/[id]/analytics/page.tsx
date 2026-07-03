"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useTheme } from "next-themes";
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
import type { Bucket } from "@/lib/types/analytics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

// Single-series charts → one validated hue (the app's primary indigo). Validated
// against both card surfaces via the dataviz palette checker (contrast ≥ 3:1, in band).
function useChartColors() {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return {
    series: dark ? "#6a63e9" : "#5048e5",
    grid: dark ? "hsl(240, 4%, 20%)" : "hsl(240, 6%, 90%)",
    axis: dark ? "hsl(240, 5%, 65%)" : "hsl(240, 4%, 46%)",
    surface: dark ? "hsl(240, 6%, 10%)" : "hsl(0, 0%, 100%)",
    ink: dark ? "hsl(0, 0%, 98%)" : "hsl(240, 10%, 4%)",
  };
}

function fmtUsd(n: number): string {
  return `$${Math.round(n / 1000)}k`;
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function StatTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card>
      <CardContent className="p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-bold tracking-tight">{value}</p>
        {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const { id } = useParams<{ id: string }>();
  const c = useChartColors();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["analytics", id],
    queryFn: () => searchesApi.analytics(id),
    enabled: !!id,
  });

  const a = data?.data;

  const tooltip = {
    contentStyle: {
      background: c.surface,
      border: `1px solid ${c.grid}`,
      borderRadius: 8,
      color: c.ink,
      fontSize: 12,
    },
    cursor: { fill: c.grid, opacity: 0.35 },
    labelStyle: { color: c.ink },
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link
          href={`/dashboard/searches/${id}`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" /> Back to results
        </Link>
        <h1 className="text-2xl font-bold">Insights</h1>
        <p className="text-muted-foreground">Salary, skills, and market signals across this search&apos;s jobs</p>
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-xl border border-destructive/30 p-6 text-center">
          <p className="text-destructive">{parseApiError(error)}</p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {a && a.total_jobs === 0 && (
        <div className="rounded-xl border border-dashed py-16 text-center">
          <p className="font-medium">No jobs to analyze yet</p>
          <p className="mt-2 text-sm text-muted-foreground">Run the search to gather results first.</p>
        </div>
      )}

      {a && a.total_jobs > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="Total jobs" value={String(a.total_jobs)} />
            <StatTile
              label="Median salary"
              value={a.salary.median ? fmtUsd(a.salary.median) : "—"}
              sub={a.salary.average ? `avg ${fmtUsd(a.salary.average)}` : undefined}
            />
            <StatTile
              label="Salary listed"
              value={`${a.salary.listed_count}/${a.total_jobs}`}
              sub={`${a.salary.unlisted_count} not listed`}
            />
            <StatTile label="Sources" value={String(a.by_source.length)} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard title="Salary distribution">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={a.salary.histogram} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
                  <CartesianGrid vertical={false} stroke={c.grid} />
                  <XAxis dataKey="label" tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={{ stroke: c.grid }} />
                  <YAxis allowDecimals={false} tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip {...tooltip} />
                  <Bar dataKey="count" name="Jobs" fill={c.series} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Postings over time">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={a.postings_over_time} margin={{ top: 8, right: 12, bottom: 0, left: -16 }}>
                  <CartesianGrid vertical={false} stroke={c.grid} />
                  <XAxis dataKey="label" tick={{ fill: c.axis, fontSize: 11 }} tickLine={false} axisLine={{ stroke: c.grid }} />
                  <YAxis allowDecimals={false} tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip {...tooltip} cursor={{ stroke: c.axis, strokeWidth: 1 }} />
                  <Line type="monotone" dataKey="count" name="Jobs posted" stroke={c.series} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <ChartCard title="Top skills in demand">
            <ResponsiveContainer width="100%" height={Math.max(200, a.top_skills.length * 28)}>
              <BarChart
                data={a.top_skills}
                layout="vertical"
                margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
              >
                <CartesianGrid horizontal={false} stroke={c.grid} />
                <XAxis type="number" allowDecimals={false} tick={{ fill: c.axis, fontSize: 12 }} tickLine={false} axisLine={{ stroke: c.grid }} />
                <YAxis
                  type="category"
                  dataKey="label"
                  width={140}
                  tick={{ fill: c.axis, fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip {...tooltip} />
                <Bar dataKey="count" name="Jobs" fill={c.series} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard title="Jobs by source">
              <SimpleBar data={a.by_source} colors={c} tooltip={tooltip} />
            </ChartCard>
            <ChartCard title="Jobs by work mode">
              <SimpleBar data={a.by_work_mode} colors={c} tooltip={tooltip} />
            </ChartCard>
          </div>
        </>
      )}
    </div>
  );
}

function SimpleBar({
  data,
  colors,
  tooltip,
}: {
  data: Bucket[];
  colors: ReturnType<typeof useChartColors>;
  tooltip: object;
}) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid vertical={false} stroke={colors.grid} />
        <XAxis dataKey="label" tick={{ fill: colors.axis, fontSize: 12 }} tickLine={false} axisLine={{ stroke: colors.grid }} />
        <YAxis allowDecimals={false} tick={{ fill: colors.axis, fontSize: 12 }} tickLine={false} axisLine={false} />
        <Tooltip {...tooltip} />
        <Bar dataKey="count" name="Jobs" fill={colors.series} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
