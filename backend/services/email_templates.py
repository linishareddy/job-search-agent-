"""Inline-styled HTML email bodies. Email clients strip <style> blocks and
external stylesheets, so every rule here is inlined on the element itself."""

from config.settings import settings

_WRAPPER_OPEN = (
    '<div style="font-family:-apple-system,Helvetica,Arial,sans-serif;max-width:600px;'
    'margin:0 auto;color:#1a1a1a;">'
)
_WRAPPER_CLOSE = "</div>"

_ROW_STYLE = "border-bottom:1px solid #e5e5e5;padding:12px 0;"
_TITLE_STYLE = "font-size:15px;font-weight:600;margin:0 0 4px 0;"
_META_STYLE = "font-size:13px;color:#666;margin:0 0 6px 0;"
_LINK_STYLE = "font-size:13px;color:#2563eb;text-decoration:none;"
_BTN_STYLE = (
    "display:inline-block;margin-top:16px;padding:10px 18px;background:#2563eb;"
    "color:#ffffff;text-decoration:none;border-radius:6px;font-size:14px;font-weight:600;"
)
_FOOTER_STYLE = "font-size:12px;color:#999;margin-top:24px;"


def _dashboard_link(path: str, label: str) -> str:
    url = f"{settings.frontend_url.rstrip('/')}{path}"
    return f'<a href="{url}" style="{_BTN_STYLE}">{label}</a>'


def new_jobs_digest(search_name: str, jobs: list[dict]) -> str:
    """jobs: [{title, company_name, location, apply_url, relevance_score}]"""
    rows = "".join(
        f'<div style="{_ROW_STYLE}">'
        f'<p style="{_TITLE_STYLE}">{j["title"]} — {j["company_name"]}</p>'
        f'<p style="{_META_STYLE}">{j.get("location") or "Location not specified"}'
        f' · Relevance {round((j.get("relevance_score") or 0) * 10, 1)}/10</p>'
        f'<a href="{j["apply_url"]}" style="{_LINK_STYLE}">View job →</a>'
        f"</div>"
        for j in jobs
    )
    return (
        f"{_WRAPPER_OPEN}"
        f'<h2 style="font-size:18px;">New matches for "{search_name}"</h2>'
        f'<p style="{_META_STYLE}">{len(jobs)} high-relevance job(s) from your latest search run.</p>'
        f"{rows}"
        f"{_dashboard_link('/dashboard/searches', 'Open dashboard')}"
        f'<p style="{_FOOTER_STYLE}">Turn off email updates in Auto-apply settings.</p>'
        f"{_WRAPPER_CLOSE}"
    )


def auto_apply_summary(applications: list[dict]) -> str:
    """applications: [{title, company_name, apply_url, match_score}]"""
    rows = "".join(
        f'<div style="{_ROW_STYLE}">'
        f'<p style="{_TITLE_STYLE}">{a["title"]} — {a["company_name"]}</p>'
        f'<p style="{_META_STYLE}">Match score {round((a.get("match_score") or 0) * 100)}%'
        f" · Tailored resume &amp; cover letter saved in your Tracker</p>"
        f'<a href="{a["apply_url"]}" style="{_LINK_STYLE}">Open job posting →</a>'
        f"</div>"
        for a in applications
    )
    return (
        f"{_WRAPPER_OPEN}"
        f'<h2 style="font-size:18px;">{len(applications)} job(s) ready to apply</h2>'
        f'<p style="{_META_STYLE}">'
        f"We prepared a tailored resume and cover letter for each match. "
        f"Review them in your Tracker, then submit on the employer site when ready."
        f"</p>"
        f"{rows}"
        f"{_dashboard_link('/dashboard/tracker', 'Open Tracker')}"
        f'<p style="{_FOOTER_STYLE}">Turn off email updates in Auto-apply settings.</p>'
        f"{_WRAPPER_CLOSE}"
    )
