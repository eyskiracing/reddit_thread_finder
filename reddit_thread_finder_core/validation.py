"""Input parsing and configuration limit enforcement."""

from __future__ import annotations

from datetime import datetime, timezone

from .constants import (
    DEFAULT_DELAY_SECONDS,
    MAX_CANDIDATE_LIMIT_PER_SEARCH,
    MAX_SEARCH_OPERATIONS,
    MAX_SUBREDDITS,
    MAX_TOP_K,
)
from .models import SearchConfig


def parse_yyyy_mm_dd(value: str) -> datetime:
    """
    Parse a YYYY-MM-DD date into a UTC datetime.

    The date is treated as midnight UTC for consistent comparison against
    Reddit's created_utc timestamps. Future dates are rejected because the
    search window is always from the requested date to the current time.
    """
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Date must be in YYYY-MM-DD format (e.g. 2025-01-15), got: {value!r}"
        )

    parsed = parsed.replace(tzinfo=timezone.utc)

    if parsed > datetime.now(timezone.utc):
        raise ValueError("from_date cannot be in the future.")

    return parsed


def parse_score(value: str) -> float:
    """Parse and validate a user-provided semantic threshold from 0.0 to 1.0."""
    try:
        score = float(value)
    except ValueError:
        raise ValueError(
            f"Score must be a number between 0.0 and 1.0, got: {value!r}"
        )
    if not 0.0 <= score <= 1.0:
        raise ValueError(
            f"Score must be between 0.0 and 1.0, got: {score}"
        )
    return score


def parse_positive_int(value: str, field_name: str) -> int:
    """Parse and validate positive integer CLI/input values."""
    try:
        parsed = int(value)
    except ValueError:
        raise ValueError(
            f"{field_name} must be a whole number greater than 0, got: {value!r}"
        )
    if parsed <= 0:
        raise ValueError(f"{field_name} must be greater than 0, got: {parsed}")
    return parsed


def enforce_limits(config: SearchConfig) -> SearchConfig:
    """
    Apply hard abuse-prevention caps to user-supplied configuration.

    Rather than failing when a user asks for too much, the function caps values
    and prints what changed. This keeps the tool usable while preserving the
    purpose limitation: find a small number of links for human review.
    """
    if config.top_k > MAX_TOP_K:
        print(f"Requested top_k={config.top_k}; capped to {MAX_TOP_K}.")
        config.top_k = MAX_TOP_K

    if len(config.subreddits) > MAX_SUBREDDITS:
        print(
            f"Requested {len(config.subreddits)} subreddits; "
            f"using first {MAX_SUBREDDITS}."
        )
        config.subreddits = config.subreddits[:MAX_SUBREDDITS]

    if config.candidate_limit > MAX_CANDIDATE_LIMIT_PER_SEARCH:
        print(
            f"Requested candidate_limit={config.candidate_limit}; "
            f"capped to {MAX_CANDIDATE_LIMIT_PER_SEARCH} per search operation."
        )
        config.candidate_limit = MAX_CANDIDATE_LIMIT_PER_SEARCH

    if config.max_search_operations > MAX_SEARCH_OPERATIONS:
        print(
            f"Requested max_search_operations={config.max_search_operations}; "
            f"capped to {MAX_SEARCH_OPERATIONS}."
        )
        config.max_search_operations = MAX_SEARCH_OPERATIONS

    if config.delay_seconds < 0:
        config.delay_seconds = DEFAULT_DELAY_SECONDS

    return config
