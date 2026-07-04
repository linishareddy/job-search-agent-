"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Search, Zap } from "lucide-react";
import { toast } from "sonner";
import { searchesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ResumeAttach } from "@/components/search/resume-attach";
import { FilterChips } from "@/components/search/search-filters";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { POSTED_WITHIN_OPTIONS } from "@/lib/constants/filters";

const EXAMPLE =
  "Remote senior software engineer in the US, full time, Python and backend, 150k+";

export default function NewSearchPage() {
  const MAX_CHARS = 5000;
  const router = useRouter();
  const [text, setText] = useState("");
  const [postedWithinDays, setPostedWithinDays] = useState<number>(0);

  const createMutation = useMutation({
    mutationFn: () =>
      searchesApi.createFromText({
        text,
        overrides: postedWithinDays > 0 ? { posted_within_days: postedWithinDays } : null,
        run_immediately: true,
      }),
    onSuccess: (res) => {
      if (res.data) {
        toast.success("Search created — pipeline started");
        const id = res.data.id;
        const runId = (res.data as { run_id?: string }).run_id;
        router.push(`/dashboard/searches/${id}${runId ? "?running=1" : ""}`);
      }
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  function handleResumeExtracted(extractedText: string) {
    const merged = text.trim() ? `${text.trim()}\n\n${extractedText}` : extractedText;
    setText(merged.slice(0, MAX_CHARS));
  }

  const charCount = text.length;
  const isOverLimit = charCount > MAX_CHARS;
  const canCreate = text.trim().length >= 10 && !createMutation.isPending && !isOverLimit;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">New search</h1>
        <p className="text-sm text-muted-foreground">
          Describe the role in plain English — AI picks title, location, and filters for you.
        </p>
      </div>

      <Card className="border-border/80">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-medium">
            <Search className="h-4 w-4 text-primary" />
            What are you looking for?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="overflow-hidden rounded-xl border border-input bg-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-background">
            <Textarea
              placeholder={EXAMPLE}
              value={text}
              onChange={(e) => setText(e.target.value.slice(0, MAX_CHARS))}
              maxLength={MAX_CHARS}
              className="min-h-[160px] resize-none border-0 bg-transparent px-4 py-4 text-base leading-relaxed shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
            />
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border/60 px-3 py-2">
              <div className="flex items-center gap-1">
                <ResumeAttach variant="inline" onExtracted={handleResumeExtracted} />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8 text-muted-foreground"
                  onClick={() => setText(EXAMPLE)}
                >
                  Use example
                </Button>
              </div>
              <span
                className={`text-xs tabular-nums ${isOverLimit ? "font-medium text-destructive" : "text-muted-foreground"}`}
              >
                {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-3 rounded-xl border border-border/60 bg-muted/20 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium">Posted within</p>
              <p className="text-xs text-muted-foreground">Default filter when viewing results</p>
            </div>
            <FilterChips
              options={POSTED_WITHIN_OPTIONS.map((o) => ({ label: o.label, value: o.value }))}
              value={postedWithinDays}
              onChange={setPostedWithinDays}
              aria-label="Posted within"
            />
          </div>

          <Button
            size="lg"
            className="w-full gap-2"
            disabled={!canCreate}
            onClick={() => createMutation.mutate()}
          >
            {createMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            Start hunting
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
