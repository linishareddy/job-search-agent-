export interface ParsedResumeData {
  skills: string[];
  job_titles: string[];
  experience_level: string | null;
  years_experience: number | null;
  summary: string | null;
}

export interface Resume {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  parse_status: "pending" | "parsed" | "failed";
  parsed_data: ParsedResumeData | null;
  uploaded_at: string;
  updated_at: string;
}

export interface ResumeDetail extends Resume {
  raw_text: string;
}

export interface ExtractedResumeText {
  filename: string;
  text: string;
}

export interface CoverLetterFromResumePayload {
  job_title: string;
  company_name: string;
  job_description?: string;
}

export interface TailoringSuggestion {
  section: string;
  current: string;
  suggested: string;
  reason: string;
}

export interface ResumeTailoring {
  id: string;
  resume_id: string;
  job_id: string;
  match_score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  suggestions: TailoringSuggestion[];
  summary_rewrite: string | null;
  gaps: string[];
  tailored_resume: string;
  created_at: string;
}
