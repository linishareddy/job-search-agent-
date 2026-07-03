from abc import ABC, abstractmethod

from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse


def build_search_queries(search: SavedSearchResponse, expansion: dict, limit: int = 3) -> list[str]:
    """Broad-to-narrow query list: the plain job title first, then top expansion queries.

    Breadth sources (Adzuna/Jooble/Remotive) AND every word in a query, so a single
    specific expansion query like "healthcare analyst EHR" can match almost nothing.
    Leading with the broad title keeps recall; expansion queries add domain matches.
    """
    queries: list[str] = []
    seen: set[str] = set()
    for q in [search.job_title, *(expansion.get("search_queries") or [])]:
        q = (q or "").strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            queries.append(q)
        if len(queries) >= limit:
            break
    return queries


class BaseJobFetcher(ABC):
    source_name: str

    @abstractmethod
    async def fetch(self, search: SavedSearchResponse, expansion: dict) -> list[JobRaw]:
        """Fetch raw jobs from this source matching the given search criteria.

        Args:
            search: The saved search configuration.
            expansion: Groq field expansion dict with primary_keywords, negative_keywords, related_titles.

        Returns:
            List of raw job records, normalized to JobRaw schema.
        """
