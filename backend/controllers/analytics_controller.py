from sqlalchemy.ext.asyncio import AsyncSession

from repositories.job_application_repository import JobApplicationRepository
from repositories.job_repository import JobRepository
from repositories.saved_search_repository import SavedSearchRepository
from models.user import User
from schemas.analytics import GlobalAnalytics, JobCounts, SearchCounts, SearchSummary, TrackerStats
from services import analytics_service


class AnalyticsController:
    def __init__(self, session: AsyncSession):
        self._job_repo = JobRepository(session)
        self._search_repo = SavedSearchRepository(session)
        self._app_repo = JobApplicationRepository(session)

    async def get_overview(self, user: User, active_only: bool = False) -> GlobalAnalytics:
        searches, total_searches = await self._search_repo.get_all(user_id=user.id, page_size=1000)
        active_count = sum(1 for s in searches if s.is_active)
        paused_count = total_searches - active_count

        unique_jobs = await self._job_repo.get_all_unique_jobs(user_id=user.id, active_only=active_only)
        market = analytics_service.compute_analytics(unique_jobs)

        total_matches = await self._job_repo.count_matches(user_id=user.id, active_only=active_only)
        new_7d = await self._job_repo.count_new_matches_since(days=7, user_id=user.id, active_only=active_only)
        new_24h = await self._job_repo.count_new_matches_since(days=1, user_id=user.id, active_only=active_only)

        tracker_raw = await self._app_repo.count_by_status(user_id=user.id)
        tracker = TrackerStats(
            saved=tracker_raw.get("saved", 0),
            applied=tracker_raw.get("applied", 0),
            interviewing=tracker_raw.get("interviewing", 0),
            offer=tracker_raw.get("offer", 0),
            rejected=tracker_raw.get("rejected", 0),
        )

        by_search: list[SearchSummary] = []
        for search_id, name, job_count, new_count in await self._job_repo.get_search_summaries(user_id=user.id):
            median = None
            if job_count > 0:
                jobs = await self._job_repo.get_all_jobs_for_search(search_id)
                median = analytics_service.median_salary(jobs)
            by_search.append(
                SearchSummary(
                    search_id=search_id,
                    name=name,
                    job_count=job_count,
                    new_count=new_count,
                    median_salary=median,
                )
            )

        return GlobalAnalytics(
            searches=SearchCounts(total=total_searches, active=active_count, paused=paused_count),
            jobs=JobCounts(
                unique=len(unique_jobs),
                total_matches=total_matches,
                new_7d=new_7d,
                new_24h=new_24h,
            ),
            tracker=tracker,
            salary=market.salary,
            top_skills=market.top_skills,
            by_source=market.by_source,
            by_work_mode=market.by_work_mode,
            postings_over_time=market.postings_over_time,
            by_search=by_search,
        )
