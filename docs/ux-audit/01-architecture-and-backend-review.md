[← back to index](00-executive-summary-and-methodology.md)

# 1. Architecture Overview

## 1.1 Frontend
Next.js 15 App Router + React 19 + TypeScript. Route tree under `frontend/app/`:

```
app/
├─ page.tsx                                  landing page
├─ providers.tsx                             React Query + next-themes
└─ dashboard/
   ├─ layout.tsx                             wraps children in DashboardShell
   ├─ page.tsx                               searches list (home)
   ├─ new/page.tsx                           new-search form
   ├─ companies/page.tsx                     ATS watchlist CRUD
   ├─ resume/page.tsx                        resume upload/list
   ├─ tracker/page.tsx                       application board
   ├─ notifications/page.tsx                 notification feed
   └─ searches/[id]/
      ├─ page.tsx → search-detail-client.tsx results/filters/pipeline
      ├─ edit/page.tsx                       edit search config
      └─ analytics/page.tsx                  Recharts insights
```
`[GAP]` No `loading.tsx`, `error.tsx`, or `not-found.tsx` anywhere in the tree — every loading/error/empty state is hand-rolled per page via React Query's `isLoading`/`isError` (consistently, see `02-screens-ux-search-experience.md`), but an actual render-time throw would fall through to Next's default (unbranded) error overlay rather than app UI.

Data layer: `lib/api/*` (typed fetch wrappers, one module per resource), `lib/types/*`, `@tanstack/react-query` for all server state — no global client-state store (Redux/Zustand); component-local `useState` for forms. This is proportionate to the app's size — introducing a state library would be over-engineering at this scale (see `05-recommendations-backlog-and-appendices.md` §3 "not worth it").

Styling: Tailwind 3.4 + an HSL CSS-variable token layer (`app/globals.css:6-49`) + 7 shadcn-style primitives (`components/ui/`). Full inventory in `03-design-system-motion-ai-states.md` §1.

## 1.2 Backend
FastAPI with a clean layered split — `routes/ → controllers/ → services/ → repositories/ → models/`, plus `schemas/` (Pydantic), `core/response.py` (envelope), `exceptions/handlers.py`, `config/` (settings, database, logging, scheduler), `services/pipeline/` (orchestrator, dedup, scoring, enrichment, fetcher) and `services/fetchers/{adzuna,jooble,remotive,greenhouse,lever,ashby}_fetcher.py`. This is a well-organized layering for a solo project — no architectural rework recommended here; `AUDIT_REPORT.md` already tracks the correctness bugs inside this pipeline (dedup, ATS fetchers, etc.).

Database: SQLAlchemy 2.0 async ORM. `[REVIEW]` Schema provenance is split three ways — Alembic migrations (`alembic/versions/001-006`) exist but per `AUDIT_REPORT.md` have never actually been run/stamped against the live DB; the live schema instead comes from `Base.metadata.create_all` plus hand-written `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements executed at every boot (`main.py:19-27`, explicitly commented as `# TEMP` mirrors of migrations 002-004). This is a correctness/ops risk already implicitly covered by `AUDIT_REPORT.md`'s H9; flagged here only because it also means **indexes defined in the Alembic files are never guaranteed to exist on the running database** — see §2.6.

# 2. Backend Production-Readiness Review

