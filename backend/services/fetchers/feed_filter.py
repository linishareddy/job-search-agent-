"""Shared keyword matching for API-based job boards that return full feeds."""
from services.fetchers.base_fetcher import build_search_queries


def search_query_list(search, expansion: dict) -> list[str]:
    return build_search_queries(search, expansion)


def query_tokens(queries: list[str]) -> list[str]:
    tokens: set[str] = set()
    for q in queries:
        q = q.lower().strip()
        if q:
            tokens.add(q)
            for word in q.split():
                if len(word) >= 3:
                    tokens.add(word)
    return list(tokens)


def matches_keywords(haystack: str, queries: list[str]) -> bool:
    if not queries:
        return True
    haystack = haystack.lower()
    return any(t in haystack for t in query_tokens(queries))
