[← back to index](00-executive-summary-and-methodology.md)

# 1. Screen-by-Screen UI + UX Review

Layout diagrams below use a short-hand: `Section [size] > Section > Section` reading top-to-bottom, spacing values as literally written in the Tailwind classes.

## 1.1 Landing page — `app/page.tsx`
Layout: `Header [Logo, ThemeToggle, Dashboard link] > Hero (badge, H1, subtext) > CTA card (link-styled input mimic) > Start hunting button > 3-col feature grid`.

- `[REVIEW]` **Technical-naming leak**, `app/page.tsx:57`: `desc: "No forms. Groq parses title, domain, salary, and work mode."` — this is real marketing copy on the public landing page naming the LLM provider directly. → **REC-01**.
- `[REVIEW]` The CTA "input" (`:38-47`) is a `<Link>` styled to look like a text field with placeholder copy ("e.g. Remote senior software engineer...") but is not actually focusable/typeable — it's a decorative affordance that navigates to `/dashboard/new` on click. This works, but the visual promise ("this looks like a text box") slightly exceeds the actual interaction ("this is a button"); a real autofocused textarea on the landing page that carries the typed text forward via query param/session would close that gap. Minor, not urgent given there's a second explicit "Start hunting" button right below it (`:48-52`) as a fallback CTA.
- `[REVIEW]` `mesh-bg` gradient (`globals.css:65-70`) and `text-gradient` utility (`:61-63`) are tasteful, restrained accents — consistent with the calibrated small usage recommended in `04-benchmarking-and-roadmap.md`'s Vercel row. No changes needed here.

## 1.2 Dashboard home — `app/dashboard/page.tsx`
Layout: `Header [title + New search button] > source badges row > (skeleton | error | empty | grid)`.

- `[REVIEW]` Loading/error/empty states are all present and reasonably designed: 3-card skeleton grid (`:49-54`), destructive-bordered retry card (`:57-65`), dashed-border empty state with icon + CTA (`:67-78`). This is the pattern repeated (with minor variation) across every list screen in the app — see §1.9 for the one deviation worth flagging.
- `[REVIEW]` `SearchCardWithCount` (`:91-97`) fires one extra `useQuery` **per search card** just to fetch a result count (`page_size: 1`, reading only `.total`). At 1-5 users with a handful of searches this is invisible, but it's N+1-shaped on the frontend — the count could be returned inline on the `GET /searches` list response instead of N follow-up requests.
- `[REVIEW]` Source badges (`:39-47`) read well (`adzuna: 12 jobs / 24h`) and reuse the same badge/color system as everywhere else — consistent.

## 1.3 New Search — `app/dashboard/new/page.tsx` *(the screenshot)*
Layout, confirmed line-for-line against the screenshot: `H1 "New search" + subtext > Card["What are you looking for?"] (Textarea, char counter, button row, AI-notes) > [ParsedIntentPreview if parsed] > Card["Options"] (time-filter chips, override name/location) > Start hunting button`.

- `[REVIEW]` **The literal Groq leak from the screenshot**, `:173`: `Preview is optional — one Groq call when you click`. → **REC-01**.
- `[REVIEW]` Every disabled state visible in the screenshot is correct, deliberate logic, not a bug: "Preview with AI" is `disabled={text.trim().length < 10 || isParsing}` (`:161`); "Start hunting" is `disabled={!canCreate}` where `canCreate = text.trim().length >= 10 && !pending && !overLimit` (`:114`, `:223`). Both buttons appear dimmed in the screenshot because the textarea is empty (the visible content is the `placeholder` prop, `:131`, using the `EXAMPLE` constant, `:20-21`) — this is `disabled:opacity-50` from `button.tsx:6`, working as designed.
- `[REVIEW]` "Preview with AI" (`:156-170`) requires a manual click — there is no live/debounced parse as the user types, and no visible reason given for that choice beyond the adjacent copy ("Preview is optional"). This is a reasonable, deliberate cost-control choice (avoids firing a Groq call per keystroke) but it does mean the AI-understood-intent card never appears unless the user remembers to click a secondary button — worth a one-line "usually cheap and fast" progress affordance rather than more automation, given the cost-control rationale is sound. See `03-design-system-motion-ai-states.md` §4 for the loading-state critique of what happens *after* the click.
- `[REVIEW]` **Label/input pairing**: `Override name` (`:197-199`) and `Override location` (`:207-209`) are the *only* two of 16 `<Label>` usages app-wide that have a matching `htmlFor`/`id` pair (confirmed via repo-wide grep). The "Default time filter" label (`:188`) has no `htmlFor` because it labels a `FilterChips` button group, not a native input — for that case, the fix is `role="group" aria-label="Default time filter"` on the chip container, not `htmlFor`. → **REC-07**.
- `[REVIEW]` No motion at all on this screen — the `ParsedIntentPreview` card mounts abruptly under `{parsed && <ParsedIntentPreview>}` (`:180`) with no enter transition, in a page that is otherwise the app's primary "wow" moment (AI understood your one sentence). This is the single highest-leverage motion opportunity in the app. → cross-ref `03-design-system-motion-ai-states.md` §3, REC-14.

