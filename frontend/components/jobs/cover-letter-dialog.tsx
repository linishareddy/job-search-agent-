"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, Copy, Loader2, Sparkles, X } from "lucide-react";
import { toast } from "sonner";
import { jobsApi, resumesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";

export function CoverLetterDialog({
  jobId,
  jobTitle,
  onClose,
}: {
  jobId: string;
  jobTitle: string;
  onClose: () => void;
}) {
  const [resumeId, setResumeId] = useState<string>("");
  const [letter, setLetter] = useState<string>("");
  const [copied, setCopied] = useState(false);

  const resumesQuery = useQuery({
    queryKey: ["resumes"],
    queryFn: () => resumesApi.list(),
  });
  const resumes = resumesQuery.data?.data ?? [];

  // Default to the most-recently uploaded resume (list is returned newest-first).
  useEffect(() => {
    const list = resumesQuery.data?.data;
    if (!resumeId && list && list.length > 0) setResumeId(list[0].id);
  }, [resumesQuery.data, resumeId]);

  const generateMutation = useMutation({
    mutationFn: () => jobsApi.coverLetter(jobId, resumeId),
    onSuccess: (res) => {
      if (res.data) setLetter(res.data.cover_letter);
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  async function copy() {
    await navigator.clipboard.writeText(letter);
    setCopied(true);
    toast.success("Cover letter copied");
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-xl border border-border bg-card shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border p-4">
          <h3 className="font-semibold">Cover letter — {jobTitle}</h3>
          <button onClick={onClose} aria-label="Close" className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 overflow-y-auto p-4">
          {resumes.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Upload a resume first (Resume tab) to generate a tailored cover letter.
            </p>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <label className="text-sm text-muted-foreground">Using resume:</label>
              <select
                value={resumeId}
                onChange={(e) => setResumeId(e.target.value)}
                className="rounded-lg border border-border bg-background px-2 py-1.5 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.filename}
                  </option>
                ))}
              </select>
              <Button
                size="sm"
                className="gap-2"
                disabled={!resumeId || generateMutation.isPending}
                onClick={() => generateMutation.mutate()}
              >
                {generateMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                {letter ? "Regenerate" : "Generate"}
              </Button>
            </div>
          )}

          {letter && (
            <div className="space-y-2">
              <div className="flex justify-end">
                <Button variant="outline" size="sm" className="gap-2" onClick={copy}>
                  {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  {copied ? "Copied" : "Copy"}
                </Button>
              </div>
              <textarea
                readOnly
                value={letter}
                className="h-80 w-full resize-none rounded-lg border border-border bg-background p-3 text-sm leading-relaxed text-foreground focus-visible:outline-none"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
