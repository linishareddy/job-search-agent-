"""JobSpy-backed fetchers — LinkedIn and Indeed only (reliably work without proxies)."""
from constants.sources import INDEED, LINKEDIN
from services.fetchers.jobspy_base_fetcher import JobSpySiteConfig, JobSpySiteFetcher

LinkedInFetcher = JobSpySiteFetcher(
    JobSpySiteConfig(
        source=LINKEDIN,
        jobspy_site="linkedin",
        us_location_filter=True,
    )
)

IndeedFetcher = JobSpySiteFetcher(
    JobSpySiteConfig(
        source=INDEED,
        jobspy_site="indeed",
        us_location_filter=True,
        use_country_indeed=True,
    )
)

ALL_JOBSPY_FETCHERS = [LinkedInFetcher, IndeedFetcher]
