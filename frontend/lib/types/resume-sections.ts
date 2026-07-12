export interface ContactSection {
  name: string;
  email: string;
  phone: string;
  location: string;
  linkedin: string;
  github: string;
  website: string;
}

export interface ExperienceEntry {
  title: string;
  company: string;
  location: string;
  start_date: string;
  end_date: string;
  bullets: string[];
}

export interface EducationEntry {
  degree: string;
  institution: string;
  location: string;
  graduation_date: string;
  details: string[];
}

export interface TailoredResumeSections {
  contact: ContactSection;
  summary: string;
  skills: string[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  certifications: string[];
  job_titles: string[];
  experience_level: string | null;
  years_experience: number | null;
}
