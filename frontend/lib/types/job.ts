export interface Job {
  id: string;
  title: string;
  company_name: string;
  location?: string | null;
  work_mode?: string | null;
  employment_type?: string | null;
  experience_level?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency: string;
  salary_listed: boolean;
  description_summary?: string | null;
  skills: string[];
  apply_url: string;
  source: string;
  source_urls: string[];
  posted_at?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface JobSearchResult {
  id: string;
  job: Job;
  relevance_score: number;
  bm25_score?: number | null;
  cosine_score?: number | null;
  match_reason?: string | null;
  gaps?: string | null;
  is_new: boolean;
  is_dismissed: boolean;
  created_at: string;
}

export interface SearchResultsParams {
  page?: number;
  page_size?: number;
  only_new?: boolean;
  posted_within_days?: number | null;
}
