#!/usr/bin/env python3
"""Test all JobSpy-supported job boards."""
import asyncio
import uuid
from datetime import datetime, timezone

from schemas.saved_search import SavedSearchResponse
from services.fetchers.jobspy_fetchers import ALL_JOBSPY_FETCHERS


def sample_search() -> SavedSearchResponse:
    now = datetime.now(timezone.utc)
    return SavedSearchResponse(
        id=uuid.uuid4(),
        name="JobSpy Test",
        job_title="Python developer",
        field_domain="software engineering",
        location="United States",
        work_mode="any",
        experience_level="any",
        employment_type="any",
        company_slugs=[],
        poll_interval_minutes=60,
        is_active=True,
        last_run_at=None,
        field_expansion_cache=None,
        created_at=now,
        updated_at=now,
    )


async def test_fetcher(fetcher) -> dict:
    search = sample_search()
    expansion = {"search_queries": ["python engineer"]}
    try:
        jobs = await fetcher.fetch(search, expansion)
        sample = jobs[0] if jobs else None
        return {
            "source": fetcher.source_name,
            "status": "ok",
            "count": len(jobs),
            "sample_title": sample.title if sample else None,
            "sample_company": sample.company_name if sample else None,
            "sample_url": sample.apply_url if sample else None,
        }
    except Exception as e:
        return {"source": fetcher.source_name, "status": "error", "count": 0, "error": str(e)[:120]}


async def main() -> None:
    print("=" * 72)
    print("JobSpy boards test — Python developer · United States")
    print("=" * 72)

    # Run sequentially to avoid rate limits from parallel scraping
    results = []
    for fetcher in ALL_JOBSPY_FETCHERS:
        print(f"\nFetching {fetcher.source_name}...")
        results.append(await test_fetcher(fetcher))

    print("\n" + "=" * 72)
    print(f"{'Source':<16} {'Status':<8} {'Count':<6} Sample / Error")
    print("-" * 72)
    for r in results:
        detail = ""
        if r.get("sample_title"):
            detail = f"{r['sample_title'][:40]} @ {r.get('sample_company', '')[:20]}"
            if r.get("sample_url"):
                detail += f"\n{'':16} {'':8} {'':6} {r['sample_url']}"
        elif r.get("error"):
            detail = r["error"]
        print(f"{r['source']:<16} {r['status']:<8} {r['count']:<6} {detail.split(chr(10))[0]}")

    ok = sum(1 for r in results if r["status"] == "ok" and r["count"] > 0)
    total = sum(r["count"] for r in results)
    print("-" * 72)
    print(f"Summary: {ok}/{len(results)} boards returned jobs, {total} total jobs")


if __name__ == "__main__":
    asyncio.run(main())
