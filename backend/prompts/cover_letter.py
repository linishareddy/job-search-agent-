SYSTEM_PROMPT = """You are an expert career writer. You write concise, specific, professional cover letters. Return ONLY the cover letter text — no preamble, no markdown, no explanation."""

USER_TEMPLATE = """Write a tailored cover letter for this candidate applying to this job.

JOB:
- Title: {job_title}
- Company: {company_name}
- Summary: {description_summary}
- Key skills wanted: {skills}

CANDIDATE RESUME:
\"\"\"
{resume_text}
\"\"\"

Requirements:
- 3-4 short paragraphs, under 300 words.
- Open with genuine interest in the specific role/company.
- Highlight the candidate's most relevant experience and skills that overlap with what the job wants — cite concrete details from the resume.
- Professional but warm tone. No clichés like "I am writing to apply".
- Do NOT invent facts not supported by the resume.
- End with a brief call to action. Sign off as the candidate (use their name from the resume if present, otherwise omit the signature line)."""
