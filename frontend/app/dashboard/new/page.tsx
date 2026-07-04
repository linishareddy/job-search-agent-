"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Search, Zap } from "lucide-react";
import { toast } from "sonner";
import { searchesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import type { SavedSearchUpdate } from "@/lib/types/search";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
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
  const [overrides, setOverrides] = useState<SavedSearchUpdate>({});

  const createMutation = useMutation({
    mutationFn: () => {
      const o: SavedSearchUpdate = { ...overrides };
      if (postedWithinDays > 0) o.posted_within_days = postedWithinDays;
      return searchesApi.createFromText({
        text,
        overrides: Object.keys(o).length ? o : null,
        run_immediately: true,
      });
    },
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
    handleTextChange(merged);
  }

  function handleTextChange(value: string) {
    setText(value.slice(0, MAX_CHARS));
  }

  const charCount = text.length;
  const isOverLimit = charCount > MAX_CHARS;
  const canCreate = text.trim().length >= 10 && !createMutation.isPending && !isOverLimit;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New search</h1>
        <p className="text-muted-foreground">Describe the job you want — AI handles the rest</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Search className="h-4 w-4" /> What are you looking for?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="overflow-hidden rounded-lg border border-input bg-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-background">
            <Textarea
              placeholder={EXAMPLE}
              value={text}
              onChange={(e) => handleTextChange(e.target.value)}
              maxLength={MAX_CHARS}
              className="min-h-[140px] resize-none border-0 bg-transparent text-base shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
            />
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border/60 px-3 py-2">
              <div className="flex flex-wrap items-center gap-2">
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
              <span className={`text-xs ${isOverLimit ? "font-medium text-destructive" : "text-muted-foreground"}`}>
                {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="mb-2 block">Default time filter</Label>
            <FilterChips
              options={POSTED_WITHIN_OPTIONS.map((o) => ({ label: o.label, value: o.value }))}
              value={postedWithinDays}
              onChange={setPostedWithinDays}
              aria-label="Default time filter"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="name">Override name</Label>
              <Input
                id="name"
                placeholder="Search name"
                value={overrides.name ?? ""}
                onChange={(e) => setOverrides((o) => ({ ...o, name: e.target.value || undefined }))}
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="location">Override location</Label>
              <Input
                id="location"
                placeholder="United States"
                value={overrides.location ?? ""}
                onChange={(e) => setOverrides((o) => ({ ...o, location: e.target.value || undefined }))}
                className="mt-1.5"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Button
        size="lg"
        className="w-full gap-2 sm:w-auto"
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
    </div>
  );
}
