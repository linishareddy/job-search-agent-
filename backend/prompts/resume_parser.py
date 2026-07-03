SYSTEM_PROMPT = """You are a resume parser. Return ONLY valid JSON, no explanation."""

USER_TEMPLATE = """Extract structured information from this resume text:

\"\"\"
{text}
\"\"\"

Return a JSON object with exactly these keys:
{{
  "skills": ["<technical and professional skills, e.g. 'Python', 'Project Management'>"],
  "job_titles": ["<job titles this person has held or is qualified for, most recent first>"],
  "experience_level": "<one of: entry | mid | senior | lead>",
  "years_experience": <estimated total years of professional experience, float or integer>,
  "summary": "<a 1-2 sentence summary of this candidate's background and focus>"
}}

Rules:
- "skills" should be concise, deduplicated, most relevant first (max 25).
- "job_titles" should reflect actual roles found in the resume, not guesses.
- If something can't be determined, use an empty list, null, or your best estimate for years_experience."""
