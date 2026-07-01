# AI-Powered Job Search Agent — Detailed Plan

*A configurable agent that automatically finds and aggregates job opportunities matching user-defined criteria, across multiple free job sources, for the United States.*

---

## 1. Problem Statement

Finding the right jobs today means manually checking many different places — large job boards, niche boards, and individual company career pages — over and over, because new roles appear constantly and disappear quickly. The same job often shows up in several places, salaries are inconsistently listed, and job titles are ambiguous (a "QA Manager" or "Analyst" can mean completely different things depending on the field).

The goal is to remove this manual effort. We want an agent that, given a person's criteria — job title, field/domain, salary expectation, work mode, location, experience level, and employment type — continuously hunts across multiple sources, removes duplicates and irrelevant noise, and presents a clean, organized list of genuinely matching, recently posted jobs. It should keep doing this on a schedule and alert the user when something new and relevant appears.

Critically, the **field/domain is not fixed**. The agent must work equally well for a healthcare search, a logistics search, or a software search — the user simply types in what they're looking for, and the system adapts without anyone changing how it works underneath.

### The core difficulty (stated plainly)

The hard part is **not** the artificial intelligence. The hard part is **getting reliable access to job data** in the first place. There is no single, free, complete, organized list of every job. The information is scattered across many sources, each formatted differently, with salary often missing and titles described in free text. Every other challenge (removing duplicates, matching titles, reading salaries) flows from this fragmentation.

---

## 2. Objective and Expected Outcome

**Primary objective:** Reduce the manual effort of finding relevant jobs to nearly zero by automating discovery, filtering, organizing, and alerting.

**Expected outcome:** A small, configurable web tool where a user defines one or more searches (e.g., *Healthcare Analyst, remote or hybrid, US, senior level*), and the agent returns a continuously refreshed, de-duplicated, well-organized list of matching jobs — and notifies the user, inside the app, when new matches appear.

**Each result will show:**

- Job title
- Company
- Salary (when available; clearly flagged when not)
- Work type (Remote / Hybrid / On-site)
- Location
- A short summary of the job description
- Required skills
- A direct application link
- Date posted

---

## 3. Scope and Key Decisions

These decisions are now confirmed and define the boundaries of the project.

| Area | Decision | Reasoning |
|---|---|---|
| **Who uses it** | A single user, up to 5 people total | It's a personal tool, not a commercial platform. This keeps everything simple. |
| **Geography** | United States only | The US has the strongest free job-data coverage, which removes a major coverage problem. Location (city/state/remote) is still a filter *within* the US. |
| **Cost** | Free data sources only | No paid job-data subscriptions. This shapes which sources we can use. |
| **Notifications** | Inside the app (web dashboard) | No email or messaging integrations needed — alerts appear in the dashboard. |
| **Frequency** | Checks for new jobs every hour | Fresh enough to be useful, light enough to stay within free limits. |
| **Field / domain** | Typed in as free text | The user describes the field in their own words; the system interprets it. |
| **Web scraping** | Not used | Scraping major boards risks violating their terms of service. A free personal tool has no reason to take that legal risk. |
| **Missing salary** | Include the job, flag it | Many jobs omit salary. Hiding all of them would empty the list. Better to show them and mark salary as "not listed." |
| **Company career pages** | Covered via a short, user-editable company list | There's no free way to look up "every company in a field," so the user maintains a small list of companies whose career pages matter to them. |

### What is explicitly *out of scope*

- Automatically applying to jobs (the agent finds and presents; the user applies).
- Coverage outside the United States.
- Paid data sources.
- Scraping restricted job boards.

---

## 4. What's In, What's Missing, What's Assumed

**Assumptions (worth confirming as we go):**

- The user is comfortable typing in field/domain descriptions in plain language.
- "Up to 5 users" means a handful of personal searches, not heavy concurrent use.
- The salary figure, when present, is treated as a soft preference for sorting and filtering — not a hard cutoff that silently removes jobs.

**Known limitations to set expectations:**

- Even within the US, free sources don't cover *every* job. Coverage is good but not total — especially for very small companies that only post on their own website and aren't in our company list.
- "Date posted" can be unreliable because some jobs are re-posted with fresh dates. We'll do our best to detect genuinely new postings.
- Salary is missing on a meaningful share of listings, so the "include and flag" approach is essential.

---

## 5. The Solution in Plain Language

Think of the agent as an **assistant that repeats a careful research routine every hour**, for each search the user has saved. The routine has five conceptual stages:

1. **Understand the request.** Take the user's typed-in criteria — especially the free-text field/domain — and interpret what they actually mean, so the system knows what counts as a relevant match. (Example: it understands that "Healthcare Analyst" in healthcare is different from a "Data Analyst at a hospital software company.")

2. **Gather candidates.** Pull recent job postings from several free US sources at once: a broad job-search service for breadth, the federal government job site for public-sector roles, selected company career pages for depth, and remote-job feeds for remote roles.

