"""Thin wrapper around the Resend HTTP API (https://resend.com) — reuses the
project's existing httpx client rather than pulling in Resend's own SDK.

Delivery is best-effort: a failed or disabled send returns False and logs, but
never raises, so a flaky provider or missing API key can't take down a pipeline
run or the auto-apply scheduler tick that triggered it.
"""
import logging

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

_RESEND_URL = "https://api.resend.com/emails"


async def send_email(to: str, subject: str, html: str) -> bool:
    if not settings.email_enabled:
        logger.debug(f"Email disabled — skipping send to {to}: {subject}")
        return False
    if not settings.resend_api_key:
        logger.warning("EMAIL_ENABLED is true but RESEND_API_KEY is unset — skipping send")
        return False

    payload = {
        "from": settings.email_from,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                _RESEND_URL,
                json=payload,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            )
            response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False
