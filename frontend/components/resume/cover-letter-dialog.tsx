"use client";

import { useState } from "react";
import { Check, Copy, Loader2, Sparkles, X } from "lucide-react";
import { toast } from "sonner";
import { resumesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogClose, DialogTitle } from "@/components/ui/dialog";

export function CoverLetterDialog({
  open,
  onOpenChange,
  resumeId,
  resumeFilename,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  resumeFilename: string;
}) {
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [letter, setLetter] = useState("");
  const [copied, setCopied] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const canGenerate = jobTitle.trim().length > 0 && companyName.trim().length > 0 && !isStreaming;

  async function generate() {
    setLetter("");
    setIsStreaming(true);
    try {
      const stream = await resumesApi.coverLetterStream(resumeId, {
        job_title: jobTitle.trim(),
        company_name: companyName.trim(),
        job_description: jobDescription.trim() || undefined,
      });
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        setLetter((prev) => prev + decoder.decode(value, { stream: true }));
      }
    } catch (err) {
      toast.error(parseApiError(err));
    } finally {
      setIsStreaming(false);
    }
  }

  async function copy() {
    await navigator.clipboard.writeText(letter);
    setCopied(true);
    toast.success("Cover letter copied");
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent open={open}>
        <div className="flex items-center justify-between border-b border-border p-4">
          <DialogTitle>Cover letter — using {resumeFilename}</DialogTitle>
          <DialogClose asChild>
            <button aria-label="Close" className="text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          </DialogClose>
        </div>

        <div className="space-y-4 overflow-y-auto p-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="cl-job-title">Job title</Label>
              <Input
                id="cl-job-title"
                className="mt-1.5"
                placeholder="Senior Backend Engineer"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="cl-company">Company</Label>
              <Input
                id="cl-company"
                className="mt-1.5"
                placeholder="Acme Inc."
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </div>
          </div>
          <div>
            <Label htmlFor="cl-description">Job description (optional)</Label>
            <Textarea
              id="cl-description"
              className="mt-1.5 min-h-[100px]"
              placeholder="Paste the job posting for a more tailored letter"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-between">
            <Button size="sm" className="gap-2" disabled={!canGenerate} onClick={generate}>
              {isStreaming ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {letter ? "Regenerate" : "Generate"}
            </Button>
            {letter && !isStreaming && (
              <Button variant="outline" size="sm" className="gap-2" onClick={copy}>
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                {copied ? "Copied" : "Copy"}
              </Button>
            )}
          </div>

          {(letter || isStreaming) && (
            <div className="h-72 w-full overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-sm leading-relaxed text-foreground">
              {letter}
              {isStreaming && (
                <span
                  className="-mb-0.5 ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-primary"
                  aria-hidden="true"
                />
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
