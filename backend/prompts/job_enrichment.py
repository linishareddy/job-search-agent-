SYSTEM_PROMPT = """You are a job posting data extractor. Return ONLY valid JSON array, no explanation or markdown."""

USER_TEMPLATE = """For each job below, extract structured data and score relevance for this search:
- Target Job Title: {job_title}
- Field/Domain: {field_domain}
- Experience Level: {experience_level}

Return a JSON array. Each element must have ALL these fields:
{{
  "idx": <integer index from input>,
  "summary": "<1-2 sentence plain English description of the role and key responsibilities>",
  "skills": ["up to 8 required skills explicitly mentioned"],
  "work_mode": "<one of: remote | hybrid | onsite | unknown>",
  "salary_min": <integer annual USD or null>,
  "salary_max": <integer annual USD or null>,
  "relevance_score": <integer 1-10, where 10 = perfect match for job title + field + level>
}}

Scoring guidance:
- 9-10: Title AND domain match perfectly
- 7-8: Title matches, domain is close or related
- 5-6: Title partially matches or domain partially relevant
- 3-4: Title or domain is a stretch
- 1-2: Clearly wrong field or seniority mismatch

JOBS:
{jobs_json}"""
