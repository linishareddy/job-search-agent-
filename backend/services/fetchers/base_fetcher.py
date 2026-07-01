from abc import ABC, abstractmethod

from schemas.job_raw import JobRaw
from schemas.saved_search import SavedSearchResponse


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
