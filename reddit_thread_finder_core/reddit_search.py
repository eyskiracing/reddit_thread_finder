"""Bounded Reddit candidate retrieval via Arctic Shift API.

This module replaces the PRAW-based Reddit API client from the main branch.
It uses direct HTTP requests to the Arctic Shift public API.

No credentials are required. Arctic Shift is a free public API with no
authentication. All requests are read-only GET requests.

Security notes:
  - All query strings and subreddit names are passed as structured URL
    parameters, not concatenated into URLs, preventing injection
  - All responses are validated via security.validate_arctic_shift_response
    and security.validate_post_fields before use
  - Thread body (selftext) and comments are intentionally not requested
    or used anywhere in this module
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests

from .constants import (
    ARCTIC_SHIFT_BASE_URL,
    ARCTIC_SHIFT_DATA_LAG_DAYS,
    ARCTIC_SHIFT_TIMEOUT_SECONDS,
    ARCTIC_SHIFT_USER_AGENT,
    DEFAULT_DELAY_SECONDS,
    MAX_SEARCH_OPERATIONS,
    MAX_UNIQUE_CANDIDATES,
)
from .models import SearchConfig
from .query import generate_search_queries
from .security import (
    check_rate_limit_header,
    run_with_rate_limit_backoff,
    validate_arctic_shift_response,
    validate_post_fields,
)
from .text_utils import clean_text


def _make_session() -> requests.Session:
    """Create a requests session with the standard headers for Arctic Shift."""
    session = requests.Session()
    session.headers.update({"User-Agent": ARCTIC_SHIFT_USER_AGENT})
    return session


def warn_if_from_date_is_recent(from_date: datetime) -> None:
    """
    Warn the user when from_date is within the Arctic Shift data lag window.

    Arctic Shift data may be 2–4 weeks behind real-time. If the user's
    from_date is very recent, they may get fewer results than expected.
    """
    now = datetime.now(timezone.utc)
    age_days = (now - from_date).days

    if age_days <= ARCTIC_SHIFT_DATA_LAG_DAYS:
        print(
            f"\nNote: Arctic Shift data may be up to {ARCTIC_SHIFT_DATA_LAG_DAYS} days "
            f"behind real-time. Your from_date is {age_days} days ago, so results "
            "may be incomplete for very recent posts."
        )


def build_semantic_text_from_metadata_only(post: dict) -> str:
    """
    Build candidate text from post metadata only — never from body or comments.

    This keeps the tool focused on link discovery and prevents processing of
    Reddit thread content beyond titles and lightweight metadata.
    """
    parts = [
        f"Title: {post.get('title', '') or ''}",
        f"Subreddit: {post.get('subreddit', '') or ''}",
    ]

    flair = post.get("link_flair_text") or post.get("flair")
    if flair:
        parts.append(f"Flair: {flair}")

    return clean_text(" ".join(parts))


def _fetch_posts_from_arctic_shift(
    session: requests.Session,
    subreddit: str,
    query: str,
    from_timestamp: float,
    limit: int,
) -> List[dict]:
    """
    Fetch posts from Arctic Shift for a single subreddit and query.

    Parameters are passed as structured URL params, never concatenated.
    The response is validated before being returned.
    """
    endpoint = f"{ARCTIC_SHIFT_BASE_URL}/posts/search"

    # Convert from_timestamp to an ISO date string for Arctic Shift's after parameter
    from_date_str = datetime.fromtimestamp(from_timestamp, tz=timezone.utc).strftime("%Y-%m-%d")

    def _do_request():
        response = session.get(
            endpoint,
            params={
                "q": query,
                "subreddit": subreddit,
                "after": from_date_str,
                "limit": limit,
                "sort": "relevance",
            },
            timeout=ARCTIC_SHIFT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        check_rate_limit_header(dict(response.headers))
        return response.json()

    raw = run_with_rate_limit_backoff(
        _do_request,
        description=f"r/{subreddit} search query={query!r}",
    )

    validated = validate_arctic_shift_response(raw, endpoint)
    return validated.get("data", [])


def fetch_candidates(
    config: SearchConfig,
) -> Dict[str, Tuple[dict, str, List[str]]]:
    """
    Retrieve bounded Reddit candidates from Arctic Shift keyed by post ID.

    Returns:
        post_id -> (post_dict, semantic_text, matched_queries)

    This function intentionally does not retrieve thread bodies or comments.
    It uses only title, subreddit, and flair for semantic matching.
    """
    session = _make_session()
    from_timestamp = config.from_date.timestamp()

    warn_if_from_date_is_recent(config.from_date)

    queries = generate_search_queries(config.topic, seed_queries=config.additional_queries)

    candidates: Dict[str, Tuple[dict, str, List[str]]] = {}
    operations = 0

    for subreddit_name in config.subreddits:
        for query in queries:
            if operations >= config.max_search_operations:
                print(
                    f"Reached search operation cap "
                    f"({config.max_search_operations}). Stopping retrieval."
                )
                return candidates

            if len(candidates) >= MAX_UNIQUE_CANDIDATES:
                print(
                    f"Reached unique candidate cap "
                    f"({MAX_UNIQUE_CANDIDATES}). Stopping retrieval."
                )
                return candidates

            operations += 1

            try:
                posts = _fetch_posts_from_arctic_shift(
                    session=session,
                    subreddit=subreddit_name,
                    query=query,
                    from_timestamp=from_timestamp,
                    limit=config.candidate_limit,
                )

                for raw_post in posts:
                    try:
                        post = validate_post_fields(raw_post, "posts/search")
                    except ValueError as exc:
                        print(f"Warning: skipping malformed post: {exc}")
                        continue

                    # created_utc may come back as int, float, or string
                    created_utc = float(post.get("created_utc") or 0)
                    if created_utc < from_timestamp:
                        continue

                    # Intentionally only uses title, subreddit, flair.
                    # Thread body and comments are never requested or used.
                    text = build_semantic_text_from_metadata_only(post)

                    if not text:
                        continue

                    if config.avoid_terms:
                        lower_text = text.lower()
                        if any(term.lower() in lower_text for term in config.avoid_terms):
                            continue

                    post_id = str(post["id"]).removeprefix("t3_")

                    if post_id not in candidates:
                        candidates[post_id] = (post, text, [query])
                    else:
                        existing_post, existing_text, matched_queries = candidates[post_id]
                        if query not in matched_queries:
                            matched_queries.append(query)
                        candidates[post_id] = (existing_post, existing_text, matched_queries)

            except Exception as exc:
                print(
                    f"Warning: search failed for r/{subreddit_name}, "
                    f"query={query!r}: {exc}"
                )

            if config.delay_seconds:
                time.sleep(config.delay_seconds)

    return candidates
