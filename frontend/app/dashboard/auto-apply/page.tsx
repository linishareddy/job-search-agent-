"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Mail, Play, Sparkles, Zap } from "lucide-react";
import { toast } from "sonner";
import { autoApplyApi, authApi, resumesApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import { Skeleton } from "@/components/ui/skeleton";

export default function AutoApplyPage() {
  const queryClient = useQueryClient();
  const { user, isLoading: userLoading } = useAuth();

  const resumesQuery = useQuery({ queryKey: ["resumes"], queryFn: () => resumesApi.list() });
  const resumes = resumesQuery.data?.data ?? [];

  const [enabled, setEnabled] = useState(false);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [resumeId, setResumeId] = useState("");
  const [minScorePct, setMinScorePct] = useState(70);
  const [maxPerRun, setMaxPerRun] = useState(5);

  // Seed local form state once the user profile has loaded — a plain useState
  // initializer can't do this since `user` arrives asynchronously.
  useEffect(() => {
    if (!user) return;
    setEnabled(user.auto_apply_enabled);
    setEmailEnabled(user.email_enabled);
    setResumeId(user.auto_apply_resume_id ?? "");
    setMinScorePct(Math.round(user.auto_apply_min_score * 100));
    setMaxPerRun(user.auto_apply_max_per_run);
  }, [user]);

  const saveMutation = useMutation({
    mutationFn: () =>
      authApi.updateMe({
        auto_apply_enabled: enabled,
        email_enabled: emailEnabled,
        auto_apply_resume_id: resumeId || null,
        auto_apply_min_score: minScorePct / 100,
        auto_apply_max_per_run: maxPerRun,
      }),
    onSuccess: () => {
      toast.success("Preferences saved");
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const runMutation = useMutation({
    mutationFn: () => autoApplyApi.run(),
    onSuccess: (res) => {
      const prepared = res.data ?? [];
      if (prepared.length === 0) {
        toast.info("No new matches ready to prepare right now");
      } else {
        toast.success(`Prepared ${prepared.length} application(s) — check the Tracker`);
      }
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  const canEnable = resumes.length > 0;
  const isLoading = userLoading || !user;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Zap className="h-6 w-6 text-primary" />
          Auto-apply
        </h1>
        <p className="text-muted-foreground">
          Every 15 minutes we check your active searches for new high-match jobs, tailor a resume and
          cover letter for each, and queue them as &quot;Ready to apply&quot; — you review and submit yourself.
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
            <CardDescription>Applies to future scheduler runs and manual &quot;Run now&quot;.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <label className="flex items-center justify-between rounded-lg border border-border p-3">
              <div>
                <p className="text-sm font-medium">Enable auto-apply</p>
                <p className="text-xs text-muted-foreground">
                  {canEnable ? "Runs automatically every 15 minutes" : "Upload a resume first"}
                </p>
              </div>
              <input
                type="checkbox"
                className="h-5 w-5 accent-primary"
                checked={enabled}
                disabled={!canEnable}
                onChange={(e) => setEnabled(e.target.checked)}
              />
            </label>

            <label className="flex items-center justify-between rounded-lg border border-border p-3">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Email me updates</p>
                  <p className="text-xs text-muted-foreground">New job digests and auto-apply summaries</p>
                </div>
              </div>
              <input
                type="checkbox"
                className="h-5 w-5 accent-primary"
                checked={emailEnabled}
                onChange={(e) => setEmailEnabled(e.target.checked)}
              />
            </label>

            <div>
              <Label htmlFor="aa-resume">Resume to use</Label>
              {resumes.length === 0 ? (
                <p className="mt-1.5 text-sm text-muted-foreground">
                  <Link href="/dashboard/resume" className="text-primary hover:underline">
                    Upload a resume
                  </Link>{" "}
                  to enable auto-apply.
                </p>
              ) : (
                <NativeSelect
                  id="aa-resume"
                  className="mt-1.5 w-full"
                  value={resumeId}
                  onChange={(e) => setResumeId(e.target.value)}
                >
                  <option value="">Select a resume…</option>
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.filename}
                    </option>
                  ))}
                </NativeSelect>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="aa-min-score">Minimum match score</Label>
                <div className="mt-1.5 flex items-center gap-2">
                  <Input
                    id="aa-min-score"
                    type="number"
                    min={0}
                    max={100}
                    value={minScorePct}
                    onChange={(e) => setMinScorePct(Number(e.target.value))}
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>
              <div>
                <Label htmlFor="aa-max-per-run">Max per run</Label>
                <Input
                  id="aa-max-per-run"
                  type="number"
                  min={1}
                  max={50}
                  className="mt-1.5"
                  value={maxPerRun}
                  onChange={(e) => setMaxPerRun(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <Button className="gap-2" disabled={saveMutation.isPending} onClick={() => saveMutation.mutate()}>
                {saveMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Save preferences
              </Button>
              <Button
                variant="outline"
                className="gap-2"
                disabled={runMutation.isPending || !canEnable}
                onClick={() => runMutation.mutate()}
              >
                {runMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Run now
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="flex items-center gap-3 p-4">
          <Sparkles className="h-5 w-5 shrink-0 text-primary" />
          <p className="text-sm text-muted-foreground">
            Prepared applications land in your{" "}
            <Link href="/dashboard/tracker" className="font-medium text-primary hover:underline">
              Tracker
            </Link>{" "}
            under the &quot;Ready to apply&quot; column, with the tailored resume and cover letter attached.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
