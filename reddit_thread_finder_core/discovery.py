"""Subreddit discovery and relevance validation using Arctic Shift.

Because Arctic Shift requires subreddit-scoped searches (it does not support
Reddit-wide full text search), this module discovers relevant subreddits
automatically before the main search begins.

The discovery process has two steps:
  1. Find candidate subreddits by keyword using Arctic Shift's subreddit search
  2. Validate each candidate by checking how many relevant posts it contains

This means users never need to know Reddit's community structure. The tool
finds the right communities for their topic automatically.

Security notes:
  - All subreddit names from discovery are validated before use in subsequent
    HTTP requests to prevent parameter injection
  - API responses are validated via security.validate_subreddit_fields before use
  - No user data is transmitted; only the search topic keyword is sent
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

import requests

from .constants import (
    ARCTIC_SHIFT_BASE_URL,
    ARCTIC_SHIFT_TIMEOUT_SECONDS,
    ARCTIC_SHIFT_USER_AGENT,
    DEFAULT_DELAY_SECONDS,
    MAX_DISCOVERY_CANDIDATES,
    MAX_DISCOVERY_VALIDATION_POSTS,
)
from .security import (
    check_rate_limit_header,
    run_with_rate_limit_backoff,
    validate_arctic_shift_response,
)
from .text_utils import clean_text

# Subreddit names on Reddit may only contain letters, numbers, and underscores.
# We validate discovered subreddit names against this pattern before using them
# in subsequent HTTP requests.
_SUBREDDIT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,50}$")

# Relevance tiers based on validation post count
_HIGH_THRESHOLD = 3
_MEDIUM_THRESHOLD = 1


@dataclass
class DiscoveredSubreddit:
    """A subreddit found and validated during discovery."""
    name: str
    description: str = ""
    subscriber_count: int = 0
    relevance_tier: str = "low"      # "high", "medium", or "low"
    validation_post_count: int = 0


def _is_valid_subreddit_name(name: str) -> bool:
    """
    Validate a subreddit name before using it in an HTTP request.

    Subreddit names on Reddit are alphanumeric + underscores, max 50 chars.
    Rejecting invalid names prevents parameter injection in subsequent
    Arctic Shift search calls.
    """
    return bool(_SUBREDDIT_NAME_PATTERN.match(name))


def _make_session() -> requests.Session:
    """Create a requests session with the standard User-Agent header."""
    session = requests.Session()
    session.headers.update({"User-Agent": ARCTIC_SHIFT_USER_AGENT})
    return session


def _search_subreddits_by_keyword(
    keyword: str,
    session: requests.Session,
    limit: int = MAX_DISCOVERY_CANDIDATES,
) -> List[dict]:
    """
    Search Arctic Shift for subreddits matching a keyword.

    Returns a list of raw subreddit dicts from the API. Each dict is validated
    for expected fields before being returned.
    """
    endpoint = f"{ARCTIC_SHIFT_BASE_URL}/subreddits/search"

    def _do_request():
        response = session.get(
            endpoint,
            params={"q": keyword, "limit": limit},
            timeout=ARCTIC_SHIFT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        check_rate_limit_header(dict(response.headers))
        return response.json()

    try:
        raw = run_with_rate_limit_backoff(
            _do_request,
            description=f"subreddit search for {keyword!r}",
        )
        validated = validate_arctic_shift_response(raw, endpoint)
        return validated.get("data", [])
    except Exception as exc:
        print(f"Warning: subreddit discovery search failed: {exc}")
        return []


def _validate_subreddit_relevance(
    subreddit_name: str,
    query: str,
    session: requests.Session,
) -> int:
    """
    Check how many posts relevant to the query exist in this subreddit.

    We fetch a small number of posts (MAX_DISCOVERY_VALIDATION_POSTS) and
    return the count. This is used to tier subreddits as high/medium/low
    relevance.

    A subreddit with zero matching posts is dropped from the results.
    """
    endpoint = f"{ARCTIC_SHIFT_BASE_URL}/posts/search"

    def _do_request():
        response = session.get(
            endpoint,
            params={
                "q": query,
                "subreddit": subreddit_name,
                "limit": MAX_DISCOVERY_VALIDATION_POSTS,
                "sort": "relevance",
            },
            timeout=ARCTIC_SHIFT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        check_rate_limit_header(dict(response.headers))
        return response.json()

    try:
        raw = run_with_rate_limit_backoff(
            _do_request,
            description=f"validation search in r/{subreddit_name}",
        )
        validated = validate_arctic_shift_response(raw, endpoint)
        return len(validated.get("data", []))
    except Exception as exc:
        print(f"Warning: validation search failed for r/{subreddit_name}: {exc}")
        return 0


def _tier_from_count(count: int) -> str:
    """Convert a post count into a human-readable relevance tier."""
    if count >= _HIGH_THRESHOLD:
        return "high"
    if count >= _MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def discover_subreddits(
    topic: str,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
) -> List[DiscoveredSubreddit]:
    """
    Discover and validate subreddits relevant to the given topic.

    Returns a list of DiscoveredSubreddit objects sorted by relevance tier
    (high first) and then by subscriber count.

    Steps:
      1. Extract a short keyword from the topic for subreddit name search
      2. Search Arctic Shift for subreddits matching that keyword
      3. Validate each by checking post relevance
      4. Return subreddits with at least one matching post, sorted by tier
    """
    session = _make_session()

    # Use the first 3 significant words as the discovery keyword.
    # A shorter keyword finds more subreddits than the full topic query.
    words = [w for w in re.findall(r"[a-zA-Z]{3,}", topic) if len(w) >= 3]
    keyword = " ".join(words[:3]) if words else topic

    print(f"Discovering relevant subreddits for: {keyword!r}")

    raw_subreddits = _search_subreddits_by_keyword(keyword, session)

    if not raw_subreddits:
        print("  No subreddit candidates found via keyword search.")
        return []

    print(f"  Found {len(raw_subreddits)} candidates. Validating...")

    results: List[DiscoveredSubreddit] = []

    for raw in raw_subreddits[:MAX_DISCOVERY_CANDIDATES]:
        name = raw.get("name") or raw.get("subreddit") or ""
        name = name.strip().removeprefix("r/")

        if not name or not _is_valid_subreddit_name(name):
            continue

        description = clean_text(raw.get("public_description") or raw.get("title") or "")
        subscriber_count = int(raw.get("subscribers") or raw.get("subscriber_count") or 0)

        time.sleep(delay_seconds)

        count = _validate_subreddit_relevance(name, topic, session)

        if count == 0:
            continue

        tier = _tier_from_count(count)

        results.append(DiscoveredSubreddit(
            name=name,
            description=description,
            subscriber_count=subscriber_count,
            relevance_tier=tier,
            validation_post_count=count,
        ))

    # Sort: high relevance first, then medium, then by subscriber count
    tier_order = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda r: (tier_order.get(r.relevance_tier, 3), -r.subscriber_count))

    return results


def format_subscriber_count(count: int) -> str:
    """Format subscriber count for display (e.g. 1200000 -> '1.2M')."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.0f}k"
    return str(count)


