SYSTEM_PROMPT = """You are a job search query builder and candidate-profile writer. Return ONLY valid JSON, no explanation."""

# search_queries are consumed as: the single best query for quota-limited sources
# (Adzuna/Jooble/Remotive get exactly one API call each, using search_queries[0]) and
# as extra fuzzy-match terms + semantic/BM25 corpus text for ATS sources and local
# scoring (Greenhouse/Lever/Ashby, scoring_service.py) — never fanned out into
# multiple API calls per source.
USER_TEMPLATE = """Given this job search:
- Job Title: {job_title}
- Field/Domain: {field_domain}

Return a JSON object with exactly these keys:
{{
  "search_queries": ["3-5 full search-query phrases a recruiter or job board would use to find this exact role — natural phrases, not single words"],
  "primary_keywords": ["list of 5-8 individual search terms that would appear in relevant job titles or descriptions"],
  "negative_keywords": ["list of 4-6 terms that signal an IRRELEVANT job despite a similar title"],
  "related_titles": ["list of 2-4 alternate job titles that mean the same role in this field"],
  "ideal_profile": "1-2 plain-English sentences describing the ideal candidate for this role — what they do day to day, what domain/tools/systems they work with"
}}

Example for job_title="Analyst", field_domain="Healthcare":
{{
  "search_queries": ["healthcare data analyst", "clinical informatics analyst", "EHR analyst remote", "claims data analyst healthcare"],
  "primary_keywords": ["healthcare analyst", "clinical data", "EHR", "HEDIS", "claims analyst", "health informatics", "medical records"],
  "negative_keywords": ["game", "retail", "fashion", "real estate", "marketing analyst"],
  "related_titles": ["Clinical Analyst", "Health Data Specialist", "Medical Data Analyst"],
  "ideal_profile": "Someone who analyzes clinical, claims, or EHR data inside hospitals, health systems, or payers, turning patient or operational data into reporting and insight."
}}"""
