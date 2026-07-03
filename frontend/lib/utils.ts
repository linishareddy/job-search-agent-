import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSalary(min?: number | null, max?: number | null): string {
  if (!min && !max) return "Not listed";
  const fmt = (n: number) =>
    n >= 1000 ? `$${Math.round(n / 1000)}k` : `$${n.toLocaleString()}`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `${fmt(min)}+`;
  if (max) return `Up to ${fmt(max)}`;
  return "Not listed";
}

export function formatRelativeDate(iso?: string | null): string {
  if (!iso) return "Unknown";
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days <= 0) return "Today";
  if (days === 1) return "1 day ago";
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function scoreLabel(score: number): string {
  return (score * 10).toFixed(1);
}

export function scoreColor(score: number): string {
  const s = score * 10;
  if (s >= 7) return "text-success";
  if (s >= 5) return "text-warning";
  return "text-muted-foreground";
}

const SOURCE_COLORS: Record<string, string> = {
  adzuna: "bg-blue-500/15 text-blue-600 dark:text-blue-400",
  jooble: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  remotive: "bg-purple-500/15 text-purple-600 dark:text-purple-400",
  greenhouse: "bg-teal-500/15 text-teal-600 dark:text-teal-400",
  lever: "bg-orange-500/15 text-orange-600 dark:text-orange-400",
  ashby: "bg-pink-500/15 text-pink-600 dark:text-pink-400",
};

export function sourceBadgeClass(source: string): string {
  return SOURCE_COLORS[source.toLowerCase()] ?? "bg-muted text-muted-foreground";
}

export function labelEnum(value?: string | null): string {
  if (!value || value === "any") return "Any";
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
