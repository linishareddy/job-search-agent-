"""
Complete end-to-end flow test — every API step with request/response payloads.

This exercises the FULL user journey:
  1. Health check
  2. Parse free-text (AI #1 — Groq intent parser)
  3. Create search from text + run pipeline (AI #2 field expansion + AI #3 enrichment)
  4. Fetch saved search (shows cached AI field expansion)
  5. Fetch job results (with match_reason, gaps, relevance_score)
  6. Fetch notifications
  7. Source health stats

Prerequisites (.env):
  - GROQ_API_KEY          (required for all AI steps)
  - ADZUNA_APP_ID/KEY     (optional — skipped if missing)
  - JOOBLE_API_KEY        (optional — skipped if missing)
  - Postgres running

Usage:
  python3 test_full_flow.py
  python3 test_full_flow.py --text "Remote Python developer in the US, 120k+"
  python3 test_full_flow.py --keep-data
  python3 test_full_flow.py --output flow_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_TEXT = (
    "Remote senior healthcare analyst in the US, full time, 90k-130k, "
    "focusing on EHR and claims data"
)

FLOW_STEPS = """
COMPLETE FLOW MAP
=================

USER INPUT (plain English)
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 1  POST /searches/parse-text                             │
│         AI #1: Groq llama-3.1-8b — parse intent to fields     │
│         Input:  { "text": "..." }                             │
│         Output: job_title, field_domain, work_mode, salary... │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 2  POST /searches/from-text  (run_immediately: true)     │
│         Saves search + runs 11-step pipeline (blocks until done)│
│                                                               │
│  Pipeline internals (not separate API calls):                 │
│    2a. AI #2 Groq — field expansion (search_queries, etc.)    │
│    2b. Fetch Adzuna, Jooble, Remotive, GH, Lever, Ashby       │
│    2c. Normalize + negative keyword filter                    │
│    2d. Fingerprint dedup + vector embedding dedup             │
│    2e. BM25 + cosine pre-score → top 70                       │
│    2f. AI #3 Groq llama-3.3-70b — enrich + score + explain    │
│    2g. Save jobs + job_search_result rows                       │
│    2h. Create notification if new high-score jobs             │
│                                                               │
│         Input:  { "text", "run_immediately": true, "overrides"}│
│         Output: saved search + run_id                         │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 3  GET /searches/{id}                                    │
│         Shows field_expansion_cache (AI #2 output, cached 24h)  │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 4  GET /searches/{id}/results                              │
│         Jobs ranked by AI relevance_score + match_reason/gaps   │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 5  GET /notifications                                    │
│         Alerts for new high-relevance jobs (score >= 7/10)    │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 6  GET /health/sources                                   │
│         Jobs fetched per source in last 24 hours              │
└───────────────────────────────────────────────────────────────┘
"""


def pp(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


class FlowReporter:
    def __init__(self) -> None:
        self.report: dict[str, Any] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "steps": [],
        }

    def step(self, name: str, *, request: Any = None, response: Any = None, notes: str = "") -> None:
        print("\n" + "═" * 72)
        print(f"  {name}")
        print("═" * 72)
        if notes:
            print(f"\n💡 {notes}")
        if request is not None:
            print("\n📤 REQUEST:")
            print(pp(request))
        if response is not None:
            print("\n📥 RESPONSE:")
            print(pp(response))

        self.report["steps"].append({
            "name": name,
            "notes": notes,
            "request": request,
            "response": response,
        })

    def save(self, path: str) -> None:
        self.report["finished_at"] = datetime.now(timezone.utc).isoformat()
        with open(path, "w") as f:
            json.dump(self.report, f, indent=2, default=str)
        print(f"\n💾 Full report saved to: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Complete end-to-end flow test")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--keep-data", action="store_true")
    parser.add_argument("--output", default="", help="Save JSON report to this file")
    parser.add_argument("--timeout", type=float, default=600.0, help="Pipeline timeout seconds")
    args = parser.parse_args()

    reporter = FlowReporter()
    search_id: str | None = None

    print(FLOW_STEPS)
    print(f"\n🚀 Starting full flow test")
    print(f"   Base URL : {args.base_url}")
    print(f"   User text: {args.text[:80]}{'...' if len(args.text) > 80 else ''}")
    print(f"   Timeout  : {args.timeout}s (pipeline can be slow on first run — loads embedding model)")

    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=args.timeout) as client:
            # ── STEP 0: Health ────────────────────────────────────────────────
            r = client.get("health")
            r.raise_for_status()
            reporter.step(
                "STEP 0 — GET /health",
                response=r.json(),
                notes="Confirms API + Postgres are up before starting.",
            )

            # ── STEP 1: Parse text (AI #1) ────────────────────────────────────
            parse_body = {"text": args.text}
            r = client.post("searches/parse-text", json=parse_body)
            r.raise_for_status()
            parsed = r.json()["data"]
            reporter.step(
                "STEP 1 — POST /searches/parse-text  [AI #1: Groq intent parser]",
                request=parse_body,
                response=r.json(),
                notes=(
                    "Groq model: llama-3.1-8b-instant. Converts plain English → structured fields. "
                    "User reviews confidence + ambiguities before saving."
                ),
            )

            # ── STEP 2: Create + run pipeline ─────────────────────────────────
            create_body = {
                "text": args.text,
                "run_immediately": True,
                "overrides": {
                    "name": f"Full Flow Test {datetime.now().strftime('%H%M%S')}",
                },
            }
            print("\n⏳ STEP 2 running — pipeline executes inside this request (may take 1–5 min)...")
            t0 = time.time()
            r = client.post("searches/from-text", json=create_body)
            elapsed = time.time() - t0
            r.raise_for_status()
            search_data = r.json()["data"]
            search_id = search_data["id"]
            run_id = search_data.get("run_id")
            reporter.step(
                "STEP 2 — POST /searches/from-text  [save + full 11-step pipeline]",
                request=create_body,
                response=r.json(),
                notes=(
                    f"Pipeline completed in {elapsed:.1f}s. "
                    "Internally ran: field expansion (AI #2) → 6 source fetchers → "
                    "normalize → dedup → BM25+cosine pre-score → Groq enrichment (AI #3) → "
                    "DB save → notifications."
                ),
            )

            # ── STEP 3: Get search with AI expansion cache ────────────────────
            r = client.get(f"searches/{search_id}")
            r.raise_for_status()
            search_full = r.json()["data"]
            expansion = search_full.get("field_expansion_cache") or {}
            reporter.step(
                "STEP 3 — GET /searches/{id}  [view AI #2 field expansion cache]",
                request={"search_id": search_id},
                response={
                    "search_summary": {
                        k: search_full.get(k)
                        for k in (
                            "id", "name", "job_title", "field_domain",
                            "work_mode", "experience_level", "last_run_at",
                        )
                    },
                    "field_expansion_cache": expansion,
                },
                notes=(
                    "field_expansion_cache is Groq AI #2 output (cached 24h). "
                    "Contains search_queries, primary_keywords, negative_keywords, "
                    "related_titles, ideal_profile — used by fetchers and scoring."
                ),
            )

            # ── STEP 4: Job results ───────────────────────────────────────────
            results_params = {"page": 1, "page_size": 10, "only_new": False}
            r = client.get(f"searches/{search_id}/results", params=results_params)
            r.raise_for_status()
            results_body = r.json()
            total = results_body.get("total", 0)
            # Trim long descriptions in report for readability
            trimmed_results = []
            for item in results_body.get("data", []):
                entry = dict(item)
                job = entry.get("job", {})
                if job.get("description_summary") and len(job["description_summary"]) > 200:
                    job = dict(job)
                    job["description_summary"] = job["description_summary"][:200] + "..."
                    entry["job"] = job
                trimmed_results.append(entry)

            reporter.step(
                "STEP 4 — GET /searches/{id}/results  [AI-enriched jobs]",
                request={"search_id": search_id, **results_params},
                response={
                    "total": total,
                    "page": results_body.get("page"),
                    "page_size": results_body.get("page_size"),
                    "data": trimmed_results,
                },
                notes=(
                    "Each result has relevance_score (Groq AI #3, 0–1), match_reason, gaps, "
                    "plus job summary/skills from Groq. Sorted by relevance_score desc."
                ),
            )

            # ── STEP 5: Notifications ─────────────────────────────────────────
            r = client.get("notifications", params={"unread_only": False})
            r.raise_for_status()
            reporter.step(
                "STEP 5 — GET /notifications",
                request={"unread_only": False},
                response=r.json(),
                notes="Created when new jobs score >= NOTIFICATION_SCORE_THRESHOLD (default 7/10).",
            )

            # ── STEP 6: Source health ─────────────────────────────────────────
            r = client.get("health/sources")
            r.raise_for_status()
            reporter.step(
                "STEP 6 — GET /health/sources",
                response=r.json(),
                notes="Shows how many jobs each source contributed in the last 24 hours.",
            )

            # ── Summary ───────────────────────────────────────────────────────
            print("\n" + "═" * 72)
            print("  FLOW SUMMARY")
            print("═" * 72)
            print(f"  Search ID     : {search_id}")
            print(f"  Run ID        : {run_id}")
            print(f"  Pipeline time : {elapsed:.1f}s")
            print(f"  Jobs matched  : {total}")
            if parsed:
                print(f"  Parsed title  : {parsed.get('job_title')}")
                print(f"  Parsed field  : {parsed.get('field_domain')}")
                print(f"  AI confidence : {parsed.get('confidence')}")
            if expansion:
                print(f"  Search queries: {expansion.get('search_queries', [])[:3]}")
            if trimmed_results:
                top = trimmed_results[0]
                print(f"  Top job score : {top.get('relevance_score')}")
                print(f"  Top match     : {top.get('job', {}).get('title')} @ {top.get('job', {}).get('company_name')}")
                print(f"  match_reason  : {top.get('match_reason', 'N/A')[:120]}...")

            reporter.report["summary"] = {
                "search_id": search_id,
                "run_id": run_id,
                "pipeline_seconds": round(elapsed, 1),
                "jobs_matched": total,
                "parsed_intent": parsed,
                "field_expansion": expansion,
            }

            # ── Cleanup ───────────────────────────────────────────────────────
            if not args.keep_data and search_id:
                r = client.delete(f"searches/{search_id}")
                print(f"\n🧹 Cleanup: deleted search {search_id} → HTTP {r.status_code}")

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP {e.response.status_code}: {e.response.text[:500]}")
        return 1
    except httpx.ConnectError:
        print(f"\n❌ Cannot connect to {args.base_url}. Start API: python3 main.py")
        return 1
    except Exception as e:
        print(f"\n❌ {type(e).__name__}: {e}")
        return 1

    if args.output:
        reporter.save(args.output)

    print("\n✅ Complete flow test finished!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
