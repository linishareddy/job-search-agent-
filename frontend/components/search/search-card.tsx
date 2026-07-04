"use client";

import Link from "next/link";
import { Check, Clock, Pause, Play, Trash2 } from "lucide-react";
import type { SavedSearch } from "@/lib/types/search";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, formatRelativeDate, labelEnum } from "@/lib/utils";

type SearchCardProps = {
  search: SavedSearch;
  resultCount?: number;
  onDelete?: () => void;
  selectable?: boolean;
  selected?: boolean;
  onSelectedChange?: (selected: boolean) => void;
};

export function SearchCard({
  search,
  resultCount,
  onDelete,
  selectable = false,
  selected = false,
  onSelectedChange,
}: SearchCardProps) {
  const cardBody = (
    <CardContent className="space-y-4 p-5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-start gap-2">
            {selectable && (
              <button
                type="button"
                aria-label={selected ? `Deselect ${search.name}` : `Select ${search.name}`}
                aria-pressed={selected}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onSelectedChange?.(!selected);
                }}
                className={cn(
                  "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors",
                  selected
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-background text-transparent hover:border-primary/50"
                )}
              >
                <Check className="h-3 w-3" />
              </button>
            )}
            <div className="min-w-0">
              <h3 className="font-semibold leading-snug">{search.name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{search.job_title}</p>
            </div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Badge
            className={cn(
              "h-6 px-2.5",
              search.is_active ? "bg-success/15 text-success" : "bg-muted text-muted-foreground"
            )}
          >
            {search.is_active ? (
              <span className="inline-flex items-center gap-1">
                <Play className="h-3 w-3 shrink-0" /> Active
              </span>
            ) : (
              <span className="inline-flex items-center gap-1">
                <Pause className="h-3 w-3 shrink-0" /> Paused
              </span>
            )}
          </Badge>
          {onDelete && !selectable && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-destructive"
              aria-label={`Delete ${search.name}`}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onDelete();
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      <p className="line-clamp-2 text-sm text-muted-foreground">{search.field_domain}</p>
      <div className="flex flex-wrap items-center gap-1.5">
        {search.work_mode && (
          <Badge className="h-6 bg-secondary px-2.5 text-secondary-foreground">
            {labelEnum(search.work_mode)}
          </Badge>
        )}
        {search.posted_within_days && (
          <Badge className="h-6 bg-secondary px-2.5 text-secondary-foreground">
            Last {search.posted_within_days}d
          </Badge>
        )}
      </div>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <Clock className="h-3 w-3 shrink-0" />
          {search.last_run_at ? `Ran ${formatRelativeDate(search.last_run_at)}` : "Never run"}
        </span>
        {resultCount !== undefined && (
          <span className="font-medium text-foreground">{resultCount} matches</span>
        )}
      </div>
    </CardContent>
  );

  if (selectable) {
    return (
      <Card
        className={cn(
          "h-full cursor-pointer transition-all hover:border-primary/40 hover:shadow-glow",
          selected && "border-primary/60 ring-1 ring-primary/30"
        )}
        onClick={() => onSelectedChange?.(!selected)}
      >
        {cardBody}
      </Card>
    );
  }

  return (
    <Card className="group h-full transition-all hover:border-primary/40 hover:shadow-glow">
      <Link href={`/dashboard/searches/${search.id}`} className="block">
        {cardBody}
      </Link>
    </Card>
  );
}
