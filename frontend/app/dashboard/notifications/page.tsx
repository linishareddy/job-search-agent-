"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { notificationsApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatRelativeDate } from "@/lib/utils";

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => notificationsApi.list(false),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      toast.success("Notification dismissed");
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const notifications = data?.data ?? [];

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Notifications</h1>
        <p className="text-muted-foreground">Alerts when high-relevance new jobs are found</p>
      </div>

      {isLoading && <div className="h-24 animate-pulse rounded-xl bg-muted" />}

      {isError && (
        <div className="rounded-xl border border-destructive/30 p-6 text-center">
          <p className="text-destructive">{parseApiError(error)}</p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {!isLoading && notifications.length === 0 && (
        <div className="flex flex-col items-center rounded-xl border border-dashed py-16 text-center">
          <Bell className="mb-4 h-10 w-10 text-muted-foreground" />
          <p className="font-medium">No notifications yet</p>
          <p className="mt-2 text-sm text-muted-foreground">
            You&apos;ll be alerted when new jobs score 7/10 or higher.
          </p>
        </div>
      )}

      <div className="space-y-2">
        {notifications.map((n) => (
          <Card key={n.id} className={!n.is_read ? "border-primary/30" : ""}>
            <CardContent className="flex items-start justify-between gap-4 p-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {!n.is_read && <Badge className="bg-primary/15 text-primary">Unread</Badge>}
                  <span className="text-xs text-muted-foreground">
                    {formatRelativeDate(n.created_at)}
                  </span>
                </div>
                <p className="text-sm font-medium">{n.message}</p>
                <p className="text-xs text-muted-foreground">{n.new_job_count} new job(s)</p>
                {n.search_id && (
                  <Link
                    href={`/dashboard/searches/${n.search_id}?only_new=true`}
                    className="text-sm text-primary hover:underline"
                    onClick={() => !n.is_read && markReadMutation.mutate(n.id)}
                  >
                    View new matches →
                  </Link>
                )}
              </div>
              <div className="flex gap-1">
                {!n.is_read && (
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Mark read"
                    onClick={() => markReadMutation.mutate(n.id)}
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Dismiss"
                  onClick={() => deleteMutation.mutate(n.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
