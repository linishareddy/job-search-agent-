[← back to index](00-executive-summary-and-methodology.md)

# 1. Master Recommendations

Full template applied to the 20 highest-leverage recommendations surfaced across files 01-04. Effort is a **solo-dev rubric**: S = under 2 hours, M = a half-day, L = multi-day. "Libraries" flags whether something new needs installing or whether the fix reuses what's already in `package.json`/`requirements`.

### Naming & Trust

**REC-01 — Remove technical-naming leaks from user-facing copy**
*Why:* A personal tool marketing itself as "just describe the job" undercuts that promise by naming its LLM vendor in the same breath. *Impact:* Small but real — the two lines are the only overt breaks in an otherwise consumer-friendly voice. *Approach:* Replace `app/page.tsx:57`'s "Groq parses..." with "AI parses..."; replace `app/dashboard/new/page.tsx:173`'s "one Groq call" with "one quick AI pass." *Libraries:* none. *Effort:* S. *Risk:* none. *Screens:* Landing, New Search. *Before → After:* "No forms. Groq parses title, domain..." → "No forms. AI parses title, domain..."; "Preview is optional — one Groq call when you click" → "Preview is optional — takes a few seconds."

**REC-04 — Replace the fake `PipelineProgress` timer with a real backend-driven signal**
*Why:* The current implementation can show "complete" while the real pipeline is still running, or churn through steps unrelated to actual backend state (`search-detail-client.tsx:110-115`) — this is the audit's single highest-severity finding because it's an existing feature actively misleading users, not an absent one. *Impact:* Restores trust in the one moment users are asked to wait. *Approach:* have `PipelineOrchestrator.run()` write its current stage to the `search_run` row after each step; have the frontend's existing 5s poll read that field instead of driving a local `setInterval`. *Libraries:* none — reuses existing poll infrastructure. *Effort:* S–M. *Risk:* none beyond normal regression risk. *Mitigation:* the 11 step labels (`search-filters.tsx:6-18`) already exist and don't need to change, only their trigger. *Screens:* Search Detail. *Before → After:* step advances every 4s regardless of reality → step advances only when the orchestrator actually completes that stage.

**REC-09 — Add token streaming to AI-generated responses**
*Why:* Both `ParsedIntentPreview` and `CoverLetterDialog` currently paint their full result in one frame after a spinner — the literal "AI loading experience" ask in the original request, and the one place a genuinely more premium feel is cheaply available given Groq supports `stream=True` natively. *Impact:* Medium — makes the app's two AI "moments" feel materially faster and more alive without any model-quality change. *Approach:* backend: call Groq with `stream=True`, proxy via FastAPI `StreamingResponse`; frontend: consume via `fetch()` + `ReadableStream`, append tokens to state. *Libraries:* none new — `StreamingResponse` is built into FastAPI, `ReadableStream` is a browser API. *Effort:* M–L (touches both layers). *Risk:* partial-response error handling (what if the stream drops mid-token). *Mitigation:* fall back to today's non-streaming call path on stream error — cheap since that path is what exists now. *Screens:* New Search (parse), Job Card / Cover Letter Dialog. *Before → After:* spinner → full card/letter in one paint, vs. words appearing progressively as Groq generates them.

### Design System & Consistency

**REC-06 — Build a real Dialog primitive; replace hand-rolled overlay and all `confirm()` calls**
*Why:* `CoverLetterDialog` has no `role="dialog"`, `aria-modal`, focus trap, or `Escape` handler (`cover-letter-dialog.tsx:52-59`) — a keyboard/screen-reader user cannot properly perceive or dismiss it. Meanwhile 4 separate call sites use blocking, unstyled `window.confirm()` for destructive actions. *Impact:* High for accessibility (the one real WCAG blocker in the app); moderate for polish (removes 4 jarring native browser dialogs). *Approach:* build one accessible `<Dialog>` (focus trap, `Escape`-to-close, `aria-modal`, backdrop click-to-close preserved from the existing pattern), refactor `CoverLetterDialog` onto it, then add one `<ConfirmDialog>` built on the same primitive replacing `companies/page.tsx:160`, `resume/page.tsx:99`, `tracker/page.tsx:55`, `search-detail-client.tsx:213`. *Libraries:* Radix UI's unstyled `Dialog` primitive is the standard low-risk choice (handles focus trap/`Escape`/`aria` correctly out of the box) — new dependency, but a narrowly-scoped and well-established one; a hand-rolled focus trap is the zero-dependency alternative if avoiding new deps matters more. *Effort:* M. *Risk:* regressions in the one existing modal's current behavior (backdrop-click-to-close). *Mitigation:* preserve that behavior explicitly in the new primitive's default props. *Screens:* Cover Letter Dialog, Companies, Resume, Tracker, Search Detail.

