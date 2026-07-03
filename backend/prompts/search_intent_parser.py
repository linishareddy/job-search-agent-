SYSTEM_PROMPT = """You are a job search intent parser. Return ONLY valid JSON, no explanation."""

USER_TEMPLATE = """A user submitted the following text to create a job search alert:

\"\"\"{text}\"\"\"

Your task: extract a JSON object describing the job they are looking for.

--- CRITICAL RULES ---
1. NEVER copy raw text from the input into any output field.
2. ALL fields must be SHORT and clean:
   - job_title: max 5 words (e.g. "AI Engineer", "Senior Python Developer")
   - field_domain: max 8 words describing the industry/tech area (e.g. "AI, LLMs, NLP, Machine Learning")
   - name: max 8 words, a human-readable label for this saved search
3. If the input is a RESUME or CV (contains sections like "Experience", "Education", "Skills", or lists of past jobs):
   - DO NOT use resume content as the job title or domain.
   - Instead, INFER the target job role from the person's most recent experience and skills.
   - Set confidence to 0.75 and add "Resume provided — inferred target role from experience" to ambiguities.
4. If the input is a SHORT QUERY (one or two sentences describing a desired job), extract directly.

--- OUTPUT FORMAT ---
{{
  "job_title": "<concise target job title, max 5 words>",
  "field_domain": "<industry/tech domain, max 8 words>",
  "name": "<short human-readable search label, max 8 words>",
  "location": "<city/region/country if mentioned, else null>",
  "work_mode": "<one of: remote | hybrid | onsite | any>",
  "experience_level": "<one of: entry | mid | senior | lead | any>",
  "employment_type": "<one of: full_time | part_time | contract | any>",
  "salary_min": <integer annual USD or null>,
  "salary_max": <integer annual USD or null>,
  "company_slugs": [{{"name": "<company name>", "slug": "<lowercase-hyphenated>", "source": "<greenhouse|lever|ashby>"}}],
  "confidence": <float 0-1>,
  "ambiguities": ["<note about anything guessed or inferred>"]
}}

--- EXAMPLES ---

Example 1 — Short query:
Input: "Remote senior Python backend engineer, full time, 150k+"
Output:
{{
  "job_title": "Senior Python Backend Engineer",
  "field_domain": "Software Engineering, Backend, Python",
  "name": "Senior Python Backend - Remote",
  "location": null,
  "work_mode": "remote",
  "experience_level": "senior",
  "employment_type": "full_time",
  "salary_min": 150000,
  "salary_max": null,
  "company_slugs": [],
  "confidence": 0.95,
  "ambiguities": []
}}

Example 2 — Resume paste (DO NOT copy resume text into fields):
Input: "Jane Doe | AI Engineer | jane@email.com\nExperience:\nAI Intern at XYZ - built RAG pipelines, LangChain agents, FastAPI backends...\nSkills: Python, LangChain, LLMs, FastAPI, PostgreSQL"
Output:
{{
  "job_title": "AI Engineer",
  "field_domain": "AI, LLMs, RAG, NLP, Backend",
  "name": "AI Engineer - LLMs & RAG",
  "location": null,
  "work_mode": "any",
  "experience_level": "entry",
  "employment_type": "any",
  "salary_min": null,
  "salary_max": null,
  "company_slugs": [],
  "confidence": 0.75,
  "ambiguities": ["Resume provided — inferred target role from experience"]
}}"""
