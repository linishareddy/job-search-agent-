"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  FileText,
  KanbanSquare,
  LayoutDashboard,
  LogOut,
  Radar,
  Search,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { NotificationBell } from "@/components/layout/notification-bell";
import { MobileNavDrawer } from "@/components/layout/mobile-nav-drawer";
import { useQuery } from "@tanstack/react-query";
import { healthApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/searches", label: "Searches", icon: Search },
  { href: "/dashboard/resume", label: "Resume", icon: FileText },
  { href: "/dashboard/tracker", label: "Tracker", icon: KanbanSquare },
  { href: "/dashboard/auto-apply", label: "Auto-apply", icon: Zap },
  { href: "/dashboard/notifications", label: "Notifications", icon: Bell },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => healthApi.check(),
    refetchInterval: 60_000,
  });

  const apiOk = health?.data?.status === "running" && health?.data?.database === "ok";

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const isShortcutKey = e.key.toLowerCase() === "k" && (e.metaKey || e.ctrlKey);
      if (!isShortcutKey) return;
      const target = e.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA"].includes(target.tagName)) return;
      e.preventDefault();
      router.push("/dashboard/new");
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [router]);

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 flex-col border-r border-border bg-card/50 md:flex">
        <Link href="/dashboard" className="flex h-16 items-center gap-2 border-b border-border px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15">
            <Radar className="h-4 w-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold">Job Radar</p>
            <p className="text-xs text-muted-foreground">AI search agent</p>
          </div>
        </Link>
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
        <div className="space-y-3 border-t border-border p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className={cn("h-2 w-2 rounded-full", apiOk ? "bg-success" : "bg-destructive")} />
            API {apiOk ? "connected" : "offline"}
          </div>
          {user && (
            <div className="flex items-center justify-between gap-2">
              <p className="truncate text-xs text-muted-foreground" title={user.email}>
                {user.email}
              </p>
              <button
                onClick={handleLogout}
                aria-label="Log out"
                className="shrink-0 text-muted-foreground hover:text-foreground"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-border px-4 md:px-8">
          <div className="flex items-center gap-2 md:hidden">
            <MobileNavDrawer open={mobileNavOpen} onOpenChange={setMobileNavOpen} nav={NAV} />
            <Link href="/dashboard" className="flex items-center gap-2">
              <Radar className="h-5 w-5 text-primary" />
              <span className="font-semibold">Job Radar</span>
            </Link>
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
