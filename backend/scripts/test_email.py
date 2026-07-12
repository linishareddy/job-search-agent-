#!/usr/bin/env python3
"""Send a test email via Resend to verify RESEND_API_KEY and EMAIL_ENABLED."""
import asyncio
import sys

from services.email_service import send_email


async def main() -> None:
    to = sys.argv[1] if len(sys.argv) > 1 else "devadiyek@gmail.com"
    ok = await send_email(
        to=to,
        subject="Job Agent — email test",
        html=(
            "<div style='font-family:sans-serif;max-width:600px'>"
            "<h2>Email is working</h2>"
            "<p>Your Job Agent app can now send:</p>"
            "<ul>"
            "<li><strong>New job digests</strong> — when a search finds high-relevance matches</li>"
            "<li><strong>Auto-apply summaries</strong> — when tailored resumes are ready in Tracker</li>"
            "</ul>"
            "<p>Enable &quot;Email me updates&quot; on the Auto-apply page to receive them.</p>"
            "</div>"
        ),
    )
    if ok:
        print(f"Sent test email to {to}")
    else:
        print("Send failed — check RESEND_API_KEY, EMAIL_ENABLED=true, and backend logs")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