*(New findings only — not a re-run of `AUDIT_REPORT.md`'s correctness backlog.)*

## 2.1 API surface
7 routers mounted under `/api/v1` (`main.py:48-54`):

| Router | Endpoints |
|---|---|
| `searches` | `GET/POST /searches`, `POST /parse-text`, `POST /from-text`, `GET/PUT/DELETE /{id}`, `POST /{id}/run`, `GET /{id}/results`, `GET /{id}/analytics` |
| `notifications` | `GET /`, `PATCH /{id}/read`, `DELETE /{id}` |
| `jobs` | `POST /{job_id}/cover-letter` |
| `applications` | `GET/POST /`, `PATCH/DELETE /{id}` |
| `companies` | `GET/POST /`, `DELETE /{id}` |
| `resumes` | `GET/POST /`, `POST /extract-text`, `GET/DELETE /{id}` |
| `health` | `GET /`, `GET /sources` |

`[REVIEW]` Mostly consistent REST (plural nouns, correct verb→method mapping, 201/204/202 used appropriately). One inconsistency: `searches` update uses `PUT` (`routes/searches.py:67`, full replace) while the structurally-identical `applications` update uses `PATCH` (`routes/applications.py:28`, partial) — same shape of operation, different HTTP semantics across two otherwise-parallel resources. **Low severity, but cheap to fix** (standardize both on `PATCH`, since both routes actually accept partial payloads in practice).

## 2.2 Pagination
`[GAP]` Only one endpoint is paginated: `GET /searches/{id}/results` (`routes/searches.py:100-101`, real `offset()/limit()` in `repositories/job_repository.py:136-169`). Every other list endpoint returns its entire table unbounded: `notifications` (`routes/notifications.py:13-20`), `applications` (`routes/applications.py:14-18`), `companies` (`routes/companies.py:14-18`), `resumes` (`routes/resumes.py:13-17`), `searches` (`routes/searches.py:15-21`). Harmless today at 1-5 users and low row counts, but notifications in particular accumulate one row per new-job burst per search — this is the cheapest list to grow unbounded, and the cheapest to paginate now while the pattern from `job_repository.py` can just be copied.

## 2.3 Rate limiting
`[GAP]` None. No `slowapi`, no custom throttling middleware, no `middleware/` directory. `main.py` registers only `CORSMiddleware` and exception handlers. Every Groq-backed endpoint (`/searches/parse-text`, `/searches/{id}/run`, `/jobs/{id}/cover-letter`) can be hit unboundedly — a double-click on "Preview with AI" or "Run now" (both visible in the new-search screenshot / `search-detail-client.tsx:181-190`) fires a second concurrent Groq call with no debounce on either the client or server. This is a real-money/quota concern, not just a theoretical one, given Groq usage is billed.

## 2.4 Logging & monitoring
`[REVIEW]` `config/logging.py:7-20` — plain-text `logging.basicConfig`, stdout only, no structured/JSON output, no request/correlation ID, no request-logging middleware. `GET /health` and `GET /health/sources` (`routes/health.py:12-33`) give a basic DB-liveness + per-source freshness check, but nothing checks Groq reachability, embedding-model load state, or scheduler liveness — so "the AI features silently stopped working" has no dedicated signal. Combined with the scheduler's log-only error handling (§2.6), a failed search only surfaces as a line in a log file the user has to go find — there's no in-app surface for "your last run failed and here's why," which is a real, user-visible support gap on top of being an ops gap.

## 2.5 Caching
`[REVIEW]` No general caching layer (no Redis, no HTTP cache headers). Two narrow, deliberate exceptions exist: `@lru_cache(maxsize=1)` memoizing the sentence-transformer model load (`services/embedding_service.py:12` — process-wide, not a data cache) and a domain-specific 24h TTL cache for Groq field-expansion results stored on `saved_search.field_expansion_cache` (`models/saved_search.py:36-37`, consumed in `orchestrator.py:170-188`). Both are appropriately scoped; no general-purpose cache is missing at this scale.

## 2.6 Database indexing
`[REVIEW]` Indexes exist only in the Alembic migration file (`alembic/versions/001_initial_schema.py`), not mirrored via `index=True`/`Index(...)` in the ORM models themselves — and per §1.2, the migration may never have actually run against the live DB, so there's no guarantee these indexes exist at runtime at all. Present-in-migration: `idx_job_fingerprint` (unique, `:86`), `idx_job_posted` (`:87`), `idx_job_company` (`:88`), `idx_job_embedding` ivfflat (`:89-91`), `idx_search_run_search` (`:105`), `idx_jsr_search_score` (`:121`), partial `idx_jsr_new` (`:122-125`), `idx_notification_read` (`:137`), partial `idx_saved_search_active` (`:46`). Missing even in the migration: an index on `job.source` (grouped on in the hot `health.py:26-32` query), on `job_search_result.run_id` FK (`models/job_search_result.py:20`), on `notification.search_id`/`run_id` FKs (`models/notification.py:15-16`), and on `search_run.status`/`started_at` despite the scheduler filtering by due-status every tick.

## 2.7 N+1 query risk
`[REVIEW]` `services/pipeline/orchestrator.py:130-146` loops over up to ~30 enriched jobs per run, issuing 2 sequential DB round-trips per job (`job_repo.upsert_job:131`, `job_repo.upsert_search_result:136-146`) instead of one bulk `INSERT ... ON CONFLICT`. Bounded (≤30 rows, once per 30-minute scheduler tick per active search) — real but not urgent. Read paths are clean: `get_results_for_search` uses `selectinload` + a single count query (`job_repository.py:158-172`); the analytics query is one join (`:114-124`).

## 2.8 Search indexing (pgvector)
`[REVIEW]` `job.embedding` is `Vector(384)` (`models/job.py:42`) with an ivfflat/cosine index defined in the migration (`001_initial_schema.py:89-91`) — but **nothing in the codebase queries through it**. `EmbeddingService.cosine_similarity` (`embedding_service.py:31-38`) is pure NumPy; every consumer (`resume_match_service.py:43-45`, `dedup_service.py:115`, `scoring_service.py:80-84`) pulls full `Job` rows into Python and computes similarity in-process. The ANN index is dead weight — all "vector search" today is an O(n) in-memory scan over whatever rows another filter already fetched. Not urgent at current row counts, but worth flagging as architecture debt before job volume grows, since the fix (`ORDER BY embedding <=> :query_vec LIMIT k` at the SQL layer) is a moderate rewrite, not a config toggle.

## 2.9 Security
`[REVIEW]` `main.py:38-44`: `allow_origins=["*"]` combined with `allow_credentials=True` — browsers reject this combination outright for credentialed requests, and it signals no real origin allowlist exists at all; `allow_methods=["*"]`/`allow_headers=["*"]` are similarly maximally permissive. `config/settings.py:9` ships a non-secret dev default `postgres_password: str = "jobsearch"` that would silently work in production if an env var isn't set — low risk given this is a single local instance, but worth tightening since it's a one-line fix (require the env var, no default). No auth on any route — already tracked as `AUDIT_REPORT.md` §C9, not re-litigated here.

## 2.10 Error handling
`[REVIEW]` `exceptions/handlers.py` registers `NotFoundError`→404, `ValidationError`→422, catch-all `Exception`→500, all shaped as `{"success": false, "message": str}`; `core/response.py:8-18`'s `ok()` returns `{"success", "data", "message", "total", "page", "page_size"}` with `exclude_none=True`. Applied consistently everywhere — every route uses `ok(...)` and the two custom exceptions rather than ad hoc `HTTPException`. One inconsistency: FastAPI's *native* request-validation 422s (malformed JSON, missing required fields) have a different body shape than handler-raised `ValidationError` 422s, since the two paths aren't reconciled — `lib/api/client.ts`'s `parseApiError` (see `03-design-system-motion-ai-states.md` §1) already defensively checks both `body.message` and `body.detail`, so the frontend degrades gracefully, but the inconsistency is still worth closing at the source.

# 3. Performance Review (Frontend + Backend)

**Backend:** the scheduler (`config/scheduler.py:31-41`) runs due searches **sequentially**, one at a time, each with its own `AsyncSessionLocal()` and an explicit `await asyncio.sleep(2)` between runs "to stagger Groq calls" (`:39`) — deliberate and reasonable at 1-5 users/searches, but it means total tick duration scales linearly with the number of active searches; worth revisiting only if the user base grows past the PRD's stated ceiling. The N+1 upsert loop (§2.7) is the other backend hot spot, bounded to ~30 rows/run.

**Frontend:** no code-splitting/virtualization concerns exist yet — list sizes (searches, jobs-per-page at 20, notifications, applications) are all small enough that this isn't a real bottleneck. The one thing worth doing regardless of scale: `search-detail-client.tsx:66-78` re-queries `search-results` on every `page`/`onlyNew`/`postedDays`/`resumeId` change with `refetchInterval: isPolling ? 5000 : false` (`:77`) — reasonable, but combined with the 3-minute polling timeout (`:124`, `180_000`ms) and no visible "still working, this can take a few minutes" framing beyond the fake `PipelineProgress` bar (see `03-design-system-motion-ai-states.md` §4), a slow real pipeline run reads to the user as either "stuck" or "silently gave up" once the fake progress bar completes before real data arrives — a perceived-performance problem more than an actual one. Addressed in `04-benchmarking-and-roadmap.md` §16.
