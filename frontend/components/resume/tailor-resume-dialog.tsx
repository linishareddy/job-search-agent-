"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Copy, Download, Loader2, Sparkles, X } from "lucide-react";
import { toast } from "sonner";
import { resumesApi } from "@/lib/api";
import { ApiError, parseApiError } from "@/lib/types/api";
import { ResumePreview } from "@/components/resume/resume-preview";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogClose, DialogTitle } from "@/components/ui/dialog";

type Tab = "preview" | "suggestions" | "plain";

export function TailorResumeDialog({
  open,
  onOpenChange,
  resumeId,
  resumeFilename,
  jobId,
  jobTitle,
  companyName,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  resumeFilename: string;
  jobId: string;
  jobTitle: string;
  companyName: string;
}) {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [tab, setTab] = useState<Tab>("preview");
  const [downloading, setDownloading] = useState(false);

  const tailoringQuery = useQuery({
    queryKey: ["resume-tailoring", resumeId, jobId],
    queryFn: () => resumesApi.getTailoring(resumeId, jobId),
    enabled: open && !!resumeId && !!jobId,
    retry: false,
  });

  const notGenerated = tailoringQuery.error instanceof ApiError && tailoringQuery.error.status === 404;
  const tailoring = tailoringQuery.data?.data ?? null;

  const tailorMutation = useMutation({
    mutationFn: () => resumesApi.tailorResume(resumeId, jobId),
    onSuccess: (res) => {
      queryClient.setQueryData(["resume-tailoring", resumeId, jobId], res);
      setTab("preview");
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  async function copy() {
    if (!tailoring) return;
    await navigator.clipboard.writeText(tailoring.tailored_resume);
    setCopied(true);
    toast.success("Tailored resume copied");
    setTimeout(() => setCopied(false), 2000);
  }

  async function downloadDocx() {
    setDownloading(true);
    try {
      await resumesApi.downloadTailored(resumeId, jobId);
      toast.success("Resume downloaded");
    } catch (err) {
      toast.error(parseApiError(err));
    } finally {
      setDownloading(false);
    }
  }

  const isBusy = tailorMutation.isPending;
  const isLoadingInitial = tailoringQuery.isLoading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent open={open}>
        <div className="flex items-center justify-between border-b border-border p-4">
          <DialogTitle>
            Tailor {resumeFilename} — {jobTitle} at {companyName}
          </DialogTitle>
          <DialogClose asChild>
            <button aria-label="Close" className="text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          </DialogClose>
        </div>

        <div className="space-y-4 overflow-y-auto p-4">
          {isLoadingInitial && (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {!isLoadingInitial && !tailoring && (
            <div className="flex flex-col items-center gap-3 py-10 text-center">
              <Sparkles className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {notGenerated
                  ? "No tailored version yet — generate one for this job."
                  : "Couldn't load a tailored version — try generating one."}
              </p>
              <Button size="sm" className="gap-2" disabled={isBusy} onClick={() => tailorMutation.mutate()}>
                {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                Generate
              </Button>
            </div>
          )}

          {tailoring && (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Badge className="h-7 bg-primary/15 px-3 text-sm text-primary">
                  Match score: {Math.round(tailoring.match_score)}%
                </Badge>
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="gap-2"
                    disabled={isBusy}
                    onClick={() => tailorMutation.mutate()}
                  >
                    {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                    Regenerate
                  </Button>
                  {tailoring.docx_available && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-2"
                      disabled={downloading}
                      onClick={downloadDocx}
                    >
                      {downloading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                      Download DOCX
                    </Button>
                  )}
                  <Button size="sm" variant="outline" className="gap-2" onClick={copy}>
                    {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    {copied ? "Copied" : "Copy text"}
                  </Button>
                </div>
              </div>

              {(tailoring.matched_keywords.length > 0 || tailoring.missing_keywords.length > 0) && (
                <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-3 text-sm">
                  {tailoring.matched_keywords.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-xs text-muted-foreground">You have:</span>
                      {tailoring.matched_keywords.map((k) => (
                        <Badge key={k} className="h-6 bg-success/15 px-2.5 text-success">
                          {k}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {tailoring.missing_keywords.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-xs text-muted-foreground">Consider adding:</span>
                      {tailoring.missing_keywords.map((k) => (
                        <Badge key={k} className="h-6 bg-warning/15 px-2.5 text-warning">
                          {k}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-1 rounded-lg border border-border bg-muted/30 p-1">
                {(["preview", "suggestions", "plain"] as Tab[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={`flex-1 rounded-md px-3 py-1.5 text-sm capitalize transition-colors ${
                      tab === t ? "bg-background font-medium shadow-sm" : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {t === "plain" ? "Plain text" : t}
                  </button>
                ))}
              </div>

              {tab === "preview" && tailoring.tailored_sections && (
                <div className="max-h-[28rem] overflow-y-auto">
                  <ResumePreview sections={tailoring.tailored_sections} />
                </div>
              )}

              {tab === "preview" && !tailoring.tailored_sections && (
                <div className="h-64 w-full overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-sm leading-relaxed text-foreground">
                  {tailoring.tailored_resume}
                </div>
              )}

              {tab === "suggestions" && (
                <div className="space-y-3">
                  {tailoring.suggestions.length > 0 ? (
                    tailoring.suggestions.map((s, i) => (
                      <div key={i} className="space-y-1 rounded-lg border border-border p-3 text-sm">
                        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          {s.section}
                        </p>
                        <p className="text-foreground">{s.suggested}</p>
                        {s.reason && <p className="text-xs text-muted-foreground">{s.reason}</p>}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No section suggestions for this tailoring.</p>
                  )}

                  {tailoring.gaps.length > 0 && (
                    <div className="rounded-lg border border-warning/30 bg-warning/5 p-3 text-sm">
                      <p className="font-medium text-warning">Gaps</p>
                      <ul className="mt-1 list-inside list-disc text-muted-foreground">
                        {tailoring.gaps.map((g, i) => (
                          <li key={i}>{g}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {tab === "plain" && (
                <div className="h-64 w-full overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-sm leading-relaxed text-foreground">
                  {tailoring.tailored_resume}
                </div>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