## 1.4 Companies — `app/dashboard/companies/page.tsx`
Layout: `Header [title + Add company toggle] > [inline Add-company card if open] > (skeleton | error | empty) > company list`.

- `[REVIEW]` Delete uses a blocking native `confirm()` (`:160`) rather than any in-app confirmation UI — consistent with the *only* other destructive-action pattern in the app (resume delete, tracker card delete all use `confirm()` too), so at least it's consistent, not ad hoc per screen. Still worth replacing app-wide once a real Dialog exists — see REC-06.
- `[REVIEW]` **Icon-only delete button has no `aria-label`** (`:156-164`, `<Button variant="ghost" size="icon">` wrapping a bare `<Trash2>`) — a screen reader announces this control as unlabeled. Contrast with `notifications/page.tsx:94-107` and `tracker/page.tsx:57` which *do* label their equivalent delete buttons — this is an inconsistency, not a blanket absence. → **REC-08**.
- `[REVIEW]` The inline add-form (`:74-123`) reuses `FilterChips` (built for filter toggles) as a 3-option source picker (`:107-111`) — functionally fine, semantically a little borrowed, but not worth a separate component at 3 static options.

## 1.5 Resume — `app/dashboard/resume/page.tsx` + `components/resume/resume-upload.tsx`
Layout: `Header > ResumeUpload (dashed dropzone) > (skeleton | error | empty) > resume cards (status badge, parsed skills/titles)`.

- `[REVIEW]` `ResumeUpload` (`resume-upload.tsx:34-47`) has real, correct drag-over state handling (`dragOver` toggles border/bg on `onDragOver`/`onDragLeave`/`onDrop`) — this is the one place in the app with a genuinely interactive hover/state transition beyond color, and it's implemented well. No motion beyond `transition-colors` (`:35`), which is sufficient here.
- `[REVIEW]` Same missing-`aria-label` pattern as Companies: the resume delete button (`resume/page.tsx:95-103`) has none, while its sibling `ResumeAttach`'s clear button (`resume-attach.tsx:63`, `aria-label="Clear attachment indicator"`) does. → folds into **REC-08**.
- `[REVIEW]` Parse-status badge (`:83-94`) with a spinning loader for `pending` is a nice small touch — clear, low-effort, effective; no change recommended.

## 1.6 Tracker — `app/dashboard/tracker/page.tsx`
Layout: `Header > (error | empty) > 5-column CSS grid (Saved/Applied/Interviewing/Offer/Rejected), each column a status count + stacked ApplicationCards`.

- `[REVIEW]` **This is not drag-and-drop.** Status changes happen via a native `<select>` per card (`:65-75`); there is no `@dnd-kit`/`react-beautiful-dnd`/HTML5 drag anywhere in the codebase (confirmed by grep). The screen's Kanban framing today is copy + a `KanbanSquare` icon (`tracker/page.tsx:4`, `:128`), not a drag mechanic. This matters directly for the Jira/Trello/Asana row of the benchmarking table — real drag is a calibrated "yes, worth it" recommendation precisely because the UI already visually promises it. → **REC-05**, `04-benchmarking-and-roadmap.md` §14.
- `[REVIEW]` **Silent-save gap**: the notes `<textarea>` (`:77-84`) saves `onBlur` with no visible confirmation — no toast, no "Saved" flash, nothing (contrast with every other mutation in the app, which does call `toast.success(...)`). A user who clicks away uncertain whether their note was saved has no way to know without reopening the card. → **REC-10**.
- `[REVIEW]` The native `<select>` here (`:65-75`) is one of three near-identical hand-copied instances of the same Tailwind class string across the app — see `03-design-system-motion-ai-states.md` §2 for the full triplication finding.
- `[REVIEW]` Delete (`:53-61`) does have `aria-label="Remove"` — correctly labeled, unlike its Companies/Resume counterparts (§1.4/§1.5).

