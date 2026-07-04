[← back to index](00-executive-summary-and-methodology.md)

# 1. Design System & Token Inventory

**Color tokens** — `app/globals.css:6-49`, HSL CSS variables, light (`:root`) + dark (`.dark`), wired into Tailwind via `tailwind.config.ts:12-44`: `background`, `foreground`, `card` (+foreground), `primary` (+foreground), `secondary` (+foreground), `muted` (+foreground), `accent` (+foreground), `destructive` (+foreground), `border`, `input`, `ring`, `success`, `warning`. **13 semantic colors total, no numbered scale** (no `primary-100...900`) — appropriate for an app this size; a full numbered scale would be over-engineering here (see `05-recommendations-backlog-and-appendices.md` "not worth it").

**Radius:** one token, `--radius: 0.75rem` (`:24`), derived into `lg`/`md`/`sm` (`tailwind.config.ts:45-49`). Applied consistently — every `Card`/`Button`/`Input`/`Textarea` primitive uses the derived scale, no ad hoc `rounded-[Npx]` found elsewhere.

**Shadow:** two custom tokens, `shadow-glow` (`:55`, used on hover states — `search-card.tsx:13`, `job-card.tsx:39`) and `shadow-card` (`:56`, the default `Card` elevation, `card.tsx:8`). Consistent, restrained usage.

**Typography:** Geist Sans/Mono via `next/font`, wired as `font-sans`/`font-mono` (`tailwind.config.ts:50-53`). `[GAP]` No defined type scale beyond Tailwind's raw defaults (`text-xs`/`sm`/`base`/`lg`/`2xl` used directly, ad hoc, across components) — works today because usage is actually consistent in practice (page titles are always `text-2xl font-bold`, card titles always `text-base`/`text-lg`), but there's no single source of truth enforcing it; a `01-recommendations` note captures this as a documentation task, not a code change.

**Spacing & icons (folds in what would otherwise be two standalone audits):** spacing is ad hoc Tailwind utility spacing (`gap-2`/`3`/`4`, `p-4`/`5`/`6`) but **genuinely consistent in practice** — card padding is `p-5` or `p-6` project-wide, inter-element gaps scale predictably with hierarchy. Icons are exclusively `lucide-react` (confirmed: no other icon import anywhere), sized `h-3`/`h-3.5`/`h-4`/`h-5`/`h-8`/`h-10`/`h-12` matching visual hierarchy (badges/meta text → buttons → empty-state illustrations). **No spacing or icon inconsistency was found across any of the 11 screens** — this finding is stated once here rather than repeated per-screen.

**Motion tokens:** none exist. See §3.

**Component primitives** (`components/ui/`, 7 files, ~185 lines total): `Button` (CVA variants: `default`/`secondary`/`outline`/`ghost`/`destructive` × sizes `default`/`sm`/`lg`/`icon`, `button.tsx:5-24`), `Card`/`CardHeader`/`CardTitle`/`CardDescription`/`CardContent` (`card.tsx`), `Badge` (`badge.tsx`), `Input`/`Label`/`Textarea` (each a thin styled wrapper over the native element), `Skeleton` (a single pulsing div). This is a deliberately minimal shadcn-style set — appropriate for the app's size. `sonner` (toast) is used globally via `app/providers.tsx` and is **not** a gap (contrary to what a surface-level scan might assume) — it's installed, mounted, and used consistently everywhere a mutation succeeds or fails.

# 2. Design-System Consistency Audit

`[REVIEW]` **The real primitive gap is Dialog, not Select or Toast.** There is exactly one hand-rolled modal in the entire app, `components/jobs/cover-letter-dialog.tsx` (`:52-59`): a `fixed inset-0` backdrop with `onClick={onClose}`, an inner panel with `onClick={(e) => e.stopPropagation()}` to prevent the backdrop handler from firing. It has **no `role="dialog"`, no `aria-modal="true"`, no focus trap, and no `Escape`-key handler** — a keyboard user cannot close it without a mouse, and a screen-reader user isn't told a dialog opened at all. → **REC-06**.

