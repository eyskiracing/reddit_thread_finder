"""Conservative query expansion for Reddit search."""

from __future__ import annotations

import re
from typing import List

from .constants import MAX_QUERY_VARIANTS, STOPWORDS
from .text_utils import clean_text


def extract_keywords(topic: str, max_keywords: int = 8) -> List[str]:
    """
    Extract simple lexical keywords from the natural-language pain point.

    This is intentionally basic and deterministic. Query expansion is meant only
    to create a candidate pool; semantic ranking does the final matching.
    """
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_\-]+", topic.lower())
    keywords = []
    seen = set()

    for word in words:
        if word in STOPWORDS:
            continue
        if len(word) <= 2:
            continue
        if word in seen:
            continue

        seen.add(word)
        keywords.append(word)

    return keywords[:max_keywords]


def generate_search_queries(topic: str, seed_queries: List[str] | None = None) -> List[str]:
    """
    Generate a small set of Reddit search query variants.

    The goal is to retrieve a reasonable candidate pool, not exhaustively mine
    Reddit. Query variants are capped by MAX_QUERY_VARIANTS. Focus-builder
    alternative queries can be passed as seed_queries.
    """
    topic_clean = clean_text(topic)
    keywords = extract_keywords(topic_clean)

    queries = [topic_clean]
    if seed_queries:
        queries.extend(seed_queries)

    if keywords:
        base = " ".join(keywords[:6])
        queries.append(base)

    if len(keywords) >= 3:
        queries.append(" ".join(keywords[:3]))

    if keywords:
        base = " ".join(keywords[:5])
        queries.extend(
            [
                f"{base} problem",
                f"{base} help",
                f"{base} tool",
                f"{base} recommendation",
                f"{base} alternative",
            ]
        )

    unique = []
    seen = set()

    for query in queries:
        q = clean_text(query)
        key = q.lower()

        if q and key not in seen:
            seen.add(key)
            unique.append(q)

    return unique[:MAX_QUERY_VARIANTS]
