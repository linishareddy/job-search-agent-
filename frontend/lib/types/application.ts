import type { Job } from "@/lib/types/job";

export type ApplicationStatus =
  | "saved"
  | "ready_to_apply"
  | "applied"
  | "interviewing"
  | "offer"
  | "rejected";

export interface JobApplication {
  id: string;
  job: Job;
  status: ApplicationStatus;
  notes?: string | null;
  applied_at?: string | null;
  auto_prepared: boolean;
  match_score?: number | null;
  cover_letter?: string | null;
  tailored_resume?: string | null;
  tailored_docx_available?: boolean;
  created_at: string;
  updated_at: string;
}