def present_discovered_subreddits(subreddits: List[DiscoveredSubreddit]) -> None:
    """Print the discovered subreddit list to the terminal."""
    if not subreddits:
        print("  No relevant subreddits found.")
        return

    print(f"\nSuggested subreddits to search ({len(subreddits)} found):\n")

    for idx, sub in enumerate(subreddits, start=1):
        members = (
            f"{format_subscriber_count(sub.subscriber_count)} members"
            if sub.subscriber_count
            else "unknown size"
        )
        print(
            f"  {idx:2}. r/{sub.name:<25} "
            f"(relevance: {sub.relevance_tier:<6}, {members})"
        )
        if sub.description:
            truncated = sub.description[:80] + "..." if len(sub.description) > 80 else sub.description
            print(f"       {truncated}")


def confirm_subreddits_with_user(
    discovered: List[DiscoveredSubreddit],
    max_subreddits: int,
) -> List[str]:
    """
    Present discovered subreddits to the user and get confirmation.

    The user can:
    - Press Enter to accept all
    - Type numbers to remove specific subreddits (e.g. "2,4")
    - Type 'n' to enter their own list manually

    Returns a validated list of subreddit names ready for search.
    """
    present_discovered_subreddits(discovered)

    if not discovered:
        manual = input("\nEnter subreddits to search (comma-separated), or press Enter to skip: ").strip()
        if manual:
            return _parse_manual_subreddit_input(manual, max_subreddits)
        return []

    print(f"\nSearch all of these? [Y/n] or type numbers to remove (e.g. 2,4):")
    print("Or type 'custom' to enter your own list instead.")

    response = input("> ").strip().lower()

    if response == "n":
        return []

    if response == "custom":
        manual = input("Enter subreddits (comma-separated): ").strip()
        return _parse_manual_subreddit_input(manual, max_subreddits)

    selected = list(discovered)

    if response and response not in ("y", "yes", ""):
        # Try to parse as removal list
        try:
            to_remove = {int(x.strip()) for x in response.split(",") if x.strip()}
            selected = [s for idx, s in enumerate(discovered, start=1) if idx not in to_remove]
        except ValueError:
            print("Could not parse input — using all suggested subreddits.")

    # Ask if they want to add any
    additions = input(
        "\nAny subreddits to add? (comma-separated, or press Enter to skip): "
    ).strip()
    extra = _parse_manual_subreddit_input(additions, max_subreddits) if additions else []

    names = [s.name for s in selected] + extra
    names = list(dict.fromkeys(names))  # deduplicate while preserving order

    return names[:max_subreddits]


def _parse_manual_subreddit_input(value: str, max_subreddits: int) -> List[str]:
    """
    Parse and validate a comma-separated subreddit list from user input.

    Subreddit names are validated against the Reddit name pattern before use.
    """
    names = []
    for part in value.split(","):
        name = part.strip().removeprefix("r/").strip()
        if name and _is_valid_subreddit_name(name):
            names.append(name)
        elif name:
            print(f"  Skipping invalid subreddit name: {name!r}")

    return names[:max_subreddits]