## 1.7 Notifications + bell — `app/dashboard/notifications/page.tsx`, `components/layout/notification-bell.tsx`
Layout: `Header > (error | empty) > notification cards (unread badge, relative time, message, "View new matches" link, mark-read/dismiss icon buttons)`.

- `[REVIEW]` This is the **best-labeled screen in the app** — both icon-only actions have explicit `aria-label`s (`:97` "Mark read", `:106` "Dismiss"), and unread state is visually distinguished both by a border color (`:71`, `border-primary/30`) and an "Unread" badge (`:75`). Use this screen as the internal reference implementation when fixing §1.4/§1.5's missing labels, rather than inventing new copy.
- `[REVIEW]` `NotificationBell` (`notification-bell.tsx:9-14`) polls every 30s regardless of tab visibility (no `visibilitychange`/focus-based pause) — minor, inexpensive at this scale, but a first thing to add if polling frequency ever needs to increase.
- `[GAP]` No bulk actions ("mark all read", "clear all") — reasonable to omit today given notification volume is low per user, but flagged since it's an explicit ask in the original request's search-history section and the same UI pattern (multi-select + bulk action) would apply here too if ever needed. Not recommended now — see "not worth it at this scale" in `05-recommendations-backlog-and-appendices.md`.

## 1.8 Search detail (results) — `app/dashboard/searches/[id]/search-detail-client.tsx`
The richest screen: `Back link > Header (name, badges, Run/Pause/Insights/Edit/Delete actions) > [PipelineProgress if polling] > Filter bar (Show all/new, Posted-within chips, Refresh) > result count + resume-match select > (skeleton | error | empty | JobCard list) > pagination`.

- `[REVIEW]` This screen is where the fake pipeline-progress problem is most visible: `isPolling` drives both a **timer** (`:110-115`, advances a step counter every 4s regardless of real backend state) and the actual data poll (`:66-78`, `refetchInterval: isPolling ? 5000 : false`). The UI can show "step 8 of 11" while the real backend is still on step 2, or show 100% "done" while results genuinely haven't landed yet (there's a 3-minute hard timeout at `:124`, `180_000`ms, after which polling silently stops regardless of outcome). This is the single most consequential UX finding in the audit — it's not a missing feature, it's an existing feature that can actively mislead. → **REC-04**, full treatment in `03-design-system-motion-ai-states.md` §4 and `04-benchmarking-and-roadmap.md` §16.
- `[REVIEW]` Empty state correctly branches copy based on `isPolling` (`:298-311`: "still running" vs. "try running the search") — this is genuinely good, context-aware empty-state design; better than most of the other screens' static copy.
- `[REVIEW]` Pagination (`:320-342`) is simple Previous/Next with a page count — adequate at current result-set sizes (`page_size: 20`); no infinite-scroll or virtualization needed yet.
- `[REVIEW]` Resume-match `<select>` (`:262-276`) is the third instance of the triplicated native-select styling (§1.6, §1.9). Delete confirmation (`:213`) is the third `confirm()` instance.
- `[REVIEW]` The 5-value posted-filter set here (`All/1d/7d/30d/90d`, `:25-31`) doesn't match the 4-value set on the New Search form (`All time/7/14/30`, `new/page.tsx:23-28`) or the Edit form (`No filter/7/14/30`, `edit/page.tsx:29-34`) — three screens, three different day-filter option sets for conceptually the same control. Not a bug, but worth reconciling into one shared constant so the options are deliberately different (if there's a reason) rather than accidentally drifted.

## 1.9 Search edit — `app/dashboard/searches/[id]/edit/page.tsx`
Layout: near-duplicate of the New Search form's "Options" card, plus fields New Search doesn't expose at all: Name, Job title, Field/domain (as a full free-text `Textarea`, not the AI-parsed flow), Work mode, Experience level, Salary min/max, Poll interval.