**REC-07 — Fix Label/`htmlFor` pairing; group `FilterChips` for screen readers**
*Why:* 14 of 16 `<Label>` usages have no programmatic association with their control (confirmed by grep — only `new/page.tsx:197-199,207-209` pair correctly); `FilterChips` renders as unrelated buttons with no `role="group"`. *Impact:* Directly affects whether a screen-reader user can identify what a focused form field is for — the single most common and most fixable a11y gap in the app. *Approach:* add matching `id`/`htmlFor` pairs to the 14 remaining Company/Edit-Search fields (copy the exact pattern already correct on New Search); add `role="group" aria-label="{label}"` to `FilterChips`'s wrapper div (`search-filters.tsx:54`). *Libraries:* none. *Effort:* S. *Risk:* none. *Screens:* Companies, Search Edit, New Search (chips), Search Detail (chips). *Before → After:* label visually adjacent but unannounced → label announced on field focus.

**REC-08 — Add `aria-label` to the remaining icon-only buttons**
*Why:* Companies' and Resume's delete buttons (`companies/page.tsx:156-164`, `resume/page.tsx:95-103`) have no accessible name, while the functionally identical Notifications/Tracker delete buttons do — an inconsistency, not a systemic absence, and the fix is copy-paste from the Notifications reference implementation. *Impact:* Small scope, meaningful for the 2 affected screens. *Approach:* add `aria-label="Remove {name}"` matching the existing `tracker/page.tsx:57` pattern. *Libraries:* none. *Effort:* S. *Risk:* none. *Screens:* Companies, Resume.

**REC-12 — Consolidate duplicated filter-option constants**
*Why:* Work-mode, experience-level, and posted-within-days option lists are independently redefined on New Search, Edit Search, and Search Detail (`edit/page.tsx:19-34`, `new/page.tsx:23-28`, `search-detail-client.tsx:25-31`) and have already drifted — the posted-within set differs across all three screens with no stated reason. *Impact:* Prevents a class of "which screen has the right options" bugs before they compound further. *Approach:* extract one shared `lib/constants/filters.ts` module, import everywhere; reconcile the posted-within values deliberately (or document why they differ, if intentional). *Libraries:* none. *Effort:* S. *Risk:* behavior change if the current drift was actually intentional. *Mitigation:* confirm with whoever set the differing values before merging (a fast conversation, not a technical risk). *Screens:* New Search, Search Edit, Search Detail.

**REC-13 — Extract the triplicated native-`<select>` styling**
*Why:* Identical Tailwind class strings are hand-copied across `tracker/page.tsx:65-75`, `cover-letter-dialog.tsx:75-85`, `search-detail-client.tsx:262-276` — a maintenance smell (a future style tweak needs 3 edits), not an accessibility one (native `<select>` is accessible by default). *Impact:* Low user-facing impact, meaningful maintainability win. *Approach:* extract a shared `<NativeSelect>` wrapper in `components/ui/` mirroring the existing `Input`/`Textarea` wrapper pattern. *Libraries:* none. *Effort:* S. *Risk:* none. *Screens:* Tracker, Cover Letter Dialog, Search Detail.

### Motion

