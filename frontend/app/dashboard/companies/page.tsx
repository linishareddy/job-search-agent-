"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Loader2, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { companiesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import type { AtsCompanyCreate } from "@/lib/types/misc";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FilterChips } from "@/components/search/search-filters";
import { sourceBadgeClass } from "@/lib/utils";

const SOURCES = [
  { label: "Greenhouse", value: "greenhouse" as const },
  { label: "Lever", value: "lever" as const },
  { label: "Ashby", value: "ashby" as const },
];

export default function CompaniesPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AtsCompanyCreate>({
    name: "",
    slug: "",
    source: "greenhouse",
  });

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["companies"],
    queryFn: () => companiesApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: () => companiesApi.create(form),
    onSuccess: () => {
      toast.success("Company added");
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      setForm({ name: "", slug: "", source: "greenhouse" });
      setShowForm(false);
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => companiesApi.delete(id),
    onSuccess: () => {
      toast.success("Company removed");
      queryClient.invalidateQueries({ queryKey: ["companies"] });
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const companies = data?.data ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">ATS companies</h1>
          <p className="text-muted-foreground">
            Career pages checked on every search run (Greenhouse, Lever, Ashby)
          </p>
        </div>
        <Button className="gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4" /> Add company
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Add company</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Company name</Label>
              <Input
                className="mt-1.5"
                placeholder="Stripe"
                value={form.name}
                onChange={(e) => {
                  const name = e.target.value;
                  setForm((f) => ({
                    ...f,
                    name,
                    slug: f.slug || name.toLowerCase().replace(/\s+/g, "-"),
                  }));
                }}
              />
            </div>
            <div>
              <Label>Slug (URL identifier)</Label>
              <Input
                className="mt-1.5 font-mono text-sm"
                placeholder="stripe"
                value={form.slug}
                onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
              />
            </div>
            <div>
              <Label className="mb-2 block">ATS source</Label>
              <FilterChips
                options={SOURCES}
                value={form.source}
                onChange={(v) => setForm((f) => ({ ...f, source: v }))}
              />
            </div>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!form.name || !form.slug || createMutation.isPending}
              className="gap-2"
            >
              {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Save company
            </Button>
          </CardContent>
        </Card>
      )}

      {isLoading && <div className="h-32 animate-pulse rounded-xl bg-muted" />}

      {isError && (
        <div className="rounded-xl border border-destructive/30 p-6 text-center">
          <p className="text-destructive">{parseApiError(error)}</p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {!isLoading && companies.length === 0 && (
        <div className="flex flex-col items-center rounded-xl border border-dashed py-16 text-center">
          <Building2 className="mb-4 h-10 w-10 text-muted-foreground" />
          <p className="font-medium">No companies on watchlist</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Add companies like Stripe or Airbnb to fetch jobs from their career pages.
          </p>
        </div>
      )}

      <div className="space-y-2">
        {companies.map((c) => (
          <Card key={c.id}>
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{c.name}</p>
                <p className="font-mono text-sm text-muted-foreground">{c.slug}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge className={sourceBadgeClass(c.source)}>{c.source}</Badge>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    if (confirm(`Remove ${c.name}?`)) deleteMutation.mutate(c.id);
                  }}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
