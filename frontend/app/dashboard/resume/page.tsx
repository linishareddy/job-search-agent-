"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { resumesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ResumeUpload } from "@/components/resume/resume-upload";

function formatSize(bytes: number): string {
  return `${(bytes / 1024).toFixed(0)} KB`;
}

const STATUS_LABEL: Record<string, string> = {
  pending: "Parsing…",
  parsed: "Parsed",
  failed: "Parse failed",
};

export default function ResumePage() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => resumesApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => resumesApi.delete(id),
    onSuccess: () => {
      toast.success("Resume removed");
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const resumes = data?.data ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Resume</h1>
        <p className="text-muted-foreground">
          Upload a resume to extract your skills, titles, and experience level
        </p>
      </div>

      <ResumeUpload />

      {isLoading && <Skeleton className="h-32 w-full" />}

      {isError && (
        <div className="rounded-xl border border-destructive/30 p-6 text-center">
          <p className="text-destructive">{parseApiError(error)}</p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {!isLoading && resumes.length === 0 && !isError && (
        <div className="flex flex-col items-center rounded-xl border border-dashed py-16 text-center">
          <FileText className="mb-4 h-10 w-10 text-muted-foreground" />
          <p className="font-medium">No resumes uploaded yet</p>
        </div>
      )}

      <div className="space-y-3">
        {resumes.map((r) => (
          <Card key={r.id}>
            <CardContent className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <p className="font-medium">{r.filename}</p>
                  <span className="text-xs text-muted-foreground">{formatSize(r.file_size)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    className={
                      r.parse_status === "parsed"
                        ? "bg-success/15 text-success"
                        : r.parse_status === "failed"
                          ? "bg-destructive/15 text-destructive"
                          : "bg-muted text-muted-foreground"
                    }
                  >
                    {r.parse_status === "pending" && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                    {STATUS_LABEL[r.parse_status] ?? r.parse_status}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      if (confirm(`Remove ${r.filename}?`)) deleteMutation.mutate(r.id);
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>

              {r.parsed_data && (
                <div className="space-y-2 border-t border-border pt-3 text-sm">
                  {r.parsed_data.summary && <p className="text-muted-foreground">{r.parsed_data.summary}</p>}
                  <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                    {r.parsed_data.experience_level && (
                      <span>
                        Level: <span className="font-medium text-foreground">{r.parsed_data.experience_level}</span>
                      </span>
                    )}
                    {r.parsed_data.years_experience != null && (
                      <span>
                        Experience:{" "}
                        <span className="font-medium text-foreground">{r.parsed_data.years_experience} yrs</span>
                      </span>
                    )}
                  </div>
                  {r.parsed_data.job_titles.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {r.parsed_data.job_titles.map((t) => (
                        <Badge key={t} className="bg-primary/10 text-primary">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {r.parsed_data.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {r.parsed_data.skills.map((s) => (
                        <Badge key={s} className="bg-secondary text-secondary-foreground">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
