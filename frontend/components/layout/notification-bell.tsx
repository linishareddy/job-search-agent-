"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { notificationsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function NotificationBell() {
  const { data } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => notificationsApi.list(true),
    refetchInterval: 30_000,
    // Explicit: don't keep polling while the tab is hidden/unfocused.
    refetchIntervalInBackground: false,
  });

  const unread = data?.data?.length ?? 0;

  return (
    <Link href="/dashboard/notifications">
      <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
        <Bell className="h-4 w-4" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </Button>
    </Link>
  );
}
