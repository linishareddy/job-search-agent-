SYSTEM_PROMPT = """You are a job search intent parser. Return ONLY valid JSON, no explanation."""

USER_TEMPLATE = """A user typed this free-text description of the job they want:

"{text}"

Extract a JSON object with exactly these keys:
{{
  "job_title": "<the core job title, e.g. 'Healthcare Analyst'>",
  "field_domain": "<the field/domain/industry context, described in a few words, e.g. 'Healthcare, EHR, claims analysis'>",
  "name": "<a short human-readable label for this saved search, e.g. 'Healthcare Analyst - Remote US'>",
  "location": "<city/state/country if mentioned, else 'United States'>",
  "work_mode": "<one of: remote | hybrid | onsite | any>",
  "experience_level": "<one of: entry | mid | senior | lead | any>",
  "employment_type": "<one of: full_time | part_time | contract | any>",
  "salary_min": <integer annual USD or null>,
  "salary_max": <integer annual USD or null>,
  "company_slugs": [{{"name": "<company name>", "slug": "<lowercase-hyphenated>", "source": "<greenhouse|lever|ashby, best guess>"}}],
  "confidence": <float 0-1, how confident you are in this extraction>,
  "ambiguities": ["<short note about anything you had to guess or infer>"]
}}

Rules:
- "company_slugs" should only be non-empty if the user explicitly named a specific company they want jobs from.
- If a field isn't mentioned in the text, use null (or "any" for enums, per the allowed values above) rather than guessing wildly.
- Salary written like "100k+" means salary_min=100000, salary_max=null.
- Always include at least "job_title" and "field_domain" — infer field_domain from context if not explicit.

Example for text="Remote senior healthcare analyst in the US, full time, 90k-130k, focusing on EHR and claims data":
{{
  "job_title": "Healthcare Analyst",
  "field_domain": "Healthcare - EHR, claims data analysis",
  "name": "Healthcare Analyst - Remote US",
  "location": "United States",
  "work_mode": "remote",
  "experience_level": "senior",
  "employment_type": "full_time",
  "salary_min": 90000,
  "salary_max": 130000,
  "company_slugs": [],
  "confidence": 0.92,
  "ambiguities": []
}}"""
