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
