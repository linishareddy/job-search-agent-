"""
Full portal test — exercises ALL 6 job sources + every API step.
Saves complete JSON report grouped by portal (source).

Portals tested:
  BREADTH: adzuna, jooble, remotive
  DEPTH (ATS): greenhouse, lever, ashby

Usage:
  python3 test_all_portals.py
  python3 test_all_portals.py --output reports/full_portal_test.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_TEXT = (
    "Remote senior healthcare analyst in the US, full time, 90k-130k, "
    "focusing on EHR and claims data"
)

# Known-working public ATS board slugs (free APIs, no auth)
ATS_COMPANIES = [
    {"name": "Stripe", "slug": "stripe", "source": "greenhouse"},
    {"name": "Airbnb", "slug": "airbnb", "source": "greenhouse"},
    {"name": "Netflix", "slug": "netflix", "source": "lever"},
    {"name": "Linear", "slug": "linear", "source": "ashby"},
]

ALL_PORTALS = ["adzuna", "jooble", "remotive", "greenhouse", "lever", "ashby"]


def pp(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


class PortalTestReport:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {
            "meta": {
                "started_at": datetime.now(timezone.utc).isoformat(),
                "portals_tested": ALL_PORTALS,
                "ats_companies_configured": ATS_COMPANIES,
            },
            "steps": [],
            "results_by_portal": {},
            "summary": {},
        }

    def add_step(self, name: str, request: Any, response: Any, notes: str = "") -> None:
        self.data["steps"].append({
            "step": name,
            "notes": notes,
            "request": request,
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def save(self, path: str) -> None:
        self.data["meta"]["finished_at"] = datetime.now(timezone.utc).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, default=str)
        print(f"\n💾 Complete JSON report saved: {path}")


def api(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    rel = path.lstrip("/")
    r = client.request(method, rel, **kwargs)
    r.raise_for_status()
    if r.status_code == 204:
        return {"status": 204, "body": None}
    return r.json()


def fetch_all_results(client: httpx.Client, search_id: str, page_size: int = 100) -> dict:
    page = 1
    all_items: list[dict] = []
    total = 0
    while True:
        body = api(
            client, "GET", f"searches/{search_id}/results",
            params={"page": page, "page_size": page_size, "only_new": False},
        )
        items = body.get("data", [])
        total = body.get("total", 0)
        all_items.extend(items)
        if len(all_items) >= total or not items:
            break
        page += 1
    return {"total": total, "data": all_items, "pages_fetched": page}


def group_by_portal(results: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        source = (item.get("job") or {}).get("source", "unknown")
        grouped[source].append(item)
    return dict(grouped)


def portal_summary(grouped: dict[str, list[dict]]) -> dict[str, Any]:
    out = {}
    for portal in ALL_PORTALS:
        jobs = grouped.get(portal, [])
        scores = [j.get("relevance_score", 0) for j in jobs]
        out[portal] = {
            "count": len(jobs),
            "avg_relevance_score": round(sum(scores) / len(scores), 3) if scores else 0,
            "top_score": round(max(scores), 3) if scores else 0,
            "sample_titles": [
                j.get("job", {}).get("title") for j in sorted(jobs, key=lambda x: -x.get("relevance_score", 0))[:3]
            ],
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--output", default="reports/full_portal_test.json")
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--keep-data", action="store_true")
    args = parser.parse_args()

    report = PortalTestReport()
    created_company_ids: list[str] = []
    search_id: str | None = None

    print("=" * 72)
    print("  FULL PORTAL TEST — all 6 sources + complete JSON output")
    print("=" * 72)
    print(f"  Output file: {args.output}")
    print(f"  Portals: {', '.join(ALL_PORTALS)}")

    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=args.timeout) as client:
            # ── STEP 0: Health ────────────────────────────────────────────────
            health = api(client, "GET", "health")
            report.add_step("0_health", None, health, "API + DB check")
            print("\n✓ Health OK")

            source_health_before = api(client, "GET", "health/sources")
            report.add_step("0b_sources_before", None, source_health_before, "Jobs per portal before run")

            # ── STEP 1: Register ATS companies ────────────────────────────────
            companies_added = []
            for co in ATS_COMPANIES:
                try:
                    resp = api(client, "POST", "companies", json=co)
                    cid = resp["data"]["id"]
                    created_company_ids.append(cid)
                    companies_added.append(resp)
                except httpx.HTTPStatusError as e:
                    companies_added.append({"error": str(e), "company": co, "body": e.response.text})
            report.add_step(
                "1_register_ats_companies",
                {"companies": ATS_COMPANIES},
                companies_added,
                "Registers Greenhouse/Lever/Ashby company slugs for depth layer",
            )
            print(f"✓ Registered {len(ATS_COMPANIES)} ATS companies")

            # ── STEP 2: Parse text (AI #1) ──────────────────────────────────
            parse_req = {"text": args.text}
            parse_resp = api(client, "POST", "searches/parse-text", json=parse_req)
            report.add_step("2_parse_text_ai1", parse_req, parse_resp, "Groq intent parser")
            print("✓ AI parse-text done")

            # ── STEP 3: Create search + run pipeline with ATS slugs ───────────
            create_req = {
                "text": args.text,
                "run_immediately": True,
                "overrides": {
                    "name": f"Portal Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "company_slugs": ATS_COMPANIES,
                },
            }
            print("\n⏳ Running full pipeline (all 6 portals) — may take 1–3 min...")
            t0 = time.time()
            create_resp = api(client, "POST", "searches/from-text", json=create_req)
            pipeline_secs = round(time.time() - t0, 1)
            search_id = create_resp["data"]["id"]
            run_id = create_resp["data"].get("run_id")
            report.add_step(
                "3_from_text_pipeline",
                create_req,
                create_resp,
                f"Full 11-step pipeline across all portals. Took {pipeline_secs}s",
            )
            print(f"✓ Pipeline done in {pipeline_secs}s (run_id={run_id})")

            # ── STEP 4: Search detail + AI expansion cache ──────────────────
            search_detail = api(client, "GET", f"searches/{search_id}")
            report.add_step(
                "4_search_detail_ai2_expansion",
                {"search_id": search_id},
                search_detail,
                "field_expansion_cache = Groq AI #2 output used by fetchers",
            )
            print("✓ Search detail + field expansion cached")

            # ── STEP 5: ALL results (paginated) ─────────────────────────────
            all_results = fetch_all_results(client, search_id, page_size=100)
            grouped = group_by_portal(all_results["data"])
            report.data["results_by_portal"] = grouped
            report.add_step(
                "5_all_results",
                {"search_id": search_id, "page_size": 100},
                {
                    "total": all_results["total"],
                    "pages_fetched": all_results["pages_fetched"],
                    "by_portal_count": {p: len(grouped.get(p, [])) for p in ALL_PORTALS},
                    "full_results": all_results["data"],
                },
                "Complete job results with AI scores, match_reason, gaps — grouped by portal below",
            )
            print(f"✓ Fetched {all_results['total']} total results")

            # ── STEP 6: Notifications ───────────────────────────────────────
            notifs = api(client, "GET", "notifications", params={"unread_only": False})
            report.add_step("6_notifications", {"unread_only": False}, notifs, "Alerts for score >= 7/10")
            print("✓ Notifications fetched")

            # ── STEP 7: Source health after ─────────────────────────────────
            source_health_after = api(client, "GET", "health/sources")
            report.add_step("7_sources_after", None, source_health_after, "Jobs per portal in last 24h")
            print("✓ Source health after run")

            # ── STEP 8: List companies ──────────────────────────────────────
            companies_list = api(client, "GET", "companies")
            report.add_step("8_companies_list", None, companies_list, "All registered ATS companies")

            # ── Summary ─────────────────────────────────────────────────────
            summary = {
                "search_id": search_id,
                "run_id": run_id,
                "pipeline_seconds": pipeline_secs,
                "total_jobs_matched": all_results["total"],
                "portal_breakdown": portal_summary(grouped),
                "parsed_intent": parse_resp.get("data"),
                "field_expansion": search_detail.get("data", {}).get("field_expansion_cache"),
                "notifications_count": notifs.get("total", 0),
                "sources_24h_after": source_health_after.get("data"),
            }
            report.data["summary"] = summary

            print("\n" + "=" * 72)
            print("  PORTAL BREAKDOWN")
            print("=" * 72)
            for portal in ALL_PORTALS:
                info = summary["portal_breakdown"][portal]
                print(f"  {portal:12} → {info['count']:3} jobs  (top score: {info['top_score']})")
                for t in info["sample_titles"]:
                    if t:
                        print(f"               • {t[:60]}")
            print(f"\n  Total matched: {all_results['total']}  |  Pipeline: {pipeline_secs}s")

            # ── Cleanup ───────────────────────────────────────────────────
            if not args.keep_data:
                if search_id:
                    client.delete(f"searches/{search_id}")
                for cid in created_company_ids:
                    try:
                        client.delete(f"companies/{cid}")
                    except Exception:
                        pass
                print("\n🧹 Test data cleaned up (use --keep-data to retain)")

    except httpx.ConnectError:
        print("\n❌ Cannot connect to API. Start server: cd backend && python3 main.py")
        return 1
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP {e.response.status_code}: {e.response.text[:800]}")
        report.add_step("error", None, {"status": e.response.status_code, "body": e.response.text})
        report.save(args.output)
        return 1
    except Exception as e:
        print(f"\n❌ {type(e).__name__}: {e}")
        report.add_step("error", None, {"error": str(e)})
        report.save(args.output)
        return 1

    report.save(args.output)
    print("\n✅ Full portal test complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