`[REVIEW]` **Native `<select>` markup is duplicated three times** with near-identical hand-copied Tailwind classes, rather than one shared component: `tracker/page.tsx:65-75` (application status), `cover-letter-dialog.tsx:75-85` (resume picker), `search-detail-client.tsx:262-276` (resume-match picker). This is a duplication smell, **not an accessibility smell** — native `<select>` is fully keyboard/screen-reader accessible by default, so the fix is a shared `<NativeSelect>` wrapper (or an extracted className constant) purely for maintainability, not a Radix/custom listbox rebuild. → **REC-13**.

`[REVIEW]` **Destructive confirmation is `window.confirm()` everywhere**, consistently: `companies/page.tsx:160`, `resume/page.tsx:99`, `tracker/page.tsx:55`, `search-detail-client.tsx:213`. Consistent is good; blocking, unstyled, and unbrandable is not. Once a real Dialog exists (REC-06), replacing all four call sites with one `<ConfirmDialog>` is a single follow-on change, not four separate ones.

`[REVIEW]` **`<Label>`/`htmlFor` pairing**: repo-wide grep confirms exactly 2 of 16 `<Label>` usages have a matching `htmlFor` + input `id` pair — both on `app/dashboard/new/page.tsx` (`:197-199` "Override name", `:207-209` "Override location"). The other 14 (Companies' Name/Slug, Edit Search's Name/Job title/Field domain/Location/Salary min/Salary max/Poll interval, and the "Default time filter"/"Work mode"/"Experience level" chip-group labels) are visually adjacent to their control but not programmatically associated — a screen reader will not announce the label when the field receives focus. → **REC-07**.

`[REVIEW]` **Icon-only button `aria-label` is inconsistent, not absent.** Present: `theme-toggle.tsx:15,24`, `notification-bell.tsx:20`, `notifications/page.tsx:97,106`, `tracker/page.tsx:57` ("Remove"), `cover-letter-dialog.tsx:62` ("Close"), `resume-attach.tsx:63` ("Clear attachment indicator"). Missing: `companies/page.tsx:156-164` (delete), `resume/page.tsx:95-103` (delete). The Notifications screen (`02-screens-ux-search-experience.md` §1.7) is the best-labeled reference implementation in the app — copy the same pattern to the two gaps. → **REC-08**.

# 3. Motion — Current-State Review

`[REVIEW]` `framer-motion` 11.15 is installed (`package.json`) and used in **exactly one place**: `components/jobs/job-card.tsx:34-37` — `<motion.div initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} transition={{delay: index*0.04, duration:0.35}}>`, a mount fade-and-rise with a per-index stagger delay on the job-results list. This is well-executed (the stagger is a genuine nice touch) but isolated — no other screen in the app uses framer-motion at all.

`[REVIEW]` `tailwind.config.ts:58-71` defines `fade-in`/`slide-up` keyframe utilities. Repo-wide grep for `animate-fade-in`/`animate-slide-up` returns **zero matches** — this is dead configuration, defined once and never applied anywhere.

`[REVIEW]` Everywhere else, "motion" means one of: `transition-colors`/`transition-all`/`transition-shadow` hover-only utility classes (`badge.tsx:8`, `button.tsx:6`, `dashboard-shell.tsx:61`, `resume-upload.tsx:35`, `search-filters.tsx:29`, `search-card.tsx:13`, `parsed-intent-preview.tsx:39`), or `animate-pulse`/`animate-spin` for loading (skeletons, `Loader2` icons — used correctly and consistently across every mutation button in the app).