3. **Clean and organize.** Convert every job — no matter which source it came from — into the same consistent format with the same fields. Read out the salary if it's there, summarize the description, and pull out the required skills.

4. **Remove noise and duplicates.** Drop jobs that don't actually match the criteria, and collapse the same job appearing in multiple sources into a single clean entry.

5. **Match, rank, and deliver.** Score the remaining jobs by how well they fit the request (using both the title *and* the field together), keep the best, figure out which ones are genuinely new since the last check, show them in the dashboard, and raise an in-app notification.

The user can change any part of any search at any time — title, field, salary, work mode, location — and the next hourly run simply uses the new criteria. Nothing about the underlying routine has to change.

---

## 6. Where the Jobs Come From (Non-Technical View)

We use a **two-layer approach** to free US sources: one layer for breadth, one for depth.

**Layer 1 — Breadth (cast a wide net):**

- A broad, free US job-search service that aggregates many listings and often includes salary information. This is the main engine of coverage.
- The US federal government's official job site, which surfaces public-sector roles that general boards rarely cover well.
- Free remote-job feeds, to strengthen results for anyone searching specifically for remote work.

**Layer 2 — Depth (go straight to the source):**

- Selected company career pages, accessed through the free, standardized systems many companies already use to publish their openings. This captures jobs that often *only* appear on a company's own site and never reach the big boards.
- Because there's no free way to automatically know "which companies hire in field X," the user keeps a short, editable list of companies they care about. Adding or removing a company is a simple list edit — no rebuild required.

**An important honesty note:** the exact free services available, and their terms, change over time. The very first task in the plan is to confirm which sources are currently free and usable, and to lock the list to whatever is actually live. We don't assume anything stays free forever.

---

## 7. How the Work Breaks Down (Workstreams)

The project is organized into seven self-contained workstreams. Each can be built and checked on its own.

### Workstream A — Source Gathering
**Purpose:** Collect raw job postings from each chosen free source.
**Delivers:** A steady stream of recent postings, tagged by where they came from.
**Done when:** At least two sources reliably return live US jobs, and if one source fails the others still work.

### Workstream B — Cleaning & Enrichment
**Purpose:** Turn messy, inconsistent postings into one clean, consistent format and fill in the useful extras (salary reading, description summary, required skills).
**Delivers:** Tidy job records with all the standard fields.
**Done when:** Nearly every record has all the required fields filled in, and salary is read correctly when present.

### Workstream C — Duplicate Removal
**Purpose:** Recognize when the same job appears in more than one place and merge it into one entry.
**Delivers:** A clean list with no repeats.
**Done when:** On a sample of known duplicates, the system reliably merges them without wrongly merging different jobs.

### Workstream D — Matching & Ranking
**Purpose:** Keep only the jobs that truly fit the user's criteria, and order them by how good the fit is — using the field/domain to resolve ambiguous titles.
**Delivers:** A ranked shortlist of genuine matches.
**Done when:** A manual review of the top results shows they're clearly relevant, across two unrelated fields (proving the system isn't secretly tuned to one field).

### Workstream E — Scheduling & "What's New"
**Purpose:** Run every search automatically each hour, and figure out which matches are genuinely new since last time.
**Delivers:** A reliable hourly cycle that surfaces only new jobs, not the same ones repeatedly.
**Done when:** Repeated runs never re-show jobs the user has already seen.

### Workstream F — Configuration & Dashboard
**Purpose:** Let the user create and edit searches, view results, and see notifications — all in the app.
**Delivers:** A simple dashboard where any criterion (including the field) can be changed and takes effect on the next run.
**Done when:** Editing a search changes the next run's results with no behind-the-scenes changes needed.

### Workstream G — Field Interpretation (the dynamic piece)
**Purpose:** Take the user's free-text field/domain and turn it into clear matching guidance, plus help decide which company career pages are relevant.
**Delivers:** A consistent interpretation of any field the user types, even one never seen before.
**Done when:** A brand-new field produces sensible matching behavior without anyone changing the system.

---

## 8. The Plan, Phase by Phase

A practical, ordered roadmap. Each phase produces something usable before the next begins.

### Phase 1 — Confirm the foundations
- **Goal:** Lock down exactly which free sources we'll use and confirm they're currently available.
- **Actions:** Register for the broad US job service; confirm the government job site's free terms; test a couple of company career-page connections; decide the starting company list.
- **Result:** A confirmed, live list of free sources.
- **Complete when:** Every chosen source has been verified as free and working today.

### Phase 2 — Define the standard job format and the search settings
- **Goal:** Agree on the consistent shape every job will take, and the set of search criteria a user can configure (with field as a free-text setting).
- **Result:** A clear definition of "a job record" and "a saved search."
- **Complete when:** Both are reviewed and frozen for the first version.

### Phase 3 — Prove it end-to-end on a thin slice
- **Goal:** Run the whole routine for a couple of real searches in **two different fields**, to prove the system is genuinely field-independent.
- **Actions:** Gather → clean → match → show results, for example *Healthcare Analyst (US, remote/hybrid)* and one unrelated field.
- **Result:** Real, relevant results visible for two unrelated searches.
- **Complete when:** Both searches return clearly relevant jobs and switching the field needs no system changes.

