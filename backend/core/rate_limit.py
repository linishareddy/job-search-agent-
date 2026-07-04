"""Rate limiting for the Groq-backed endpoints — a double-click or an accidental
repeat request on /parse-text, /run, /from-text, or /cover-letter currently has no
guardrail and can burn paid Groq quota. Deliberately scoped to just those routes,
not applied globally — the rest of the API doesn't touch a paid, rate-limited
external service."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Generous enough not to interfere with a legitimate retry, tight enough to catch
# an accidental double-click or a runaway client loop.
GROQ_ENDPOINT_LIMIT = "20/minute"