**REC-14 — Apply `AnimatePresence` + shared motion values to the 3 abrupt mount/unmount points**
*Why:* `job-card.tsx:34-37` already proves the app can do tasteful mount motion well; `ParsedIntentPreview` (the app's best "AI understood you" moment), `CoverLetterDialog`, and `PipelineProgress` all currently cut in/out with zero transition. *Impact:* The highest-visibility, lowest-risk motion improvement available — reuses an already-validated pattern rather than inventing a new one. *Approach:* wrap each in `<AnimatePresence>` + `<motion.div>` using the same `{opacity:0,y:12}→{opacity:1,y:0}` values already tuned in `job-card.tsx`; delete the dead `fade-in`/`slide-up` Tailwind keyframes (`tailwind.config.ts:58-71`) in the same change rather than leaving unused config behind. *Libraries:* `framer-motion` — already installed, zero new dependencies. *Effort:* S–M. *Risk:* none beyond visual regression, easily caught by eye. *Screens:* New Search, Job Card/Cover Letter Dialog, Search Detail.

**REC-20 — Add `prefers-reduced-motion` support**
*Why:* No reduced-motion handling exists anywhere; cheapest to build in now, before REC-14 adds more motion, than to retrofit later. *Impact:* Accessibility compliance for vestibular-disorder users; currently moot but won't stay moot once REC-14 ships. *Approach:* gate the new `AnimatePresence` transitions behind a `useReducedMotion()` check (framer-motion ships this hook natively). *Libraries:* none new. *Effort:* S. *Risk:* none. *Screens:* same as REC-14.

### Navigation & Mobile

**REC-11 — Add a mobile navigation drawer**
*Why:* 4 of 6 sections (Searches home, Companies, Resume, Tracker) are unreachable on mobile except by typing a URL directly — `dashboard-shell.tsx:43`'s sidebar is `hidden md:flex` with no replacement. *Impact:* High for any mobile usage at all — currently mobile is close to unusable for anything but creating a new search or checking notifications. *Approach:* add a hamburger-triggered slide-in drawer reusing the existing `NAV` array (`dashboard-shell.tsx:21-28`) — no new navigation model needed, just a mobile-visible way to reach the one that exists. *Libraries:* `framer-motion` (already installed) for the slide-in; no new dependency required. *Effort:* M. *Risk:* none significant. *Screens:* `DashboardShell` (global).

**REC-15 — Add one keyboard shortcut (`Cmd+K` → New Search)**
*Why:* Zero keyboard shortcuts exist anywhere in the app; New Search is the single most common action, and a global shortcut is the cheapest "feels fast" win available. *Impact:* Small but real for any keyboard-first user. *Approach:* a single `useEffect` + `keydown` listener at the `DashboardShell` level routing to `/dashboard/new`. *Libraries:* none. *Effort:* S. *Risk:* none. *Screens:* `DashboardShell` (global).

### Backend Production-Readiness

**REC-02 — Fix the CORS wildcard + credentials misconfiguration**
*Why:* `main.py:38-44`'s `allow_origins=["*"]` + `allow_credentials=True` is an invalid combination per the CORS spec (browsers reject credentialed wildcard-origin requests) and signals no real origin allowlist exists. *Impact:* Low urgency at zero real users beyond the developer, but a one-line fix that removes a standing misconfiguration before it matters. *Approach:* set `allow_origins` to the actual frontend origin(s) via an env var. *Libraries:* none. *Effort:* S. *Risk:* breaks local dev if the origin list is wrong. *Mitigation:* include `localhost:3000` explicitly in the env-var default. *Screens:* n/a (backend).

**REC-03 — Add rate limiting to Groq-backed endpoints**
*Why:* `/parse-text`, `/{id}/run`, `/{job_id}/cover-letter` have no throttling — a double-click or an accidental repeated request burns paid Groq quota with no guardrail. *Impact:* Direct cost protection. *Approach:* add `slowapi` (or a simple in-memory token-bucket given single-instance deployment) on the three Groq-touching routes specifically, not globally. *Libraries:* `slowapi` — new, small, FastAPI-native dependency. *Effort:* S–M. *Risk:* over-throttling a legitimate rapid-retry. *Mitigation:* set a generous per-minute ceiling (this is guardrail, not traffic shaping). *Screens:* n/a (backend).

**REC-16 — Paginate the remaining unbounded list endpoints**
*Why:* Notifications, applications, companies, resumes, and searches all return their full table with no limit — harmless today, cheapest to fix while row counts are still small. *Impact:* Prevents a future slow-list bug rather than fixing a current one. *Approach:* copy the existing `offset()/limit()` pattern already implemented for search results (`job_repository.py:136-169`) onto the other four repositories. *Libraries:* none. *Effort:* S. *Risk:* none. *Screens:* n/a (backend), consumed by Notifications/Tracker/Companies/Resume pages.

**REC-17 — Move similarity search to SQL-level pgvector operators**
*Why:* The ivfflat index on `job.embedding` (`001_initial_schema.py:89-91`) is defined but never queried through — every similarity computation (`resume_match_service.py`, `dedup_service.py`, `scoring_service.py`) pulls full rows into Python and computes cosine similarity via NumPy instead. *Impact:* Architecture debt that doesn't hurt yet but will as job volume grows — the fix is a moderate rewrite, not a toggle, so it's cheaper to do before it's urgent. *Approach:* rewrite the relevant repository queries to use `ORDER BY embedding <=> :query_vec LIMIT k` at the SQL layer. *Libraries:* none new — `pgvector`'s SQLAlchemy integration is already in use for the column type. *Effort:* M. *Risk:* behavior differences between in-process and SQL-level cosine distance at edge cases. *Mitigation:* compare outputs on a sample before switching over fully. *Screens:* n/a (backend).

**REC-18 — Add structured logging + correlation IDs, especially around scheduler failures**
*Why:* The scheduler's per-search failures are logged and silently swallowed (`config/scheduler.py:40-41`) with no user-visible surface — "why didn't my search update" currently has no debugging path short of reading server logs. *Impact:* Directly closes the support gap named in `01-*.md` §2.4. *Approach:* switch `logging.basicConfig`'s formatter to structured JSON, add a per-run correlation ID (the existing `search_run.id` is already a natural one), and surface the last-run error message on the Search Detail page if the most recent `search_run.status` is `failed`. *Libraries:* none required (Python's standard `logging` supports a JSON formatter without new deps; `python-json-logger` is a small optional convenience). *Effort:* S–M. *Risk:* none. *Screens:* Search Detail (surfacing), backend logging config.

**REC-19 — Increase icon-only button touch target toward 44px**
*Why:* `button.tsx:20`'s `icon` size variant is `h-9 w-9` (36px), under the commonly-cited 44px minimum touch target, and applies to every icon-only button in the app. *Impact:* Small, real improvement for mobile/touch usability. *Approach:* either bump the variant to `h-11 w-11` or keep the visual icon size and add invisible hit-slop padding. *Libraries:* none. *Effort:* S. *Risk:* visual density change on desktop. *Mitigation:* use hit-slop padding rather than growing the visible button if desktop density matters more. *Screens:* global (any icon-only button).

### Kanban

**REC-05 — Add real drag-and-drop to the Tracker board**
*Why:* The screen already visually promises "Kanban" (icon + copy, `tracker/page.tsx:4,128`) but status changes happen via a `<select>` dropdown — the single largest gap between metaphor and mechanic found in this audit, and the one benchmarking pull explicitly justified in §14. *Impact:* High relative to effort — this is the one interaction pattern users are likely to expect on sight and not find. *Approach:* introduce `@dnd-kit/core` + `@dnd-kit/sortable` (accessible, actively maintained, the current standard choice over the unmaintained `react-beautiful-dnd`), wire drag-between-columns to the existing `applicationsApi.update` mutation already used by the `<select>` today — the backend call doesn't change, only the trigger. Keep the `<select>` as a keyboard-accessible fallback rather than removing it (`@dnd-kit` supports keyboard sensors too, so this can eventually be one unified interaction, but shipping both is the lower-risk first step). *Libraries:* `@dnd-kit/core`, `@dnd-kit/sortable` — new dependency, but purpose-built and the modern standard for this exact use case. *Effort:* M. *Risk:* drag interactions are easy to get subtly wrong (drop targets, touch support). *Mitigation:* keep the `<select>` fallback live during and after rollout rather than a hard cutover. *Screens:* Tracker.

**REC-10 — Add save-confirmation feedback to the Tracker notes field**
*Why:* The notes `<textarea>` (`tracker/page.tsx:77-84`) saves `onBlur` with zero visible confirmation, unlike every other mutation in the app which calls `toast.success(...)`. *Impact:* Small but concrete — closes the one silent-save gap in an otherwise consistently-toasted app. *Approach:* add `toast.success("Note saved")` to the existing `updateMutation.onSuccess` handler — the mutation already exists, this is a one-line addition. *Libraries:* none — `sonner` already in use everywhere else. *Effort:* S. *Risk:* none. *Screens:* Tracker.

# 2. Supplementary Findings (condensed)

Everything below was noted in files 01-04 but doesn't warrant a standalone full-template entry — grouped by theme, each row is one fix regardless of how many instances it covers.

| ID | Finding | Section | Severity | Effort | Fix |
|---|---|---|---|---|---|
| SF-01 | `searches` uses PUT, `applications` uses PATCH for structurally identical update operations | `01-*.md` §2.1 | Low | S | Standardize both on PATCH |
| SF-02 | `SearchCardWithCount` fires one extra query per search card for a result count | `02-*.md` §1.2 | Low | S | Return count inline on `GET /searches` |
| SF-03 | Default dev Postgres password (`"jobsearch"`) silently works if env var unset | `01-*.md` §2.9 | Low | S | Require the env var, no default |
| SF-04 | FastAPI's native validation-422 shape differs from handler-raised `ValidationError`-422 shape | `01-*.md` §2.10 | Low | S | Reconcile both onto one envelope |
| SF-05 | `NotificationBell` polls every 30s regardless of tab visibility | `02-*.md` §1.7 | Low | S | Pause on `visibilitychange`/blur |
| SF-06 | Landing-page CTA "input" is a styled `<Link>`, not an actual typable field | `02-*.md` §1.1 | Low | M | Real textarea carrying text forward via query param |
| SF-07 | Brand mark in sidebar/mobile header isn't a link to dashboard home | `02-*.md` §3 | Low | S | Wrap in `<Link href="/dashboard">` |
| SF-08 | Search Edit's loading state is a generic pulse block, not form-shaped | `02-*.md` §1.9 | Low | S | Swap for a form-shaped skeleton |
| SF-09 | `--warning`/`--success` tokens used as both 15%-opacity badge backgrounds and plain text color without a contrast check | `03-*.md` §6 | Medium | S | Run axe/Lighthouse contrast check, adjust if needed |
| SF-10 | Missing DB indexes on `job.source`, `job_search_result.run_id`, `notification.search_id`/`run_id`, `search_run.status`/`started_at` | `01-*.md` §2.6 | Medium | S | Add to the (currently unrun) Alembic migration, verify it actually applies |

# 3. Severity × Effort Matrix

**Quick wins (do first — high leverage, low effort):** REC-01 (naming), REC-02 (CORS), REC-04 (real progress signal), REC-07 (Label pairing), REC-08 (aria-labels), REC-10 (save toast), REC-13 (shared select), REC-15 (keyboard shortcut), REC-16 (pagination), REC-19 (touch target), REC-20 (reduced motion), all of §2's supplementary findings.

**Big bets (high leverage, real effort — schedule deliberately):** REC-05 (Tracker drag-and-drop), REC-06 (Dialog primitive + confirm replacement), REC-09 (AI streaming), REC-11 (mobile nav drawer).

**Worth doing, not urgent (real but bounded value):** REC-03 (rate limiting), REC-12 (consolidate filter constants), REC-14 (motion on 3 mount points), REC-17 (pgvector SQL-level), REC-18 (structured logging).

**Sequencing note:** REC-04 should ship before REC-09 (both touch the same screen's "is the AI working" moment, and REC-04 is strictly cheaper since it reuses existing poll infrastructure rather than adding a new streaming protocol). REC-06 should ship before REC-14 (motion recipes are cleaner to define once the Dialog primitive exists, rather than animating the hand-rolled one and re-doing it).

# 4. Appendices

## 4a. File-pointer index
All `file:line` citations across this audit resolve against `job-search-agent-/` as the repo root. Frontend paths are relative to `frontend/`, backend paths relative to `backend/`. No file referenced in this audit was created for the purpose of this review — every citation points to pre-existing source.

## 4b. Glossary
- **`[REVIEW]` / `[GAP]` / `[PRESCRIPTIVE]`** — see confidence legend, `00-executive-summary-and-methodology.md`.
- **REC-NN** — a fully-templated recommendation in §1 of this file.
- **SF-NN** — a condensed supplementary finding in §2 of this file.

## 4c. Not worth it at this scale
Named explicitly so omissions read as calibrated judgment, not oversight:
- A full numbered color/spacing token scale (`primary-100...900` etc.) — the existing 13 semantic tokens are sufficient for an app with no theming/whitelabeling need.
- Storybook or a component-documentation site — no second consumer of these components exists.
- Visual regression testing (Chromatic/Percy) — valuable for a team shipping frequent UI changes with multiple contributors; disproportionate for a solo maintainer.
- A custom `<Select>` component to replace native `<select>` — native is already fully accessible; only the styling is duplicated (REC-13 solves that cheaply).
- Kanban swimlanes, WIP limits, custom fields, automation rules — named directly in §14's Jira/Trello/Asana row; real drag (REC-05) is worth it, these are not.
- Multiplayer/presence/collaboration of any kind (Figma-style cursors, Slack-style threads) — the PRD confirms no per-user data isolation exists; there is no multi-user surface to attach this to.
- Bulk notification actions ("mark all read", "clear all") — current notification volume per user doesn't justify the added UI surface yet; revisit if that changes.
- Full command palette (beyond REC-15's single shortcut) — 6 nav destinations don't need fuzzy search.
- Chart export/share (analytics screen) — no stated need for sharing insights outside the app.
- SSE-based full streaming infrastructure as a first step — REC-09's cheaper `StreamingResponse` approach gets most of the benefit; the full version in `04-*.md` §16 is explicitly sequenced *after*, not instead.
