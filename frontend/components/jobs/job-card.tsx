"use client";

import { motion } from "framer-motion";
import { ExternalLink, MapPin } from "lucide-react";
import type { JobSearchResult } from "@/lib/types/job";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { RelevanceScore } from "@/components/jobs/relevance-score";
import {
  cn,
  formatRelativeDate,
  formatSalary,
  labelEnum,
  sourceBadgeClass,
} from "@/lib/utils";

export function JobCard({ result, index = 0 }: { result: JobSearchResult; index?: number }) {
  const { job } = result;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.35 }}
    >
      <Card className="group overflow-hidden transition-shadow hover:shadow-glow">
        <CardContent className="p-5">
          <div className="flex gap-4">
            <RelevanceScore score={result.relevance_score} />
            <div className="min-w-0 flex-1 space-y-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {result.is_new && (
                      <Badge className="bg-primary/15 text-primary">New</Badge>
                    )}
                    <Badge className={sourceBadgeClass(job.source)}>{job.source}</Badge>
                  </div>
                  <h3 className="text-base font-semibold leading-snug">{job.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {job.company_name}
                    {job.location && (
                      <span className="inline-flex items-center gap-1">
                        {" "}
                        · <MapPin className="h-3 w-3" /> {job.location}
                      </span>
                    )}
                  </p>
                </div>
                <a
                  href={job.apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex h-8 shrink-0 items-center justify-center gap-2 rounded-lg bg-primary px-3 text-xs font-medium text-primary-foreground hover:opacity-90"
                >
                  Apply <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>

              <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                {job.work_mode && (
                  <span className="rounded-md bg-secondary px-2 py-1">{labelEnum(job.work_mode)}</span>
                )}
                <span
                  className={cn(
                    "rounded-md px-2 py-1",
                    job.salary_listed ? "bg-secondary" : "bg-warning/10 text-warning"
                  )}
                >
                  {formatSalary(job.salary_min, job.salary_max)}
                </span>
                <span className="rounded-md bg-secondary px-2 py-1">
                  Posted {formatRelativeDate(job.posted_at)}
                </span>
              </div>

              {job.description_summary && (
                <p className="text-sm leading-relaxed text-muted-foreground">{job.description_summary}</p>
              )}

              {job.skills?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {job.skills.slice(0, 8).map((skill) => (
                    <Badge key={skill} className="bg-muted text-muted-foreground">
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}

              {(result.match_reason || result.gaps) && (
                <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-3 text-sm">
                  {result.match_reason && (
                    <p>
                      <span className="font-medium text-success">Match: </span>
                      {result.match_reason}
                    </p>
                  )}
                  {result.gaps && result.gaps !== "None notable" && (
                    <p>
                      <span className="font-medium text-warning">Gap: </span>
                      {result.gaps}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function JobCardSkeleton() {
  return (
    <Card>
      <CardContent className="flex gap-4 p-5">
        <div className="h-14 w-14 animate-pulse rounded-full bg-muted" />
        <div className="flex-1 space-y-3">
          <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
          <div className="h-3 w-1/2 animate-pulse rounded bg-muted" />
          <div className="h-16 w-full animate-pulse rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  );
}