- `[REVIEW]` **Confirmed duplication, not just similarity**: `FilterChips` usage for work-mode/experience/posted-within (`:132-146`, `:177-189`) is structurally identical to patterns on New Search and Search Detail, but each screen defines its own local options array (`WORK_MODES`/`LEVELS`/`POSTED` at `:19-34`) rather than importing one shared constant module. Three near-identical option lists drifting independently (see §1.8's day-filter mismatch, which is a direct symptom of this). → **REC-12**.
- `[REVIEW]` This screen has none of New Search's AI assistance (no free-text parse, no resume attach, no confidence preview) — reasonable, since editing an existing search is a config-tweak task, not a rediscovery task. Not a gap, a deliberate and correct scope difference.
- `[GAP]` Loading state is a single generic pulse block (`:79`, `h-64 animate-pulse`) rather than a skeleton shaped like the actual form — cosmetic, very low priority.

## 1.10 Search analytics — `app/dashboard/searches/[id]/analytics/page.tsx`
Layout: `Back link > H1 "Insights" > (skeleton | error | empty-if-zero-jobs) > 4 stat tiles > 2-col chart grid (salary histogram, postings over time) > horizontal top-skills bar chart > 2-col chart grid (by source, by work mode)`.

- `[REVIEW]` This is the most **dataviz-mature** screen in the app: `useChartColors()` (`:28-38`) computes theme-aware series/grid/axis/tooltip colors from the same HSL tokens as the rest of the UI, and the inline comment (`:26-27`) states the single series color was "validated against both card surfaces via the dataviz palette checker (contrast ≥ 3:1, in band)" — meaning this screen already had a color-contrast pass applied, unlike anywhere else in the app. This is a positive finding and a template: the same rigor is not yet applied to badge/status colors elsewhere (`lib/utils.ts:31-38`'s six hardcoded per-source Tailwind colors, or `--success`/`--warning` token contrast — see `03-design-system-motion-ai-states.md` §6).
- `[REVIEW]` Zero-jobs empty state (`:121-126`) is handled explicitly and distinctly from the loading/error states — good coverage.
- `[GAP]` No way to export/share these charts (image/CSV) — reasonable omission at this scale, not recommended (see "not worth it" appendix).

# 2. Search-Experience Journey Map

This synthesizes §1.3, §1.8, and §1.9 into one cross-screen flow, since "search experience" as requested is a journey, not a single screen:

```
Landing "type one sentence" CTA
   → New Search: free-text entry (no live search/autocomplete — by design, this isn't a query box)
      → optional manual "Preview with AI" click → ParsedIntentPreview (confidence bar, ambiguity notes)
      → optional resume attach (merges extracted text into the free-text field)
      → time-filter chips + name/location overrides
   → "Start hunting" → redirect to Search Detail with ?running=1
      → fake PipelineProgress (timer, decoupled from real state) + real 5s poll
      → results stream in once the real backend finishes (no relation to the fake progress bar's own completion)
   → Filter (all/new, posted-within) + resume-match select, paginate
   → Edit (config-only, no AI) | Insights (charts) | Run again | Pause/Resume | Delete
```

`[REVIEW]` The journey has no persistent, ambient "recent searches" or in-progress query history — the closest analogue, the dashboard's "Your searches" list (§1.2), is a list of **saved, named, recurring searches**, not an ephemeral query history a user could browse, restore, or delete-and-undo. This is a legitimate gap relative to the "search experience" deliverable, and is treated as a full forward-looking spec (not a code review, since nothing like it exists) in `04-benchmarking-and-roadmap.md` §15.

`[REVIEW]` There is no keyboard shortcut anywhere in the app (no `Cmd+K`, no `/` to focus search, no `Esc` to close the one modal that exists) — reasonable at this scale but worth a single cheap win: `Esc` to close `CoverLetterDialog` (see `03-design-system-motion-ai-states.md` §2).

# 3. Navigation & Information Architecture

`DashboardShell` (`components/layout/dashboard-shell.tsx`) provides: a fixed 256px sidebar, desktop-only (`:43`, `hidden ... md:flex`), listing all 6 sections (`NAV` array, `:21-28`: Searches, New Search, Companies, Resume, Tracker, Notifications) with pathname-based active-state highlighting (`:55`); a topbar with a subtitle (desktop-only, `:87-89`), a mobile-only "New" button (`:90-96`), `NotificationBell`, and `ThemeToggle`.

- `[REVIEW]` **Mobile nav gap, precise:** on mobile, the sidebar is entirely hidden, and the only navigation surfaces in the header are the "New" button (→ New Search) and the notification bell (→ Notifications). **Companies, Resume, Tracker, and the dashboard home ("Searches") are unreachable on mobile except by typing the URL directly.** Four of six sections. → **REC-11**.
- `[REVIEW]` The brand mark (`Radar` icon + "Job Radar" text) is a plain, non-interactive `<div>` in both the desktop sidebar header (`:44-52`) and the mobile header (`:83-86`) — consistent between the two (not a regression introduced by mobile), but neither is a link back to the dashboard home, which is a common, low-cost convention elsewhere. Minor.
- `[REVIEW]` The API-connectivity indicator (`:73-78`, a colored dot polling `/health` every 60s) is a nice, honest touch — surfaces backend availability directly in the chrome rather than failing silently. Worth preserving in any future nav redesign.
