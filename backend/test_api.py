"""
API integration test script — exercises all endpoints and prints request/response payloads.

Usage:
    python test_api.py              # fast tests (no pipeline run)
    python test_api.py --pipeline   # also trigger full job-search pipeline (slow, needs Groq + API keys)
    python test_api.py --base-url http://localhost:8000/api/v1
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
SAMPLE_TEXT = (
    "Remote senior healthcare analyst in the US, full time, 90k-130k, "
    "focusing on EHR and claims data"
)


def pp(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def call(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    params: dict | None = None,
    expected: int | tuple[int, ...] = 200,
    timeout: float = 30.0,
) -> httpx.Response:
    # Paths must be relative (no leading slash) so httpx appends to base_url correctly.
    rel_path = path.lstrip("/")
    url = path if path.startswith("http") else rel_path
    section(f"{method} /{rel_path}")

    if json_body is not None:
        print("\n📤 REQUEST BODY:")
        print(pp(json_body))
    if params:
        print("\n📤 QUERY PARAMS:")
        print(pp(params))

    response = client.request(method, url, json=json_body, params=params, timeout=timeout)

    print(f"\n📥 STATUS: {response.status_code}")
    if response.content:
        try:
            print("📥 RESPONSE:")
            print(pp(response.json()))
        except Exception:
            print(response.text)
    else:
        print("📥 RESPONSE: (empty body)")

    codes = (expected,) if isinstance(expected, int) else expected
    if response.status_code not in codes:
        raise AssertionError(f"Expected {codes}, got {response.status_code}")

    return response


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Job Search Agent APIs")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Run full pipeline (slow; needs GROQ_API_KEY and job source keys)",
    )
    parser.add_argument(
        "--keep-data",
        action="store_true",
        help="Do not delete the test search/company at the end",
    )
    args = parser.parse_args()

    created_search_id: str | None = None
    created_company_id: str | None = None
    parsed: dict | None = None
    passed = 0
    failed = 0

    print(f"\n🚀 Job Search Agent API Tests")
    print(f"   Base URL: {args.base_url}")

    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), follow_redirects=True) as client:
            # ── Health ────────────────────────────────────────────────────────
            call(client, "GET", "/health")
            passed += 1

            call(client, "GET", "/health/sources")
            passed += 1

            # ── Parse text (Groq) ───────────────────────────────────────────────
            parse_payload = {"text": SAMPLE_TEXT}
            r = call(client, "POST", "/searches/parse-text", json_body=parse_payload, timeout=60.0)
            parsed = r.json()["data"]
            passed += 1

            # ── Create structured search ──────────────────────────────────────
            structured_payload = {
                "name": f"API Test Search {uuid.uuid4().hex[:8]}",
                "job_title": "Software Engineer",
                "field_domain": "Backend Python, FastAPI, PostgreSQL",
                "location": "United States",
                "work_mode": "remote",
                "experience_level": "senior",
                "employment_type": "full_time",
                "poll_interval_minutes": 60,
            }
            r = call(client, "POST", "/searches", json_body=structured_payload, expected=201, timeout=30.0)
            created_search_id = r.json()["data"]["id"]
            passed += 1

            # ── Create from text (no immediate run by default) ──────────────────
            from_text_payload = {
                "text": SAMPLE_TEXT,
                "run_immediately": args.pipeline,
                "overrides": {"name": f"From-Text Test {uuid.uuid4().hex[:8]}"},
            }
            r = call(
                client,
                "POST",
                "/searches/from-text",
                json_body=from_text_payload,
                expected=201,
                timeout=120.0 if args.pipeline else 60.0,
            )
            from_text_search_id = r.json()["data"]["id"]
            run_id = r.json()["data"].get("run_id")
            passed += 1

            if args.pipeline and run_id:
                print(f"\n⏳ Pipeline started (run_id={run_id}). Waiting 15s before checking results...")
                time.sleep(15)

            # ── List searches ─────────────────────────────────────────────────
            call(client, "GET", "/searches")
            passed += 1

            # ── Get single search ─────────────────────────────────────────────
            call(client, "GET", f"/searches/{created_search_id}")
            passed += 1

            # ── Update search ─────────────────────────────────────────────────
            update_payload = {"salary_min": 100000, "salary_max": 150000}
            call(client, "PUT", f"/searches/{created_search_id}", json_body=update_payload)
            passed += 1

            # ── Manual pipeline trigger (structured search) ─────────────────────
            if args.pipeline:
                r = call(
                    client,
                    "POST",
                    f"/searches/{created_search_id}/run",
                    expected=202,
                    timeout=180.0,
                )
                manual_run_id = r.json()["data"]["run_id"]
                print(f"\n⏳ Manual pipeline run_id={manual_run_id}. Waiting 20s...")
                time.sleep(20)
                passed += 1

            # ── Results ───────────────────────────────────────────────────────
            results_search_id = from_text_search_id if args.pipeline else created_search_id
            call(
                client,
                "GET",
                f"/searches/{results_search_id}/results",
                params={"page": 1, "page_size": 5, "only_new": False},
            )
            passed += 1

            # ── Companies ─────────────────────────────────────────────────────
            call(client, "GET", "/companies")
            passed += 1

            company_payload = {
                "name": "Stripe",
                "slug": "stripe",
                "source": "greenhouse",
            }
            r = call(client, "POST", "/companies", json_body=company_payload, expected=201)
            created_company_id = r.json()["data"]["id"]
            passed += 1

            # ── Notifications ───────────────────────────────────────────────
            call(client, "GET", "/notifications", params={"unread_only": False})
            passed += 1

            # ── Cleanup ───────────────────────────────────────────────────────
            if not args.keep_data:
                section("DELETE /searches/{id} (cleanup)")
                for sid in {created_search_id, from_text_search_id}:
                    if sid:
                        resp = client.delete(f"searches/{sid}")
                        print(f"  deleted {sid} → {resp.status_code}")
                passed += 1

                if created_company_id:
                    section("DELETE /companies/{id} (cleanup)")
                    resp = client.delete(f"companies/{created_company_id}")
                    print(f"  deleted {created_company_id} → {resp.status_code}")
                    passed += 1

    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        failed += 1
    except httpx.ConnectError:
        print(f"\n❌ Cannot connect to {args.base_url}")
        print("   Make sure the API is running: python main.py")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        failed += 1

    section("SUMMARY")
    print(f"  Passed checks: {passed}")
    print(f"  Failed:        {failed}")
    if not args.pipeline:
        print("\n  Tip: run with --pipeline to test full job fetch + Groq enrichment (slower)")
    if parsed:
        print("\n  Parse-text preview (job_title / field_domain):")
        print(f"    job_title:    {parsed.get('job_title')}")
        print(f"    field_domain: {parsed.get('field_domain')}")
        print(f"    confidence:   {parsed.get('confidence')}")

    if failed:
        return 1

    print("\n✅ All API tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
