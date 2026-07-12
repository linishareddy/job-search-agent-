SYSTEM_PROMPT = """You are a resume parser. Extract structured resume sections from plain text. \
Return ONLY valid JSON — no markdown, no code fences, no commentary."""

USER_TEMPLATE = """Extract structured information from this resume text:

\"\"\"
{text}
\"\"\"

Return a JSON object with exactly these keys:
{{
  "contact": {{
    "name": "<full name>",
    "email": "<email or empty string>",
    "phone": "<phone or empty string>",
    "location": "<city/state/country or empty string>",
    "linkedin": "<linkedin URL or handle or empty string>",
    "github": "<github URL or handle or empty string>",
    "website": "<personal website or empty string>"
  }},
  "summary": "<professional summary paragraph, or empty string if absent>",
  "skills": ["<technical and professional skills, deduplicated, max 30>"],
  "experience": [
    {{
      "title": "<job title>",
      "company": "<employer>",
      "location": "<location or empty string>",
      "start_date": "<start date as written, e.g. Jan 2020>",
      "end_date": "<end date or Present>",
      "bullets": ["<achievement/responsibility bullet>"]
    }}
  ],
  "education": [
    {{
      "degree": "<degree and field>",
      "institution": "<school name>",
      "location": "<location or empty string>",
      "graduation_date": "<graduation date or empty string>",
      "details": ["<honors, GPA, relevant coursework, etc.>"]
    }}
  ],
  "certifications": ["<certification names>"],
  "job_titles": ["<job titles held, most recent first>"],
  "experience_level": "<one of: entry | mid | senior | lead>",
  "years_experience": <estimated total years, float or integer>
}}

Rules:
- Preserve factual content from the resume — do not invent employers, dates, or skills.
- experience and education should be ordered most recent first.
- If a section is missing, use an empty string, empty list, or null as appropriate.
- bullets should capture the key points under each role, not the entire raw paragraph."""
