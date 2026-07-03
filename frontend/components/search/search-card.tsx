"use client";

import Link from "next/link";
import { Clock, Pause, Play } from "lucide-react";
import type { SavedSearch } from "@/lib/types/search";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatRelativeDate, labelEnum } from "@/lib/utils";

export function SearchCard({ search, resultCount }: { search: SavedSearch; resultCount?: number }) {
  return (
    <Link href={`/dashboard/searches/${search.id}`}>
      <Card className="h-full transition-all hover:border-primary/40 hover:shadow-glow">
        <CardContent className="space-y-4 p-5">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold">{search.name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{search.job_title}</p>
            </div>
            <Badge className={search.is_active ? "bg-success/15 text-success" : "bg-muted text-muted-foreground"}>
              {search.is_active ? (
                <span className="flex items-center gap-1"><Play className="h-3 w-3" /> Active</span>
              ) : (
                <span className="flex items-center gap-1"><Pause className="h-3 w-3" /> Paused</span>
              )}
            </Badge>
          </div>
          <p className="line-clamp-2 text-sm text-muted-foreground">{search.field_domain}</p>
          <div className="flex flex-wrap gap-2 text-xs">
            {search.work_mode && (
              <Badge className="bg-secondary text-secondary-foreground">{labelEnum(search.work_mode)}</Badge>
            )}
            {search.posted_within_days && (
              <Badge className="bg-secondary text-secondary-foreground">Last {search.posted_within_days}d</Badge>
            )}
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {search.last_run_at ? `Ran ${formatRelativeDate(search.last_run_at)}` : "Never run"}
            </span>
            {resultCount !== undefined && (
              <span className="font-medium text-foreground">{resultCount} matches</span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
