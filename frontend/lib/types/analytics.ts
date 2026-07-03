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
