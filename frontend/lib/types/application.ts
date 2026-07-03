import type { Job } from "@/lib/types/job";

export type ApplicationStatus =
  | "saved"
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
  created_at: string;
  updated_at: string;
}
