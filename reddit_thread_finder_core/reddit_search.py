"""Bounded Reddit candidate retrieval."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import praw

from .constants import ALLOWED_SORTS, MAX_UNIQUE_CANDIDATES
from .models import SearchConfig
from .query import generate_search_queries
from .security import run_with_rate_limit_backoff
from .text_utils import clean_text


def choose_reddit_time_filter(from_date: datetime, now: Optional[datetime] = None) -> str:
    """
    Choose the smallest Reddit search time_filter that contains from_date -> now.

    Reddit's native time filters are coarse. The script intentionally over-fetches
    within Reddit's available window, then applies the exact from_date filter
    locally using created_utc.
    """
    now = now or datetime.now(timezone.utc)
    delta_days = max(0, (now - from_date).days)

    if delta_days <= 1:
        return "day"
    if delta_days <= 7:
        return "week"
    if delta_days <= 31:
        return "month"
    if delta_days <= 365:
        return "year"
    return "all"


def build_semantic_text_from_metadata_only(submission) -> str:
    """
    Build candidate text without using submission.selftext or comments.

    This keeps the tool focused on finding links for human review, not collecting
    or processing Reddit thread content.
    """
    parts = [
        f"Title: {getattr(submission, 'title', '') or ''}",
        f"Subreddit: {getattr(submission, 'subreddit', '') or ''}",
    ]

    link_flair = getattr(submission, "link_flair_text", None)
    if link_flair:
        parts.append(f"Flair: {link_flair}")

    return clean_text(" ".join(parts))


def _execute_search(subreddit, query: str, sort: str, time_filter: str, limit: int) -> list:
    """
    Execute a single Reddit search with explicit parameter binding.

    This helper exists to avoid Python's closure-by-reference behaviour.
    When run_with_rate_limit_backoff retries a lambda, the lambda re-reads
    the loop variables at retry time, not at the time the lambda was created.
    Passing all arguments explicitly here guarantees the retry searches for
    the same query/sort combination that originally triggered the rate limit.
    """
    return list(
        subreddit.search(
            query,
            sort=sort,
            time_filter=time_filter,
            limit=limit,
            # Plain syntax is intentionally locked. Lucene syntax supports
            # field-specific queries (e.g. author:, flair:) that could be
            # used to target user data. Plain keeps searches to keyword
            # matching and is consistent with Reddit's own search UI.
            syntax="plain",
        )
    )


def fetch_candidates(
    reddit: praw.Reddit,
    config: SearchConfig,
) -> Dict[str, Tuple[object, str, List[str]]]:
    """
    Retrieve bounded Reddit candidates keyed by Reddit submission ID.

    Returns:
        submission_id -> (submission, semantic_text, matched_queries)

    This function intentionally does not retrieve thread bodies or comments.
    """
    now = datetime.now(timezone.utc)
    from_timestamp = config.from_date.timestamp()
    time_filter = choose_reddit_time_filter(config.from_date, now=now)
    queries = generate_search_queries(config.topic, seed_queries=config.additional_queries)

    if "all" in config.subreddits:
        print("Note: searching r/all — results will span all public subreddits.")

    candidates: Dict[str, Tuple[object, str, List[str]]] = {}
    operations = 0

    for subreddit_name in config.subreddits:
        subreddit = reddit.subreddit(subreddit_name)

        for query in queries:
            for sort in ALLOWED_SORTS:
                # Stop before the search pattern can drift into high-volume monitoring.
                if operations >= config.max_search_operations:
                    print(
                        f"Reached search operation cap "
                        f"({config.max_search_operations}). Stopping retrieval."
                    )
                    return candidates

                # Candidate cap limits local processing and JSON export blast radius.
                if len(candidates) >= MAX_UNIQUE_CANDIDATES:
                    print(
                        f"Reached unique candidate cap "
                        f"({MAX_UNIQUE_CANDIDATES}). Stopping retrieval."
                    )
                    return candidates

                operations += 1

                try:
                    # Bind loop variables explicitly via _execute_search to prevent
                    # the closure-by-reference bug: on retry, a bare lambda would
                    # re-read `query` and `sort` from the enclosing scope, which
                    # may have advanced to the next iteration.
                    submissions = run_with_rate_limit_backoff(
                        lambda q=query, s=sort, tf=time_filter, lim=config.candidate_limit: (
                            _execute_search(subreddit, q, s, tf, lim)
                        ),
                        description=(
                            f"r/{subreddit_name} search query={query!r} "
                            f"sort={sort!r}"
                        ),
                    )

                    for submission in submissions:
                        created_utc = getattr(submission, "created_utc", 0)
                        if created_utc < from_timestamp:
                            continue

                        if getattr(submission, "stickied", False):
                            continue

                        # Important: this intentionally avoids submission.selftext
                        # and comments. The goal is to find links, not ingest content.
                        text = build_semantic_text_from_metadata_only(submission)

                        if not text:
                            continue

                        # Avoid terms are user-supplied noise filters. They are applied
                        # only to lightweight metadata, never to body/comment content.
                        if config.avoid_terms:
                            lower_text = text.lower()
                            if any(term.lower() in lower_text for term in config.avoid_terms):
                                continue

                        if submission.id not in candidates:
                            candidates[submission.id] = (submission, text, [query])
                        else:
                            existing_submission, existing_text, matched_queries = candidates[
                                submission.id
                            ]
                            if query not in matched_queries:
                                matched_queries.append(query)
                            candidates[submission.id] = (
                                existing_submission,
                                existing_text,
                                matched_queries,
                            )

                except Exception as exc:
                    print(
                        f"Warning: search failed for r/{subreddit_name}, "
                        f"query={query!r}, sort={sort!r}: {exc}"
                    )

                if config.delay_seconds:
                    time.sleep(config.delay_seconds)

    return candidates
