"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, Loader2, Save } from "lucide-react";
import { toast } from "sonner";
import { searchesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import type { SavedSearchUpdate } from "@/lib/types/search";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FilterChips } from "@/components/search/search-filters";

const WORK_MODES = ["any", "remote", "hybrid", "onsite"].map((v) => ({
  label: v.charAt(0).toUpperCase() + v.slice(1),
  value: v,
}));

const LEVELS = ["any", "entry", "mid", "senior", "lead"].map((v) => ({
  label: v.charAt(0).toUpperCase() + v.slice(1),
  value: v,
}));

const POSTED = [
  { label: "No filter", value: 0 },
  { label: "7 days", value: 7 },
  { label: "14 days", value: 14 },
  { label: "30 days", value: 30 },
];

export default function EditSearchPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<SavedSearchUpdate>({});

  const { data, isLoading } = useQuery({
    queryKey: ["search", id],
    queryFn: () => searchesApi.get(id),
    enabled: !!id,
  });

  const search = data?.data;

  useEffect(() => {
    if (search) {
      setForm({
        name: search.name,
        job_title: search.job_title,
        field_domain: search.field_domain,
        location: search.location ?? "",
        work_mode: search.work_mode ?? "any",
        experience_level: search.experience_level ?? "any",
        salary_min: search.salary_min ?? undefined,
        salary_max: search.salary_max ?? undefined,
        posted_within_days: search.posted_within_days ?? undefined,
        poll_interval_minutes: search.poll_interval_minutes,
        is_active: search.is_active,
      });
    }
  }, [search]);

  const updateMutation = useMutation({
    mutationFn: (payload: SavedSearchUpdate) => searchesApi.update(id, payload),
    onSuccess: () => {
      toast.success("Search saved");
      queryClient.invalidateQueries({ queryKey: ["search", id] });
      router.push(`/dashboard/searches/${id}`);
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  if (isLoading || !search) {
    return <div className="h-64 animate-pulse rounded-xl bg-muted" />;
  }

  const postedVal = form.posted_within_days ?? 0;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Link
        href={`/dashboard/searches/${id}`}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="h-4 w-4" /> Back to results
      </Link>
      <h1 className="text-2xl font-bold">Edit search</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Search configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input
              className="mt-1.5"
              value={form.name ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <Label>Job title</Label>
            <Input
              className="mt-1.5"
              value={form.job_title ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, job_title: e.target.value }))}
            />
          </div>
          <div>
            <Label>Field / domain</Label>
            <Textarea
              className="mt-1.5"
              value={form.field_domain ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, field_domain: e.target.value }))}
            />
          </div>
          <div>
            <Label>Location</Label>
            <Input
              className="mt-1.5"
              value={form.location ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
            />
          </div>
          <div>
            <Label className="mb-2 block">Work mode</Label>
            <FilterChips
              options={WORK_MODES}
              value={form.work_mode ?? "any"}
              onChange={(v) => setForm((f) => ({ ...f, work_mode: v }))}
            />
          </div>
          <div>
            <Label className="mb-2 block">Experience level</Label>
            <FilterChips
              options={LEVELS}
              value={form.experience_level ?? "any"}
              onChange={(v) => setForm((f) => ({ ...f, experience_level: v }))}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Salary min</Label>
              <Input
                type="number"
                className="mt-1.5"
                value={form.salary_min ?? ""}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    salary_min: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
              />
            </div>
            <div>
              <Label>Salary max</Label>
              <Input
                type="number"
                className="mt-1.5"
                value={form.salary_max ?? ""}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    salary_max: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
              />
            </div>
          </div>
          <div>
            <Label className="mb-2 block">Default posted within</Label>
            <FilterChips
              options={POSTED}
              value={postedVal}
              onChange={(v) =>
                setForm((f) => ({
                  ...f,
                  posted_within_days: v > 0 ? v : undefined,
                }))
              }
            />
          </div>
          <div>
            <Label>Poll interval (minutes)</Label>
            <Input
              type="number"
              min={30}
              max={1440}
              className="mt-1.5"
              value={form.poll_interval_minutes ?? 60}
              onChange={(e) =>
                setForm((f) => ({ ...f, poll_interval_minutes: Number(e.target.value) }))
              }
            />
          </div>
        </CardContent>
      </Card>

      <Button
        className="gap-2"
        onClick={() => updateMutation.mutate(form)}
        disabled={updateMutation.isPending}
      >
        {updateMutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Save className="h-4 w-4" />
        )}
        Save changes
      </Button>
    </div>
  );
}
