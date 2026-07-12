#!/usr/bin/env python3
"""Test the full fetch pipeline — every registered source, exactly as a real search runs."""
import asyncio
import uuid
from datetime import datetime, timezone

from schemas.saved_search import SavedSearchResponse
from services.pipeline.fetcher_service import fetch_all_sources


def sample_search() -> SavedSearchResponse:
    now = datetime.now(timezone.utc)
    return SavedSearchResponse(
        id=uuid.uuid4(),
        name="All Sources Test",
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


async def main() -> None:
    search = sample_search()
    expansion = {"search_queries": ["python developer"]}

    print("=" * 72)
    print("Full pipeline fetch test — Python developer · United States")
    print("=" * 72)

    jobs, stats = await fetch_all_sources(search, expansion)

    print(f"\n{'Source':<14} {'Jobs':<6} Error")
    print("-" * 72)
    for source, s in sorted(stats.items()):
        err = (s["error"] or "")[:45]
        print(f"{source:<14} {s['fetched']:<6} {err}")
    print("-" * 72)
    print(f"Total jobs fetched: {len(jobs)} from {len(stats)} sources")

    linkedin = [j for j in jobs if j.source == "linkedin"]
    if linkedin:
        print(f"\nLinkedIn sample ({len(linkedin)} jobs):")
        for j in linkedin[:3]:
            print(f"  - {j.title} @ {j.company_name} ({j.location})")


if __name__ == "__main__":
    asyncio.run(main())
