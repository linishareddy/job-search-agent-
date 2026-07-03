"use client";

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Paperclip, X } from "lucide-react";
import { toast } from "sonner";
import { resumesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const ACCEPTED = ".pdf,.docx,.txt";

export function ResumeAttach({ onExtracted }: { onExtracted: (text: string) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [attachedName, setAttachedName] = useState<string | null>(null);

  const extractMutation = useMutation({
    mutationFn: (file: File) => resumesApi.extractText(file),
    onSuccess: (res, file) => {
      if (res.data) {
        onExtracted(res.data.text);
        setAttachedName(file.name);
        toast.success("Resume text added below your description");
      }
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  function handleFile(file: File | undefined) {
    if (!file) return;
    extractMutation.mutate(file);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="flex items-center gap-2">
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="gap-2"
        disabled={extractMutation.isPending}
        onClick={() => inputRef.current?.click()}
      >
        {extractMutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Paperclip className="h-4 w-4" />
        )}
        {attachedName ? "Replace resume" : "Attach resume (optional)"}
      </Button>
      {attachedName && (
        <Badge className="gap-1 bg-secondary text-secondary-foreground">
          {attachedName}
          <button type="button" onClick={() => setAttachedName(null)} aria-label="Clear attachment indicator">
            <X className="h-3 w-3" />
          </button>
        </Badge>
      )}
    </div>
  );
}