`[REVIEW]` **No `AnimatePresence`, anywhere** — every conditionally-rendered overlay or card mounts and unmounts abruptly with a bare `{condition && <Component/>}`:
- `new/page.tsx:180` — `{parsed && <ParsedIntentPreview>}` (the AI-understood-your-search moment — the app's best "wow" candidate, currently a hard cut)
- `job-card.tsx:172-178` — `{showCoverLetter && <CoverLetterDialog>}` (modal has no enter/exit transition at all, on top of lacking `role="dialog"` per §2)
- `search-detail-client.tsx:221` — `{isPolling && <PipelineProgress>}`

`[GAP]` No `prefers-reduced-motion` handling anywhere (no matching media query in `globals.css` or `tailwind.config.ts`) — moot today given how little motion exists, but should be built in from the start once motion tokens are introduced (`04-benchmarking-and-roadmap.md` §17), not retrofitted after.

# 4. AI Loading / "Thinking" States — Current-State Review

Three real, distinct AI-response surfaces exist — none of them stream:

1. **`ParsedIntentPreview`** (`components/search/parsed-intent-preview.tsx`) — button shows a spinner (`new/page.tsx:164-168`) while `POST /parse-text` is in flight, then the full parsed-intent card appears at once: field grid, a confidence bar (`:32-43`, animated width via `transition-all` only — no count-up), and an ambiguity-warnings block if present. Reasonably designed for a non-streaming response; the confidence bar is a good existing precedent to extend (`04-benchmarking-and-roadmap.md` §14, ChatGPT/Gemini row).
2. **`PipelineProgress`** (`components/search/search-filters.tsx:6-41`) — an 11-step labeled progress list (`STEPS` array, `:6-18`: "Expand field" → "Notify"). `[REVIEW]` **This is a fake.** `search-detail-client.tsx:110-115` drives `activeStep` from a plain `setInterval` firing every 4 seconds, capped at step 10, with **zero connection to the real backend pipeline state** — the real signal being polled is just `resultsQuery.data?.total` (`:117-126`). A run that actually takes 45 seconds will show a full, confident-looking 11-step readout; a run that takes 4 minutes will show "step 11 of 11 complete" for over 3 minutes before the 180-second timeout silently gives up (`:124`). This is the most consequential single finding in this audit: it's not a missing feature, it's existing UI actively telling the user something untrue about system state. → **REC-04**, forward spec in `04-benchmarking-and-roadmap.md` §16.
3. **`CoverLetterDialog`** (`components/jobs/cover-letter-dialog.tsx`) — spinner-in-button (`:92-96`) while `POST /jobs/{id}/cover-letter` is in flight, then the full generated letter appears in one paint (`:110-114`). Same non-streaming pattern as #1.

`[REVIEW]` Backend-side, a repo-wide grep for `stream` returns **zero hits** — the Groq client is never called with `stream=True` anywhere in `services/groq_service.py` or elsewhere. A real streaming/"thinking" UI (the literal ask in the original request's "AI Loading Experience" section) is therefore a **full-stack change**, not a frontend rendering fix: it requires a backend SSE/WebSocket endpoint in addition to a frontend token-reveal component. This materially changes the effort estimate versus treating it as a UI-only task — captured accurately in the prescriptive spec at `04-benchmarking-and-roadmap.md` §16.

# 5. Component-by-Component Checklist

| Component | File | Default | Hover | Focus | Disabled | Loading | Error | Empty | A11y label paired | Motion |
|---|---|---|---|---|---|---|---|---|---|---|
| Button | `ui/button.tsx` | ✓ | ✓ | ✓ (`focus-visible:ring-2`) | ✓ (`opacity-50`) | n/a (per-usage `Loader2`) | n/a | n/a | usage-dependent (§2) | hover-only |
| Card | `ui/card.tsx` | ✓ | usage-dependent (`hover:shadow-glow` where applied) | n/a | n/a | n/a | n/a | n/a | n/a | usage-dependent |
| Input / Textarea | `ui/input.tsx`, `ui/textarea.tsx` | ✓ | n/a | ✓ | ✓ | n/a | n/a | n/a | 2/16 pages pair `htmlFor` (§2) | none |
| Label | `ui/label.tsx` | ✓ | n/a | n/a | n/a | n/a | n/a | n/a | see above | none |
| Badge | `ui/badge.tsx` | ✓ | n/a | n/a | n/a | n/a | n/a | n/a | n/a | `transition-colors` only |
| Skeleton | `ui/skeleton.tsx` | ✓ (`animate-pulse`) | n/a | n/a | n/a | is-the-loading-state | n/a | n/a | n/a | pulse |
| JobCard | `jobs/job-card.tsx` | ✓ | ✓ (`shadow-glow`) | via child buttons | via child buttons | `JobCardSkeleton` exported | n/a | n/a | n/a | ✓ mount fade+stagger (only instance app-wide) |
| CoverLetterDialog | `jobs/cover-letter-dialog.tsx` | ✓ | n/a | **no focus trap** | button-level only | ✓ spinner | via toast | "upload a resume first" copy | **no `role=dialog`/`aria-modal`/Esc** (§2) | **none, abrupt mount/unmount** |
| ParsedIntentPreview | `search/parsed-intent-preview.tsx` | ✓ | n/a | n/a | n/a | parent button spinner | n/a | n/a | n/a | **none, abrupt mount** |
| PipelineProgress | `search/search-filters.tsx` | ✓ | n/a | n/a | n/a | is-the-loading-state (**fake**, §4) | n/a | n/a | n/a | `transition-colors` step-highlight only |
| FilterChips | `search/search-filters.tsx` | ✓ | ✓ | ✓ (button-level) | n/a | n/a | n/a | n/a | **no `role=group`/`aria-label` on the set** | none |
| ResumeUpload | `resume/resume-upload.tsx` | ✓ | ✓ drag-over state | n/a | ✓ (uploading) | ✓ spinner+label swap | via toast | n/a | n/a | `transition-colors` |
| ResumeAttach | `search/resume-attach.tsx` | ✓ | n/a | n/a | ✓ (extracting) | ✓ spinner | via toast | n/a | ✓ clear button | none |
| SearchCard | `search/search-card.tsx` | ✓ | ✓ (`shadow-glow`) | n/a (whole card is a Link) | n/a | n/a | n/a | n/a | n/a | none |
| NotificationBell | `layout/notification-bell.tsx` | ✓ | ✓ | ✓ | n/a | n/a | n/a | count=0 hides badge | ✓ | none |
| DashboardShell nav | `layout/dashboard-shell.tsx` | ✓ | ✓ | via `<Link>` default | n/a | n/a | n/a | n/a | n/a | `transition-colors` on active-state |

# 6. Accessibility Audit (WCAG lens)

- `[REVIEW]` **Keyboard:** all native form controls (`input`/`select`/`textarea`/`button`) are keyboard-operable by default and none have had that default behavior broken. The one real gap is the hand-rolled `CoverLetterDialog` — no focus trap means Tab can escape the dialog into page content behind it, and there's no `Escape` handler (§2). `FilterChips` (`search-filters.tsx:43-70`) renders a row of independent `<Button>`s that *visually* reads as a segmented/radio control but has no `role="radiogroup"`/`role="group"` — a screen-reader user hears "button, button, button" with no indication they form a single choice set. → folds into **REC-07**.
- `[REVIEW]` **Focus indicators:** consistently present via `focus-visible:ring-2 focus-visible:ring-ring` on `Button`/`Input`/`Textarea` (`button.tsx:6`, `input.tsx:10`, `textarea.tsx:9`) and on the three hand-copied native `<select>`s. Good baseline, no gap found.
- `[REVIEW]` **ARIA / labeling:** see §2 (Label pairing, icon-button labels, FilterChips grouping) — the substantive finding of this section, not repeated here.
- `[GAP]` **Alt text:** zero `alt=` attributes exist anywhere — but also zero `<img>` tags exist anywhere (confirmed by grep); the app uses only Lucide SVG icons and CSS gradients for all visuals. Not a gap in practice, just a fact worth recording so it isn't mistaken for an oversight later once real images (e.g. company logos) are added.
- `[REVIEW]` **Contrast:** `analytics/page.tsx:26-27`'s inline comment confirms the chart series color was explicitly validated for ≥3:1 contrast against both card surfaces — the one place in the app where this was actually checked. `--warning` (`hsl(38 92% 45%)` light / `hsl(38 92% 50%)` dark) and `--success` (`hsl(142 71% 40%)` light / `45%` dark) are used as both badge backgrounds-at-15%-opacity and as plain text colors (e.g. `job-card.tsx:163`, `text-warning`) across several screens — these should get the same automated contrast check (axe or Lighthouse) the analytics screen already received, rather than a manual code-reading judgment call here.
- `[REVIEW]` **Touch targets:** icon-sized buttons are `h-9 w-9` (`button.tsx:20`, 36px) — under the commonly-cited 44px minimum recommended touch target. Affects every icon-only button in the app (delete, mark-read, dismiss, theme toggle, notification bell). Low-cost fix: bump the `icon` size variant, or add invisible padding via a larger hit-slop, without changing the visual icon size.
- `[GAP]` **Reduced motion:** no `prefers-reduced-motion` support exists (§3) — low urgency today given how little motion exists, but should be designed in from the start of any motion-token work rather than retrofitted.
