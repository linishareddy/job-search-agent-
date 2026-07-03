"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Search, Sparkles, Zap } from "lucide-react";
import { toast } from "sonner";
import { searchesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import type { ParsedSearchIntent, SavedSearchUpdate } from "@/lib/types/search";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ParsedIntentPreview } from "@/components/search/parsed-intent-preview";
import { FilterChips } from "@/components/search/search-filters";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const EXAMPLE =
  "Remote senior software engineer in the US, full time, Python and backend, 150k+";

const POSTED_OPTIONS = [
  { label: "All time", value: 0 },
  { label: "7 days", value: 7 },
  { label: "14 days", value: 14 },
  { label: "30 days", value: 30 },
] as const;

export default function NewSearchPage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [parsed, setParsed] = useState<ParsedSearchIntent | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [postedWithinDays, setPostedWithinDays] = useState<number>(0);
  const [overrides, setOverrides] = useState<SavedSearchUpdate>({});

  const lastParsedTextRef = useRef<string>("");
  const parseRequestIdRef = useRef(0);

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

  async function runParse(force = false) {
    const trimmed = text.trim();
    if (trimmed.length < 10) {
      setParsed(null);
      setParseError("Enter at least 10 characters before previewing");
      return;
    }
    if (!force && trimmed === lastParsedTextRef.current && parsed) {
      return;
    }

    const requestId = ++parseRequestIdRef.current;
    setIsParsing(true);
    setParseError(null);

    try {
      const res = await searchesApi.parseText(trimmed);
      if (requestId !== parseRequestIdRef.current) return;
      if (res.data) {
        lastParsedTextRef.current = trimmed;
        setParsed(res.data);
      }
    } catch (err) {
      if (requestId !== parseRequestIdRef.current) return;
      setParseError(parseApiError(err));
      setParsed(null);
    } finally {
      if (requestId === parseRequestIdRef.current) {
        setIsParsing(false);
      }
    }
  }

  function handleTextChange(value: string) {
    setText(value);
    // Clear stale preview when user edits — no API call until they click Preview.
    if (value.trim() !== lastParsedTextRef.current) {
      setParsed(null);
      setParseError(null);
    }
  }

  const canCreate = text.trim().length >= 10 && !createMutation.isPending;

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
          <Textarea
            placeholder={EXAMPLE}
            value={text}
            onChange={(e) => handleTextChange(e.target.value)}
            className="min-h-[140px] text-base"
          />
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setText(EXAMPLE);
                setParsed(null);
                setParseError(null);
                lastParsedTextRef.current = "";
              }}
            >
              Use example
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="gap-2"
              disabled={text.trim().length < 10 || isParsing}
              onClick={() => void runParse(true)}
            >
              {isParsing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Preview with AI
            </Button>
            <span className="text-xs text-muted-foreground">
              Preview is optional — one Groq call when you click
            </span>
          </div>
          {parseError && <p className="text-sm text-destructive">{parseError}</p>}
        </CardContent>
      </Card>

      {parsed && <ParsedIntentPreview parsed={parsed} />}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="mb-2 block">Default time filter</Label>
            <FilterChips
              options={POSTED_OPTIONS.map((o) => ({ label: o.label, value: o.value }))}
              value={postedWithinDays}
              onChange={setPostedWithinDays}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="name">Override name</Label>
              <Input
                id="name"
                placeholder={parsed?.name ?? "Search name"}
                value={overrides.name ?? ""}
                onChange={(e) => setOverrides((o) => ({ ...o, name: e.target.value || undefined }))}
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="location">Override location</Label>
              <Input
                id="location"
                placeholder={parsed?.location ?? "United States"}
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
