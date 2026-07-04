[← back to index](00-executive-summary-and-methodology.md)

# 14. Benchmarking Against Industry Leaders

**Calibration rule** (applied once, to every row): pull a pattern only if (a) Job Radar has an analogous surface today, and (b) the underlying problem the pattern solves — coordination across many users, discovery at huge volume, trust at scale — actually exists for a 1-5-person tool with no auth (`PRD.md:47`, `AUDIT_REPORT.md` §C9). Otherwise, name it and reject it explicitly, here, rather than silently omitting it.

| Product | What we borrow | Lands in | What we explicitly skip, and why |
|---|---|---|---|
| **ChatGPT / Gemini** | Streaming token reveal + inline confidence/uncertainty framing — Job Radar already has a real precedent to extend, the confidence bar in `ParsedIntentPreview` (`03-*.md` §4) | §16 below, REC-04/REC-14 | Conversation threading, memory/context carryover, plugin/tool-call visuals — there is no chat surface and none is proposed; grafting chat UI onto a form-based app would be pure cargo-culting |
| **Linear** | Keyboard-first quick actions (a single `Cmd+K`-style shortcut to New Search); restrained, fast easing curves as the actual reference point for §17's motion tokens | REC-15 (below), §17 | A full fuzzy command palette across entities — overkill for an app with 6 nav destinations total |
| **Notion** | Empty-state copy quality (Job Radar's are already reasonably good, `02-*.md` §1.2/§1.6/§1.7 — use as the bar to hold, not a gap to close); inline-edit save confirmation, since the Tracker notes field (`02-*.md` §1.6) silently saves with zero feedback today | REC-10 | Nested blocks, multi-view databases, cross-linking — no content model here resembles Notion's |
| **Figma** | Nothing structural — no canvas, no multiplayer, and the PRD confirms no per-user data isolation exists at all, so there's no basis for presence/cursors. Cited only as a general hover/cursor-polish quality bar | — | Comments, presence, collaborative cursors — explicitly rejected, not just unaddressed |
| **Apple (HIG)** | Cross-cutting reference for easing-curve character and VoiceOver rigor | §17, §6 in `03-*.md` | Platform-specific patterns (sheets, haptics) — this is a web app |
| **Vercel** | Restrained gradient/mesh accents (already present and well-executed: `mesh-bg`, `text-gradient`, `globals.css:61-70`) and monospace for data values (already used for the confidence % and company slugs) — both are things to *keep*, not add | — (already done, noted as positive) | Deployment-pipeline UI (build logs, edge maps) — no analogous domain |
| **Slack / Discord** | Unread-badge affordance — already present and correctly implemented (`NotificationBell`, `03-*.md` §5); toast stacking — already handled by `sonner` | — (already done) | Threads, presence, channels — no multi-user surface exists to hang these on; explicitly rejected |
| **Jira / Trello / Asana** | Real drag-between-columns for the Tracker, because the app already visually promises "Kanban" (icon + copy, `02-*.md` §1.6) and this is the single highest-resonance gap between the metaphor and the mechanic | REC-05 | Swimlanes, WIP limits, custom fields, automation rules — explicitly not worth it at 1-5 users tracking their own job applications |

# 15. `[PRESCRIPTIVE]` Ambient Search History + Undo/Soft-Delete

> **This section is a target-state design proposal. No code implementing this exists today.** The "Your searches" list (`app/dashboard/page.tsx`) is a list of saved, named, recurring searches — not an ephemeral, browsable query history.

**Why this matters here, not just "because ChatGPT has it":** the New Search form (`02-*.md` §1.3) is currently a one-shot text box — if a user types a long, carefully-worded query, previews it, then navigates away without submitting, that text is gone. At 1-5 users doing occasional job-search sessions, the realistic pain point isn't "browse my search history from 6 months ago," it's "I closed the tab by accident and lost the sentence I just wrote."

**What "good" looks like:** a small, ambient list of recently-typed (not necessarily submitted) queries, surfaced as suggestions when the New Search textarea is focused-and-empty, each restorable with one click and deletable with an inline undo toast (`sonner` already supports action buttons on toasts — no new dependency).

**Cheap MVP** (sized for solo maintenance): persist the last 5 typed queries to `localStorage` client-side only (no backend change), show them as a dismissible chip list above the textarea when it's empty and focused, "Clear" wipes localStorage with a 5-second undo toast. Effort: S (a few hours), zero backend involvement.

**Full version:** persist to a new lightweight `search_draft` table (text, created_at, source: "new"|"edit"), expose `GET/DELETE /search-drafts`, soft-delete with a `deleted_at` column and a background cleanup job (reuse the existing APScheduler instance, `config/scheduler.py`) purging drafts older than 30 days. Undo becomes a real `PATCH .../restore` within the toast's visible window. Effort: M (a day) — mostly boilerplate given the existing repository/schema/route patterns are already established and copyable.

**Lands in:** `app/dashboard/new/page.tsx` (primary), optionally `edit/page.tsx`'s field-domain textarea.

# 16. `[PRESCRIPTIVE]` AI Streaming / "Thinking" UI

> **This section is a target-state design proposal. No code implementing this exists today — confirmed by a repo-wide grep for `stream` returning zero hits anywhere in the backend.**

**Why this matters here:** this is the one prescriptive item with an existing, concrete, negative counter-example already in production: the fake `PipelineProgress` timer (`03-*.md` §4) actively misrepresents system state today. The fix isn't just "add streaming for delight," it's "replace a UI element that currently lies" — that raises this from nice-to-have to the highest-priority prescriptive item in the audit.

**What "good" looks like:** for the two Groq-backed generative surfaces (`ParsedIntentPreview`, `CoverLetterDialog`), reveal tokens as they arrive rather than waiting for the full response. For the pipeline run (11 real backend stages already named in `search-filters.tsx:6-18`'s `STEPS` array — the copy already exists, it's just not wired to anything real), replace the fake timer with a signal that reflects actual orchestrator state.

**Cheap MVP:**
- *Parse/cover-letter streaming:* call Groq with `stream=True` in `services/groq_service.py`, proxy chunks through a `StreamingResponse` (FastAPI supports this natively — no new dependency), consume with the browser's `ReadableStream` on a `fetch()` call and append tokens to state as they arrive. Effort: M — touches both layers, but each side reuses an existing endpoint rather than adding a new protocol.
- *Real pipeline progress:* cheapest fix requires no new infrastructure — have `PipelineOrchestrator.run()` (`services/pipeline/orchestrator.py`) write its current stage name to the existing `search_run` row after each step (a column already conceptually adjacent to `source_stats` JSONB, added in migration 003 per `AUDIT_REPORT.md`), and have the frontend's existing 5-second poll (`search-detail-client.tsx:66-78`) read that real stage instead of driving a local `setInterval`. This deletes the fake timer entirely rather than layering a real signal on top of it. Effort: S–M, and notably **cheaper** than building streaming, since the poll infrastructure already exists — this should be sequenced first.

**Full version:** Server-Sent Events endpoint (`GET /searches/{id}/run/stream`) pushing stage-completion + token events over one connection instead of polling; frontend consumes via `EventSource`. Effort: L — new protocol, new failure modes (reconnect-on-drop) to handle for a real production-grade version, versus the MVP's reuse of existing polling.

**Lands in:** `search-detail-client.tsx` (pipeline progress), `new/page.tsx` + `parsed-intent-preview.tsx` (parse streaming), `cover-letter-dialog.tsx` (letter streaming).

# 17. `[PRESCRIPTIVE]` Motion & Design-Token System Completion

> **This section is a target-state design proposal.** Some motion exists (`03-*.md` §3), but no motion **tokens** (duration/easing variables) exist at all — every transition today hard-codes Tailwind's default utility durations.

**Why this matters here:** the app already has the right instinct in one place (`job-card.tsx`'s stagger) and the wrong instinct in the rest (three abrupt mount/unmount points, `03-*.md` §3) — the gap isn't taste, it's that there's no reusable system to apply the good instinct everywhere else.

**What "good" looks like:** a small, fixed set of durations/easings (not a large token explosion) applied consistently: fast (~150ms, ease-out) for hover/press feedback already covered by Tailwind's defaults; medium (~250-350ms) for mount/unmount of cards and the parsed-intent reveal, matching the existing `job-card.tsx` values; and one dialog-specific enter/exit pair once REC-06's real Dialog exists. All gated behind `prefers-reduced-motion` from day one (`03-*.md` §6).

**Cheap MVP:** define 2-3 CSS custom properties (`--motion-fast`, `--motion-medium`, `--motion-ease`) in `globals.css` alongside the existing color tokens, wrap the three abrupt-mount points (`ParsedIntentPreview`, `CoverLetterDialog`, `PipelineProgress`) in `<AnimatePresence>` + `<motion.div>` reusing the exact fade/y-rise values already validated in `job-card.tsx:34-37`, and delete the dead `fade-in`/`slide-up` Tailwind keyframes (`tailwind.config.ts:58-71`) rather than leaving unused config alongside new tokens. Effort: S, since it's copying an existing, already-good pattern to three more places rather than inventing a new one.

**Full version:** a documented motion-token file (durations, easings, and named "recipes" like `enterCard`/`exitDialog`) that `03-*.md`'s component checklist explicitly references, applied to route-level transitions (Next.js `template.tsx`) and list reordering (Tracker column moves, once REC-05's real drag exists). Effort: M, and sequenced *after* REC-05/REC-06 rather than before, since it needs those interactions to exist first.

**Lands in:** `new/page.tsx`, `cover-letter-dialog.tsx`, `search-filters.tsx` (`PipelineProgress`), `tailwind.config.ts`/`globals.css`.
