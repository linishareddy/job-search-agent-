export interface CompanySlug {
  name: string;
  slug: string;
  source: "greenhouse" | "lever" | "ashby" | string;
}

export interface SavedSearch {
  id: string;
  name: string;
  job_title: string;
  field_domain: string;
  location?: string | null;
  work_mode?: string | null;
  experience_level?: string | null;
  employment_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  company_slugs: CompanySlug[];
  poll_interval_minutes: number;
  posted_within_days?: number | null;
  is_active: boolean;
  last_run_at?: string | null;
  field_expansion_cache?: FieldExpansion | null;
  created_at: string;
  updated_at: string;
}

export interface FieldExpansion {
  search_queries?: string[];
  primary_keywords?: string[];
  negative_keywords?: string[];
  related_titles?: string[];
  ideal_profile?: string;
}

export interface SavedSearchCreate {
  name: string;
  job_title: string;
  field_domain: string;
  location?: string | null;
  work_mode?: string | null;
  experience_level?: string | null;
  employment_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  company_slugs?: CompanySlug[];
  poll_interval_minutes?: number;
  posted_within_days?: number | null;
}

export interface SavedSearchUpdate {
  name?: string;
  job_title?: string;
  field_domain?: string;
  location?: string | null;
  work_mode?: string | null;
  experience_level?: string | null;
  employment_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  company_slugs?: CompanySlug[];
  poll_interval_minutes?: number;
  posted_within_days?: number | null;
  is_active?: boolean;
}

export interface ParsedSearchIntent {
  job_title: string;
  field_domain: string;
  name: string;
  location?: string | null;
  work_mode?: string | null;
  experience_level?: string | null;
  employment_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  company_slugs: CompanySlug[];
  confidence: number;
  ambiguities: string[];
  raw_text: string;
}

export interface CreateFromTextPayload {
  text: string;
  overrides?: SavedSearchUpdate | null;
  run_immediately?: boolean;
}

export interface CreateFromTextResult extends SavedSearch {
  run_id?: string;
}
