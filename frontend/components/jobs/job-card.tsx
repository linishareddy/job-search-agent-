"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { BookmarkPlus, ExternalLink, Loader2, MapPin, Sparkles } from "lucide-react";
import { toast } from "sonner";
import type { JobSearchResult } from "@/lib/types/job";
import { parseApiError } from "@/lib/types/api";
import { applicationsApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { TailorResumeDialog } from "@/components/resume/tailor-resume-dialog";
import {
  cn,
  formatRelativeDate,
  formatSalary,
  labelEnum,
  sourceBadgeClass,
} from "@/lib/utils";

export function JobCard({
  result,
  index = 0,
  resumeId,
  resumeFilename,
}: {
  result: JobSearchResult;
  index?: number;
  /** Currently selected resume (from the "Match against resume" picker on the
   * results page) — when set, offers a "Tailor resume" action for this job. */
  resumeId?: string;
  resumeFilename?: string;
}) {
  const { job } = result;
  const [tailorOpen, setTailorOpen] = useState(false);

  const saveMutation = useMutation({
    mutationFn: () => applicationsApi.create(job.id),
    onSuccess: () => toast.success("Saved to tracker"),
    onError: (err) => toast.error(parseApiError(err)),
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.35 }}
    >
      <Card className="group overflow-hidden transition-shadow hover:shadow-glow">
        <CardContent className="p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1 space-y-2">
              <div className="flex flex-wrap items-center gap-1.5">
                {result.is_new && (
                  <Badge className="h-6 bg-primary/15 px-2.5 text-primary">New</Badge>
                )}
                <Badge className={cn("h-6 px-2.5", sourceBadgeClass(job.source))}>
                  {job.source}
                </Badge>
              </div>
              <div>
                <h3 className="text-base font-semibold leading-snug">{job.title}</h3>
                <p className="mt-1 flex flex-wrap items-center gap-x-1 gap-y-0.5 text-sm text-muted-foreground">
                  <span>{job.company_name}</span>
                  {job.location && (
                    <>
                      <span aria-hidden>·</span>
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 shrink-0" />
                        {job.location}
                      </span>
                    </>
                  )}
                </p>
              </div>
            </div>

            <div className="flex w-full shrink-0 flex-col gap-1.5 sm:w-auto sm:min-w-[9.5rem]">
              <div className="flex items-center gap-1.5">
                <Button asChild size="sm" className="h-8 flex-1 gap-2">
                  <a href={job.apply_url} target="_blank" rel="noopener noreferrer">
                    Apply
                    <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                  </a>
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8 shrink-0"
                  aria-label="Save to tracker"
                  disabled={saveMutation.isPending}
                  onClick={() => saveMutation.mutate()}
                >
                  {saveMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <BookmarkPlus className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
              {resumeId && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-full gap-1.5 text-xs"
                  onClick={() => setTailorOpen(true)}
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Tailor resume
                </Button>
              )}
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-1.5">
            {job.work_mode && (
              <Badge className="h-6 bg-secondary px-2.5 text-secondary-foreground">
                {labelEnum(job.work_mode)}
              </Badge>
            )}
            <Badge
              className={cn(
                "h-6 px-2.5",
                job.salary_listed ? "bg-secondary text-secondary-foreground" : "bg-warning/10 text-warning"
              )}
            >
              {formatSalary(job.salary_min, job.salary_max)}
            </Badge>
            <Badge className="h-6 bg-secondary px-2.5 text-secondary-foreground">
              Posted {formatRelativeDate(job.posted_at)}
            </Badge>
          </div>

          <div className="mt-3 space-y-3">
            {job.description_summary && (
              <p className="text-sm leading-relaxed text-muted-foreground">{job.description_summary}</p>
            )}

            {job.skills?.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                {job.skills.slice(0, 8).map((skill) => (
                  <Badge key={skill} className="h-6 bg-muted px-2.5 text-muted-foreground">
                    {skill}
                  </Badge>
                ))}
              </div>
            )}

            {result.match && (
              <div className="space-y-2 rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm">
                <p className="flex items-center gap-2 font-medium">
                  <span className="text-primary">Resume match: {Math.round(result.match.match_score * 100)}%</span>
                </p>
                {result.match.matched_skills.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-xs text-muted-foreground">You have:</span>
                    {result.match.matched_skills.map((s) => (
                      <Badge key={s} className="h-6 bg-success/15 px-2.5 text-success">
                        {s}
                      </Badge>
                    ))}
                  </div>
                )}
                {result.match.missing_skills.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-xs text-muted-foreground">Skills to close:</span>
                    {result.match.missing_skills.map((s) => (
                      <Badge key={s} className="h-6 bg-warning/15 px-2.5 text-warning">
                        {s}
                      </Badge>
                    ))}
                  </div>
                )}
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
        </CardContent>
      </Card>

      {resumeId && (
        <TailorResumeDialog
          open={tailorOpen}
          onOpenChange={setTailorOpen}
          resumeId={resumeId}
          resumeFilename={resumeFilename ?? "resume"}
          jobId={job.id}
          jobTitle={job.title}
          companyName={job.company_name}
        />
      )}
    </motion.div>
  );
}

export function JobCardSkeleton() {
  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-muted" />
        <div className="h-16 w-full animate-pulse rounded bg-muted" />
      </CardContent>
    </Card>
  );
}
