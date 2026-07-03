import Link from "next/link";
import { ArrowRight, Radar, Sparkles, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden mesh-bg">
      <header className="flex items-center justify-between px-6 py-5 md:px-10">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/15">
            <Radar className="h-5 w-5 text-primary" />
          </div>
          <span className="text-lg font-semibold">Job Radar</span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link href="/dashboard">
            <Button variant="outline">Dashboard</Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 pb-20 pt-16 text-center md:pt-24">
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-card/80 px-4 py-1.5 text-sm text-muted-foreground backdrop-blur">
          <Sparkles className="h-4 w-4 text-primary" />
          AI-powered · 6 job sources · US roles
        </p>
        <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
          Your personal <span className="text-gradient">job radar</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
          Describe the role you want in plain English. We hunt across Adzuna, Jooble, Remotive,
          and company career pages — then rank matches with AI explanations.
        </p>

        <div className="mx-auto mt-10 max-w-2xl">
          <Link href="/dashboard/new">
            <div className="group rounded-2xl border border-border bg-card/80 p-2 shadow-glow backdrop-blur transition hover:border-primary/40">
              <div className="flex items-center gap-3 rounded-xl bg-background px-4 py-4 text-left text-muted-foreground">
                <span className="flex-1 text-sm md:text-base">
                  e.g. Remote senior software engineer, Python backend, 150k+
                </span>
                <ArrowRight className="h-5 w-5 text-primary transition group-hover:translate-x-0.5" />
              </div>
            </div>
          </Link>
          <Link href="/dashboard/new" className="mt-6 inline-block">
            <Button size="lg" className="gap-2">
              Start hunting <Zap className="h-4 w-4" />
            </Button>
          </Link>
        </div>

        <div className="mt-20 grid gap-6 md:grid-cols-3">
          {[
            { title: "Type one sentence", desc: "No forms. Groq parses title, domain, salary, and work mode." },
            { title: "6 sources at once", desc: "Job boards plus Greenhouse, Lever, and Ashby company pages." },
            { title: "Explained matches", desc: "Every job gets a relevance score, match reason, and gaps." },
          ].map((f) => (
            <div key={f.title} className="rounded-xl border border-border bg-card/60 p-6 text-left backdrop-blur">
              <h3 className="font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
