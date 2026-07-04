"use client";

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Paperclip, X } from "lucide-react";
import { toast } from "sonner";
import { resumesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const ACCEPTED = ".pdf,.docx,.txt";

export function ResumeAttach({
  onExtracted,
  variant = "default",
}: {
  onExtracted: (text: string) => void;
  variant?: "default" | "inline";
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [attachedName, setAttachedName] = useState<string | null>(null);

  const extractMutation = useMutation({
    mutationFn: (file: File) => resumesApi.extractText(file),
    onSuccess: (res, file) => {
      if (res.data) {
        onExtracted(res.data.text);
        setAttachedName(file.name);
        toast.success("Resume text added to your description");
      }
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  function handleFile(file: File | undefined) {
    if (!file) return;
    extractMutation.mutate(file);
    if (inputRef.current) inputRef.current.value = "";
  }

  const inline = variant === "inline";

  return (
    <div className={cn("flex items-center gap-2", inline && "gap-1.5")}>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <Button
        type="button"
        variant={inline ? "ghost" : "outline"}
        size={inline ? "icon" : "sm"}
        className={cn(inline && "h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground")}
        disabled={extractMutation.isPending}
        aria-label={attachedName ? "Replace resume" : "Attach resume"}
        title={attachedName ? `Attached: ${attachedName}` : "Attach resume (optional)"}
        onClick={() => inputRef.current?.click()}
      >
        {extractMutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Paperclip className="h-4 w-4" />
        )}
      </Button>
      {!inline && (
        <span className="text-sm text-muted-foreground">
          {attachedName ? "Replace resume" : "Attach resume (optional)"}
        </span>
      )}
      {attachedName && (
        <span
          className={cn(
            "inline-flex max-w-[10rem] items-center gap-1 truncate rounded-md bg-secondary px-2 py-1 text-xs text-secondary-foreground",
            inline && "max-w-[8rem]"
          )}
          title={attachedName}
        >
          <span className="truncate">{attachedName}</span>
          <button
            type="button"
            className="shrink-0"
            onClick={() => setAttachedName(null)}
            aria-label="Clear attachment indicator"
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      )}
    </div>
  );
}