### Phase 4 — Make it consistent and clean
- **Goal:** Strengthen cleaning, enrichment, and duplicate removal so results are tidy and trustworthy.
- **Result:** Consistent, de-duplicated, well-summarized results.
- **Complete when:** Records are reliably complete and duplicates are merged correctly.

### Phase 5 — Make it automatic
- **Goal:** Add the hourly schedule and the "what's new since last time" detection.
- **Result:** Searches run on their own every hour and surface only new matches.
- **Complete when:** Repeated runs never repeat already-seen jobs.

### Phase 6 — Add the dashboard and notifications
- **Goal:** Give the user a place to manage searches, read results, and see alerts — all in-app.
- **Result:** A working dashboard with editable searches and in-app notifications.
- **Complete when:** A user can create, edit, and monitor searches entirely through the app.

### Phase 7 — Polish and expand coverage
- **Goal:** Improve reliability, watch for sources breaking, and grow the company list for deeper career-page coverage.
- **Result:** A dependable everyday tool.
- **Complete when:** Source problems are noticed automatically and adding a new source or company needs no rebuild.

---

## 9. Task Checklist

A simple, ordered task list derived from the phases.

| # | Task | Priority | Depends on |
|---|---|---|---|
| 1 | Confirm and lock the free US source list | High | — |
| 2 | Define the standard job format | High | 1 |
| 3 | Define the saved-search settings (field as free text) | High | 1 |
| 4 | Set up field interpretation (Workstream G) | High | 2 |
| 5 | Decide which company career pages to include | High | 4 |
| 6 | Connect the broad US job source | High | 2 |
| 7 | Connect company career pages and government source | High | 5 |
| 8 | Build the cleaning & enrichment step | High | 6 |
| 9 | Build duplicate removal | High | 8 |
| 10 | Build matching & ranking (title + field together) | High | 8, 9 |
| 11 | Set the "include and flag" salary rule | Medium | 8 |
| 12 | Add the hourly schedule and saved searches | Medium | 10 |
| 13 | Add "what's new since last run" detection | Medium | 12 |
| 14 | Build the dashboard and search editor | High | 3, 12 |
| 15 | Add in-app notifications | Medium | 13, 14 |
| 16 | Add monitoring for broken sources | Medium | 7, 12 |
| 17 | Test quality across two unrelated fields | Medium | 9, 10 |

---

## 10. Risks and How We Handle Them

| Risk | Why it happens | Effect | How we reduce it |
|---|---|---|---|
| A free source changes or stops working | External services update or restrict access | Gaps in results | Keep sources independent so one failing doesn't break the rest; monitor and fix quickly; confirm terms up front |
| The system accidentally gets tuned to one field | It's easy to special-case the first field built | Breaks the "works for any field" promise | Build and test on two unrelated fields from the very start |
| The salary filter empties the results | Many jobs omit salary | An almost-empty list | Include jobs without salary and clearly flag them; treat the salary target as a soft preference |
| Wrong matches due to ambiguous titles | The same title means different things in different fields | Irrelevant results, lost trust | Match using the field *and* the title together; review quality regularly |
| Duplicates slip through or good jobs get wrongly merged | The same role is posted differently in different places | Cluttered or incorrect list | Careful duplicate-detection with measured accuracy on samples |
| Dead application links | Jobs get filled or removed after we find them | Frustrating dead ends | Re-check links before showing them; always display the posted date |
| A source's free terms change over time | Free tiers and rules evolve | Loss of a source | Re-verify terms periodically; keep alternatives ready |

---

## 11. What Success Looks Like

- A user can set up a search in any field, in plain language, and get relevant US results without touching anything technical.
- Results are clean, organized, de-duplicated, and recent.
- Salary is shown when available and clearly flagged when not.
- New matching jobs appear in the dashboard and trigger an in-app alert, automatically, every hour.
- Changing a search's criteria — including switching to a completely different field — just works on the next run.
- The same system handles two unrelated fields equally well, proving it's genuinely flexible.

---

## 12. Recommended Approach and Immediate Next Steps

**Recommended approach:** A small, single-app personal tool that combines **broad free US job sources** (for wide coverage) with **selected company career pages** (for depth), interprets the user's free-text field to stay flexible, and runs automatically every hour with in-app alerts. Web scraping is deliberately avoided, and jobs without salary are included and flagged rather than hidden.

**Immediate next steps:**

1. **Verify the free sources** are currently available and lock the starting list (Phase 1).
2. **Agree the standard job format and search settings**, with field as a free-text option (Phase 2).
3. **Prove it on two unrelated fields** end-to-end before building anything further — this is the cheapest way to guarantee the tool stays genuinely flexible rather than quietly hardwired to one field (Phase 3).

---

*This document focuses on the plan and approach rather than technical implementation. The two areas with the most design work remaining are field interpretation (Workstream G) and the source-gathering setup (Workstreams A and G together).*