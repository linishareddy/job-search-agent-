"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  Building2,
  LayoutDashboard,
  Plus,
  Radar,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { NotificationBell } from "@/components/layout/notification-bell";
import { useQuery } from "@tanstack/react-query";
import { healthApi } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Searches", icon: LayoutDashboard },
  { href: "/dashboard/new", label: "New Search", icon: Plus },
  { href: "/dashboard/companies", label: "Companies", icon: Building2 },
  { href: "/dashboard/notifications", label: "Notifications", icon: Bell },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => healthApi.check(),
    refetchInterval: 60_000,
  });

  const apiOk = health?.data?.status === "running" && health?.data?.database === "ok";

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 flex-col border-r border-border bg-card/50 md:flex">
        <div className="flex h-16 items-center gap-2 border-b border-border px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15">
            <Radar className="h-4 w-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold">Job Radar</p>
            <p className="text-xs text-muted-foreground">AI search agent</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-4">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-border p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className={cn("h-2 w-2 rounded-full", apiOk ? "bg-success" : "bg-destructive")} />
            API {apiOk ? "connected" : "offline"}
          </div>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-border px-4 md:px-8">
          <div className="flex items-center gap-3 md:hidden">
            <Radar className="h-5 w-5 text-primary" />
            <span className="font-semibold">Job Radar</span>
          </div>
          <div className="hidden md:block">
            <p className="text-sm text-muted-foreground">Find roles across 6 job sources with AI matching</p>
          </div>
          <div className="flex items-center gap-1">
            <Link href="/dashboard/new">
              <button className="mr-2 flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground md:hidden">
                <Search className="h-4 w-4" />
                New
              </button>
            </Link>
            <NotificationBell />
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
