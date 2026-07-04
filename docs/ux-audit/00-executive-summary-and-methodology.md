# Job Radar — Staff-Level UX / Product / Motion Design Audit

**Date:** 2026-07-04
**Scope:** Full literal pass over the 20-deliverable staff-engineering / product-design / UX / motion-design review template, applied to the actual Job Radar codebase.
**Form:** Written audit report. No code was changed to produce this document.
**Relationship to prior work:** [`AUDIT_REPORT.md`](../../AUDIT_REPORT.md) (2026-07-03) is the correctness-bug backlog for this app (cross-search blindness, `is_new` never clearing, no auth, etc.). This audit is deliberately **separate** — it covers UX, product, visual design, motion, accessibility, and benchmarking. Where a correctness bug has a direct UX consequence, it is cross-referenced, not re-litigated.

## What this app actually is

Job Radar is a **personal job-alert tool for 1–5 users** (`PRD.md:47`: *"personal tool, not a commercial platform"*). It has no authentication (tracked separately as `AUDIT_REPORT.md` §C9) and, per the PRD, no per-user data isolation — functionally a single shared instance. This fact is load-bearing for the whole audit: it's the reason §14 (benchmarking) explicitly rejects most multi-tenant/collaboration patterns from the products named in the request, and why the recommendations in `05-recommendations-backlog-and-appendices.md` are sized for a solo maintainer, not a team.

Stack, confirmed by direct reads:
- **Backend:** FastAPI, layered `routes/ → controllers/ → services/ → repositories/ → models/`, SQLAlchemy 2.0 async + Alembic + Postgres/pgvector, Groq for LLM calls, local MiniLM embeddings, APScheduler for a single polling job.
- **Frontend:** Next.js 15 (App Router) + React 19 + TypeScript, Tailwind CSS 3.4, shadcn-style local primitives (`components/ui/`), `next-themes` (dark default, light supported), `lucide-react` icons, `sonner` toasts, `framer-motion` installed.
- **11 real screens:** landing, dashboard home (searches list), new-search, companies (ATS watchlist), resume, tracker (Kanban-styled application board), notifications, search detail, search edit, search analytics — enumerated with layout notes in `02-screens-ux-search-experience.md`.

## Method

Every finding in this audit traces to a specific `file:line` obtained by directly reading the source (not inferring from summaries) — file, component, and backend reads covered all 11 screens, all `components/ui/*` primitives, all feature components, `lib/utils.ts`, `lib/api/client.ts`, `globals.css`, `tailwind.config.ts`, and the backend's routing, scheduler, CORS, and model layers. The one screenshot supplied by the user (the "New Search" page) was cross-checked line-for-line against `app/dashboard/new/page.tsx` — every element in it (the placeholder copy, the disabled button states, the "Groq" mention) traces to an exact line, confirmed in `02-screens-ux-search-experience.md`. A live dev-server pass was considered but skipped in favor of this source-level verification: the disabled-state logic, motion (or its absence), and copy are all deterministic from the JSX/CSS actually read, and the user's own screenshot already served as a real-environment check for the one screen photographed. Screens without a supplied screenshot (companies, resume, tracker, notifications, analytics) are reviewed from JSX structure — this is noted per-section as a limitation where real font rendering or computed contrast would materially change a judgment call.

## Confidence legend

Every finding below is tagged so aspiration is never mistaken for a bug report:

| Tag | Meaning |
|---|---|
| `[REVIEW]` | Critiques code that exists today. Always cites `file:line`. |
| `[GAP]` | Something the target quality bar (this template) implies is missing, stated neutrally — not a defect, an absence. |
| `[PRESCRIPTIVE]` | A target-state design proposal for something that has **no code today**. Every prescriptive section opens with an explicit disclaimer banner. Confined to `04-benchmarking-and-roadmap.md` §15–17. |

## How the 20 requested deliverables map to these files

| # | Deliverable (from the request) | Where it lives |
|---|---|---|
| 1 | Architecture review | `01-architecture-and-backend-review.md` §1 |
| 2 | Full UI review (every screen) | `02-screens-ux-search-experience.md` §1 |
| 3 | Full UX audit | `02-screens-ux-search-experience.md` §1–3 |
| 4 | Motion design specification | `03-design-system-motion-ai-states.md` §3 (current) + `04-benchmarking-and-roadmap.md` §17 (target) |
| 5 | Animation spec per interactive component | `03-design-system-motion-ai-states.md` §5 (component checklist) |
| 6 | AI loading system specification | `03-design-system-motion-ai-states.md` §4 (current) + `04-benchmarking-and-roadmap.md` §16 (target) |
| 7 | Backend improvement roadmap | `01-architecture-and-backend-review.md` §2 |
| 8 | Frontend improvement roadmap | `05-recommendations-backlog-and-appendices.md` §1 |
| 9 | Accessibility checklist | `03-design-system-motion-ai-states.md` §6 |
| 10 | Mobile optimization roadmap | `02-screens-ux-search-experience.md` §3 (nav) + recs in `05-*.md` |
| 11 | Search history architecture | `04-benchmarking-and-roadmap.md` §15 |
| 12 | Kanban interaction specification | `02-screens-ux-search-experience.md` §1.6 (Tracker, current) + rec REC-05 |
| 13 | Design system specification | `03-design-system-motion-ai-states.md` §1–2 |
| 14 | Component-by-component implementation checklist | `03-design-system-motion-ai-states.md` §5 |
| 15 | Performance optimization roadmap | `01-architecture-and-backend-review.md` §3 |
| 16 | Visual consistency audit | `03-design-system-motion-ai-states.md` §2 |
| 17 | Icon consistency audit | `03-design-system-motion-ai-states.md` §1 (folded in, not standalone — see note below) |
| 18 | Alignment and spacing audit | `03-design-system-motion-ai-states.md` §1 (folded in, not standalone — see note below) |
| 19 | Naming cleanup plan | `02-screens-ux-search-experience.md` §1.1/1.3 findings + REC-01 |
| 20 | Prioritized implementation roadmap | `05-recommendations-backlog-and-appendices.md` §1–2 |

**Why icon/spacing audits aren't standalone sections:** across all 11 screens, icon sizing (`lucide-react`, consistently `h-3`/`h-3.5`/`h-4`/`h-5` by hierarchy) and spacing (`gap-2`/`gap-3`/`gap-4`, `p-4`/`p-5`/`p-6`) are genuinely consistent system-wide — see `03-design-system-motion-ai-states.md` §1 for the one-time systemic finding. A standalone section would otherwise repeat "consistent, no issue" 11 times.

## File index

1. [`00-executive-summary-and-methodology.md`](00-executive-summary-and-methodology.md) — this file
2. [`01-architecture-and-backend-review.md`](01-architecture-and-backend-review.md) — architecture, backend production-readiness, performance
3. [`02-screens-ux-search-experience.md`](02-screens-ux-search-experience.md) — per-screen UI/UX, search journey, navigation/IA
4. [`03-design-system-motion-ai-states.md`](03-design-system-motion-ai-states.md) — design tokens, consistency audit, motion (current), AI-loading states (current), component checklist, accessibility
5. [`04-benchmarking-and-roadmap.md`](04-benchmarking-and-roadmap.md) — benchmarking vs. 12 named products, 3 prescriptive specs (search history, AI streaming, motion-token completion)
6. [`05-recommendations-backlog-and-appendices.md`](05-recommendations-backlog-and-appendices.md) — master recommendation table, severity×effort matrix, file index, glossary, "not worth it at this scale"
