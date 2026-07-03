export interface AtsCompany {
  id: string;
  name: string;
  slug: string;
  source: string;
  is_active: boolean;
  created_at: string;
}

export interface AtsCompanyCreate {
  name: string;
  slug: string;
  source: "greenhouse" | "lever" | "ashby";
}

export interface Notification {
  id: string;
  search_id?: string | null;
  run_id?: string | null;
  message: string;
  new_job_count: number;
  is_read: boolean;
  created_at: string;
}

export interface HealthStatus {
  database: string;
  status: string;
}

export interface SourceHealth {
  jobs_last_24h: number;
}

export type SourceHealthMap = Record<string, SourceHealth>;
