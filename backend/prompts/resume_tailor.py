SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization specialist. \
Given a candidate's resume and a target job, you produce a structured JSON assessment \
plus tailored resume sections. Return ONLY valid JSON — no markdown, no code \
fences, no commentary outside the JSON object."""

USER_TEMPLATE = """Tailor this resume for the target job below.

JOB:
- Title: {job_title}
- Company: {company_name}
- Description: {description}
- Key skills wanted: {skills}

CANDIDATE RESUME (structured sections):
\"\"\"
{resume_sections}
\"\"\"

Return a JSON object with exactly these fields:
{{
  "match_score": <integer 0-100, how well the resume currently fits this job>,
  "matched_keywords": [<skills/keywords from the job already present in the resume>],
  "missing_keywords": [<important skills/keywords from the job absent from the resume>],
  "suggestions": [
    {{"section": <resume section name>, "current": <short quote or paraphrase of what's there now, or "" if the section is missing>, "suggested": <concrete rewritten text>, "reason": <why this change helps for this specific job>}}
  ],
  "summary_rewrite": <a 2-3 sentence professional summary tailored to this job>,
  "gaps": [<genuine gaps between the candidate's background and the job's requirements>],
  "tailored_sections": {{
    "contact": {{
      "name": "<same as original unless a minor formatting fix is needed>",
      "email": "<same as original>",
      "phone": "<same as original>",
      "location": "<same as original>",
      "linkedin": "<same as original>",
      "github": "<same as original>",
      "website": "<same as original>"
    }},
    "summary": "<tailored professional summary for this job>",
    "skills": ["<reordered/reworded skills emphasizing job relevance>"],
    "experience": [
      {{
        "title": "<same title as original>",
        "company": "<same company as original>",
        "location": "<same as original>",
        "start_date": "<same as original>",
        "end_date": "<same as original>",
        "bullets": ["<rewritten bullets emphasizing relevance to this job>"]
      }}
    ],
    "education": [
      {{
        "degree": "<same as original>",
        "institution": "<same as original>",
        "location": "<same as original>",
        "graduation_date": "<same as original>",
        "details": ["<same or lightly reworded details>"]
      }}
    ],
    "certifications": ["<same certifications as original>"],
    "job_titles": ["<same titles as original>"],
    "experience_level": "<same as original>",
    "years_experience": <same as original>
  }}
}}

Rules:
- Do NOT invent employers, titles, dates, or skills not present in the original resume.
- Reordering, rewording, and re-emphasizing existing true experience is encouraged.
- tailored_sections must keep the same roles/education entries as the original — only rewrite content.
- suggestions should be specific and actionable (3-6 items), not generic advice.
- summary_rewrite should match the tailored_sections.summary content."""
