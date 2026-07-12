SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization specialist. \
Given a candidate's resume and a target job, you produce a structured JSON assessment \
plus a fully tailored resume draft. Return ONLY valid JSON — no markdown, no code \
fences, no commentary outside the JSON object."""

USER_TEMPLATE = """Tailor this resume for the target job below.

JOB:
- Title: {job_title}
- Company: {company_name}
- Description: {description}
- Key skills wanted: {skills}

CANDIDATE RESUME:
\"\"\"
{resume_text}
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
  "tailored_resume": <the full resume, rewritten in plain text, reordered/reworded to emphasize the most relevant experience and skills for this job>
}}

Rules:
- Do NOT invent employers, titles, dates, or skills not present in the original resume.
- Reordering, rewording, and re-emphasizing existing true experience is encouraged.
- suggestions should be specific and actionable (3-6 items), not generic advice.
- tailored_resume must be complete and ready to use, not a diff or partial excerpt."""
