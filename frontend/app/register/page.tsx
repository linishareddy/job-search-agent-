"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Radar } from "lucide-react";
import { toast } from "sonner";
import { authApi } from "@/lib/api";
import { parseApiError } from "@/lib/types/api";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const registerMutation = useMutation({
    mutationFn: () => authApi.register({ email: email.trim(), password, name: name.trim() || undefined }),
    onSuccess: (res) => {
      if (!res.data) return;
      login(res.data.access_token);
      toast.success("Account created");
      router.push("/dashboard");
    },
    onError: (err) => toast.error(parseApiError(err)),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    registerMutation.mutate();
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden mesh-bg px-6">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/15">
            <Radar className="h-5 w-5 text-primary" />
          </div>
          <span className="text-lg font-semibold">Job Radar</span>
        </Link>

        <div className="rounded-2xl border border-border bg-card/80 p-6 shadow-glow backdrop-blur">
          <h1 className="text-xl font-semibold">Create your account</h1>
          <p className="mt-1 text-sm text-muted-foreground">Start hunting in one sentence</p>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <div>
              <Label htmlFor="register-name">Name (optional)</Label>
              <Input
                id="register-name"
                autoComplete="name"
                className="mt-1.5"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="register-email">Email</Label>
              <Input
                id="register-email"
                type="email"
                required
                autoComplete="email"
                className="mt-1.5"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="register-password">Password</Label>
              <Input
                id="register-password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                className="mt-1.5"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="mt-1.5 text-xs text-muted-foreground">At least 8 characters</p>
            </div>
            <Button type="submit" className="w-full gap-2" disabled={registerMutation.isPending}>
              {registerMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Create account
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
