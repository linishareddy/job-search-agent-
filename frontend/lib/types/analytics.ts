export interface Bucket {
  label: string;
  count: number;
}

export interface SalaryStats {
  listed_count: number;
  unlisted_count: number;
  median: number | null;
  average: number | null;
  histogram: Bucket[];
}

export interface SearchAnalytics {
  total_jobs: number;
  salary: SalaryStats;
  top_skills: Bucket[];
  by_source: Bucket[];
  by_work_mode: Bucket[];
  postings_over_time: Bucket[];
}

export interface SearchCounts {
  total: number;
  active: number;
  paused: number;
}

export interface JobCounts {
  unique: number;
  total_matches: number;
  new_7d: number;
  new_24h: number;
}

export interface TrackerStats {
  saved: number;
  applied: number;
  interviewing: number;
  offer: number;
  rejected: number;
}

export interface SearchSummary {
  search_id: string;
  name: string;
  job_count: number;
  new_count: number;
  median_salary: number | null;
}

export interface GlobalAnalytics {
  searches: SearchCounts;
  jobs: JobCounts;
  tracker: TrackerStats;
  salary: SalaryStats;
  top_skills: Bucket[];
  by_source: Bucket[];
  by_work_mode: Bucket[];
  postings_over_time: Bucket[];
  by_search: SearchSummary[];
}
