"""Thin client for Dice's official MCP job search API (https://mcp.dice.com/mcp)."""
import json
import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

logger = logging.getLogger(__name__)

_MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "User-Agent": "JobRadar/1.0 (job aggregator; dice.com MCP)",
}


def _parse_sse_payload(raw: str) -> dict[str, Any]:
    for line in raw.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise ValueError("MCP response missing SSE data payload")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def search_jobs(**arguments: Any) -> dict[str, Any]:
    """Call Dice MCP search_jobs and return the parsed result object."""
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "search_jobs", "arguments": arguments},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(settings.dice_mcp_url, json=body, headers=_MCP_HEADERS)
        response.raise_for_status()

    payload = _parse_sse_payload(response.text)
    if payload.get("error"):
        raise RuntimeError(payload["error"])

    result = payload.get("result") or {}
    if result.get("isError"):
        message = result.get("content", [{}])[0].get("text", "Dice MCP search failed")
        raise RuntimeError(message)

    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured

    for block in result.get("content") or []:
        if block.get("type") == "text" and block.get("text"):
            return json.loads(block["text"])

    return {"data": [], "meta": {}}
