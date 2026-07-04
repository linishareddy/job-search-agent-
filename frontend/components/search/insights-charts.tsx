"use client";

import { useTheme } from "next-themes";
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
import type { Bucket, SalaryStats } from "@/lib/types/analytics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function useChartColors() {
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

export function fmtUsd(n: number): string {
  return `$${Math.round(n / 1000)}k`;
}

export function makeTooltip(colors: ReturnType<typeof useChartColors>) {
  return {
    contentStyle: {
      background: colors.surface,
      border: `1px solid ${colors.grid}`,
      borderRadius: 8,
      color: colors.ink,
      fontSize: 12,
    },
    cursor: { fill: colors.grid, opacity: 0.35 },
    labelStyle: { color: colors.ink },
  };
}

export function StatTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg border border-border bg-card/60 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-0.5 text-lg font-semibold tracking-tight">{value}</p>
      {sub && <p className="mt-0.5 text-[11px] text-muted-foreground">{sub}</p>}
    </div>
  );
}

export function ChartCard({
  title,
  children,
  className,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("border-border/80 bg-card/60", className)}>
      <CardHeader className="pb-2 pt-4">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent className="pb-4">{children}</CardContent>
    </Card>
  );
}

export function SimpleBar({
  data,
  colors,
  tooltip,
  height = 160,
}: {
  data: Bucket[];
  colors: ReturnType<typeof useChartColors>;
  tooltip: object;
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
        <CartesianGrid vertical={false} stroke={colors.grid} />
        <XAxis
          dataKey="label"
          tick={{ fill: colors.axis, fontSize: 10 }}
          tickLine={false}
          axisLine={{ stroke: colors.grid }}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: colors.axis, fontSize: 10 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip {...tooltip} />
        <Bar dataKey="count" name="Jobs" fill={colors.series} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function MarketChartsSection({
  salary,
  topSkills,
  bySource,
  byWorkMode,
  postingsOverTime,
  jobCount,
}: {
  salary: SalaryStats;
  topSkills: Bucket[];
  bySource: Bucket[];
  byWorkMode: Bucket[];
  postingsOverTime: Bucket[];
  jobCount: number;
}) {
  const c = useChartColors();
  const tooltip = makeTooltip(c);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        <StatTile label="Total jobs" value={String(jobCount)} />
        <StatTile
          label="Median salary"
          value={salary.median ? fmtUsd(salary.median) : "—"}
          sub={salary.average ? `avg ${fmtUsd(salary.average)}` : undefined}
        />
        <StatTile
          label="Salary listed"
          value={`${salary.listed_count}/${jobCount}`}
          sub={`${salary.unlisted_count} not listed`}
        />
        <StatTile label="Sources" value={String(bySource.length)} />
      </div>

      <ChartCard title="Salary distribution">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={salary.histogram} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
            <CartesianGrid vertical={false} stroke={c.grid} />
            <XAxis
              dataKey="label"
              tick={{ fill: c.axis, fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: c.grid }}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: c.axis, fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip {...tooltip} />
            <Bar dataKey="count" name="Jobs" fill={c.series} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Postings over time">
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={postingsOverTime} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <CartesianGrid vertical={false} stroke={c.grid} />
            <XAxis
              dataKey="label"
              tick={{ fill: c.axis, fontSize: 9 }}
              tickLine={false}
              axisLine={{ stroke: c.grid }}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: c.axis, fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip {...tooltip} cursor={{ stroke: c.axis, strokeWidth: 1 }} />
            <Line
              type="monotone"
              dataKey="count"
              name="Jobs posted"
              stroke={c.series}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Top skills">
        <ResponsiveContainer width="100%" height={Math.max(160, Math.min(topSkills.length, 8) * 24)}>
          <BarChart
            data={topSkills.slice(0, 8)}
            layout="vertical"
            margin={{ top: 0, right: 8, bottom: 0, left: 0 }}
          >
            <CartesianGrid horizontal={false} stroke={c.grid} />
            <XAxis
              type="number"
              allowDecimals={false}
              tick={{ fill: c.axis, fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: c.grid }}
            />
            <YAxis
              type="category"
              dataKey="label"
              width={88}
              tick={{ fill: c.axis, fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip {...tooltip} />
            <Bar dataKey="count" name="Jobs" fill={c.series} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="space-y-3">
        <ChartCard title="By source">
          <SimpleBar data={bySource} colors={c} tooltip={tooltip} />
        </ChartCard>
        <ChartCard title="By work mode">
          <SimpleBar data={byWorkMode} colors={c} tooltip={tooltip} />
        </ChartCard>
      </div>
    </div>
  );
}
