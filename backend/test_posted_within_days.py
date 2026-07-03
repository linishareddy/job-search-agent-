"""
Complete test for posted_within_days filter — config + API + actual result counts.

Usage:
    python test_posted_within_days.py
    python test_posted_within_days.py --search-id <uuid>
    python test_posted_within_days.py --save reports/posted_within_days_test.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"
REPORT_PATH = "reports/posted_within_days_test.json"


def pp(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def days_ago(iso: str | None) -> str:
    if not iso:
        return "unknown"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return f"{delta.days}d ago"
    except Exception:
        return "?"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--search-id", default=None, help="Use existing search with results")
    parser.add_argument("--save", default=REPORT_PATH)
    args = parser.parse_args()

    report: dict[str, Any] = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "steps": [],
    }

    with httpx.Client(base_url=args.base_url, timeout=60.0) as client:
        # Health
        health = client.get("/health").json()
        report["health"] = health
        print("✓ Health:", health.get("data", {}).get("status"))

        search_id = args.search_id

        # Find a search that already has results if not provided
        if not search_id:
            searches = client.get("/searches").json().get("data", [])
            for s in searches:
                sid = s["id"]
                r = client.get(f"/searches/{sid}/results", params={"page": 1, "page_size": 1})
                if r.status_code == 200 and r.json().get("total", 0) > 0:
                    search_id = sid
                    report["auto_selected_search"] = {"id": sid, "name": s.get("name"), "total_jobs": r.json()["total"]}
                    break

        if not search_id:
            print("✗ No search with results found. Run test_all_portals.py first.")
            return 1

        print(f"✓ Using search: {search_id}")

        # --- 1. Baseline (no filter) ---
        baseline = client.get(f"/searches/{search_id}/results", params={"page": 1, "page_size": 100}).json()
        baseline_total = baseline.get("total", 0)
        report["steps"].append({"step": "baseline_no_filter", "total": baseline_total})
        print(f"\n1. No filter          → {baseline_total} jobs")

        # --- 2. Filter sweeps ---
        filter_days = [1, 3, 7, 14, 30, 60, 90, 365]
        filter_results: dict[str, int] = {}
        for days in filter_days:
            r = client.get(
                f"/searches/{search_id}/results",
                params={"page": 1, "page_size": 1, "posted_within_days": days},
            )
            total = r.json().get("total", 0) if r.status_code == 200 else -1
            filter_results[str(days)] = total
            print(f"2. Last {days:3d} days      → {total} jobs")

        report["steps"].append({"step": "filter_sweep", "totals_by_days": filter_results})

        # --- 3. Sample jobs for last 7 days (full detail) ---
        last_7 = client.get(
            f"/searches/{search_id}/results",
            params={"page": 1, "page_size": 20, "posted_within_days": 7},
        ).json()
        last_7_jobs = []
        for item in last_7.get("data", []):
            job = item.get("job", {})
            last_7_jobs.append({
                "title": job.get("title"),
                "company": job.get("company_name"),
                "source": job.get("source"),
                "posted_at": job.get("posted_at"),
                "posted_ago": days_ago(job.get("posted_at")),
                "relevance_score": item.get("relevance_score"),
            })
        report["steps"].append({
            "step": "last_7_days_sample",
            "total": last_7.get("total"),
            "jobs": last_7_jobs,
        })
        print(f"\n3. Last 7 days sample ({last_7.get('total')} total):")
        for j in last_7_jobs[:10]:
            print(f"   • {j['title'][:50]:50} | {j['company'][:20]:20} | {j['posted_ago']:10} | score {j['relevance_score']}")

        # --- 4. Saved default on search config ---
        create_body = {
            "name": "Time Filter Config Test",
            "job_title": "Software Engineer",
            "field_domain": "Backend",
            "posted_within_days": 14,
        }
        created = client.post("/searches", json=create_body).json()
        cfg_id = created["data"]["id"]
        report["steps"].append({"step": "create_with_config", "search_id": cfg_id, "posted_within_days": 14})

        got = client.get(f"/searches/{cfg_id}").json()
        assert got["data"]["posted_within_days"] == 14, "Config not saved"
        print(f"\n4. Created search with posted_within_days=14 → saved OK (id={cfg_id[:8]}...)")

        # --- 5. Validation errors ---
        bad_cases = [
            ("body_0", "POST", "/searches", {"name": "X", "job_title": "Y", "field_domain": "Z", "posted_within_days": 0}),
            ("body_400", "POST", "/searches", {"name": "X", "job_title": "Y", "field_domain": "Z", "posted_within_days": 400}),
            ("query_0", "GET", f"/searches/{search_id}/results", None, {"posted_within_days": 0}),
            ("query_400", "GET", f"/searches/{search_id}/results", None, {"posted_within_days": 400}),
        ]
        validation = []
        for name, method, path, body, *rest in bad_cases:
            params = rest[0] if rest else None
            if method == "POST":
                r = client.post(path, json=body)
            else:
                r = client.get(path, params=params)
            ok = r.status_code == 422
            validation.append({"case": name, "status": r.status_code, "passed": ok})
            print(f"5. Validation {name:12} → HTTP {r.status_code} {'✓' if ok else '✗'}")
        report["steps"].append({"step": "validation", "cases": validation})

        # --- 6. Saved default applies when no query param ---
        client.put(f"/searches/{search_id}", json={"posted_within_days": 30})
        default_30 = client.get(f"/searches/{search_id}/results", params={"page": 1, "page_size": 1}).json()
        override_7 = client.get(
            f"/searches/{search_id}/results",
            params={"page": 1, "page_size": 1, "posted_within_days": 7},
        ).json()
        report["steps"].append({
            "step": "saved_default_vs_override",
            "saved_default_days": 30,
            "no_query_param_total": default_30.get("total"),
            "override_7_days_total": override_7.get("total"),
        })
        print(f"\n6. Saved default=30 (no param) → {default_30.get('total')} jobs")
        print(f"   Override ?posted_within_days=7 → {override_7.get('total')} jobs")

        # Summary table
        report["summary"] = {
            "search_id": search_id,
            "baseline_total": baseline_total,
            "filter_totals": filter_results,
            "last_7_days_total": last_7.get("total"),
            "all_validation_passed": all(v["passed"] for v in validation),
        }

    # Save report
    import os
    os.makedirs(os.path.dirname(args.save) or ".", exist_ok=True)
    with open(args.save, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Search ID:     {search_id}")
    print(f"Baseline:      {baseline_total} jobs (no filter)")
    print(f"Last 1 day:    {filter_results.get('1')} jobs")
    print(f"Last 7 days:   {filter_results.get('7')} jobs")
    print(f"Last 30 days:  {filter_results.get('30')} jobs")
    print(f"Last 365 days: {filter_results.get('365')} jobs")
    print(f"Report saved:  {args.save}")
    print("=" * 72)

    if not all(v["passed"] for v in validation):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
