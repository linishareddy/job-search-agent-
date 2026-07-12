"use client";

import { useState } from "react";
import { Check, Copy, X } from "lucide-react";
import { toast } from "sonner";
import type { JobApplication } from "@/lib/types/application";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogClose, DialogTitle } from "@/components/ui/dialog";

export function AutoApplyDetailsDialog({
  open,
  onOpenChange,
  app,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  app: JobApplication | null;
}) {
  const [copiedField, setCopiedField] = useState<"cover_letter" | "tailored_resume" | null>(null);

  async function copy(field: "cover_letter" | "tailored_resume", text: string) {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    toast.success("Copied");
    setTimeout(() => setCopiedField(null), 2000);
  }

  if (!app) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent open={open}>
        <div className="flex items-center justify-between border-b border-border p-4">
          <DialogTitle>
            {app.job.title} — {app.job.company_name}
          </DialogTitle>
          <DialogClose asChild>
            <button aria-label="Close" className="text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          </DialogClose>
        </div>
        <div className="space-y-4 overflow-y-auto p-4">
          {app.match_score != null && (
            <Badge className="h-7 bg-primary/15 px-3 text-sm text-primary">
              Match score: {Math.round(app.match_score * 100)}%
            </Badge>
          )}

          {app.tailored_resume && (
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <p className="text-sm font-medium">Tailored resume</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-2"
                  onClick={() => copy("tailored_resume", app.tailored_resume as string)}
                >
                  {copiedField === "tailored_resume" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  Copy
                </Button>
              </div>
              <div className="h-48 w-full overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-sm leading-relaxed text-foreground">
                {app.tailored_resume}
              </div>
            </div>
          )}

          {app.cover_letter && (
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <p className="text-sm font-medium">Cover letter</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-2"
                  onClick={() => copy("cover_letter", app.cover_letter as string)}
                >
                  {copiedField === "cover_letter" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  Copy
                </Button>
              </div>
              <div className="h-48 w-full overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-sm leading-relaxed text-foreground">
                {app.cover_letter}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
