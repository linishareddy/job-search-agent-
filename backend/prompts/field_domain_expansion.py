SYSTEM_PROMPT = """You are a job search query builder. Return ONLY valid JSON, no explanation."""

USER_TEMPLATE = """Given this job search:
- Job Title: {job_title}
- Field/Domain: {field_domain}

Return a JSON object with exactly these keys:
{{
  "primary_keywords": ["list of 5-8 search terms that would appear in relevant job titles or descriptions"],
  "negative_keywords": ["list of 4-6 terms that signal an IRRELEVANT job despite a similar title"],
  "related_titles": ["list of 2-4 alternate job titles that mean the same role in this field"]
}}

Example for job_title="Analyst", field_domain="Healthcare":
{{
  "primary_keywords": ["healthcare analyst", "clinical data", "EHR", "HEDIS", "claims analyst", "health informatics", "medical records"],
  "negative_keywords": ["game", "retail", "fashion", "real estate", "marketing analyst"],
  "related_titles": ["Clinical Analyst", "Health Data Specialist", "Medical Data Analyst"]
}}"""
