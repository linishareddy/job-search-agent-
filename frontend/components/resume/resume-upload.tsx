"use client";

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Upload } from "lucide-react";
import { toast } from "sonner";
import { resumesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";

const ACCEPTED = ".pdf,.docx,.txt";

export function ResumeUpload() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumesApi.upload(file),
    onSuccess: () => {
      toast.success("Resume uploaded and parsed");
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  function handleFile(file: File | undefined) {
    if (!file) return;
    uploadMutation.mutate(file);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border border-dashed p-10 text-center transition-colors ${
        dragOver ? "border-primary bg-primary/5" : "border-border"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <Upload className="mb-4 h-8 w-8 text-muted-foreground" />
      <p className="font-medium">Drop your resume here, or</p>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <Button
        variant="secondary"
        size="sm"
        className="mt-3 gap-2"
        disabled={uploadMutation.isPending}
        onClick={() => inputRef.current?.click()}
      >
        {uploadMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
        {uploadMutation.isPending ? "Uploading…" : "Browse files"}
      </Button>
      <p className="mt-3 text-xs text-muted-foreground">PDF, DOCX, or TXT — max 5MB</p>
    </div>
  );
}
