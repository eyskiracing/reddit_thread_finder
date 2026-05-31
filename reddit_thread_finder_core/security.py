"""HTTP response validation and rate-limit backoff for Arctic Shift API calls.

This module replaces the credential-handling and Reddit client setup from the
main branch. There are no credentials, no .env file, and no Reddit client in
this branch.

Security responsibilities in this module:
- Validate all Arctic Shift API responses before they enter the pipeline
- Back off gracefully when rate limits are encountered
- Never transmit personal data or credentials in requests
"""

from __future__ import annotations

import time
from typing import Any

from .constants import DEFAULT_RATE_LIMIT_BACKOFF_SECONDS, MAX_RATE_LIMIT_RETRIES


# ---------------------------------------------------------------------------
# HTTP response validation
# ---------------------------------------------------------------------------

def validate_arctic_shift_response(response_json: Any, endpoint: str) -> dict:
    """
    Validate an Arctic Shift API response before it enters the pipeline.

    This function fails closed: if the response is not a dict, does not contain
    the expected 'data' key, or contains unexpected top-level structure, it raises
    a clear error rather than passing unknown data downstream.

    We parse JSON from a third-party server we do not control. Validating the
    structure here means the rest of the codebase can trust the shape of the data.
    """
    if not isinstance(response_json, dict):
        raise ValueError(
            f"Arctic Shift response from {endpoint} was not a JSON object. "
            f"Got type: {type(response_json).__name__}"
        )

    if "data" not in response_json:
        error_msg = response_json.get("error") or response_json.get("message") or "unknown"
        raise ValueError(
            f"Arctic Shift response from {endpoint} missing 'data' field. "
            f"Server message: {error_msg}"
        )

    data = response_json["data"]

    if not isinstance(data, list):
        raise ValueError(
            f"Arctic Shift response 'data' from {endpoint} was not a list. "
            f"Got type: {type(data).__name__}"
        )

    return response_json


def validate_post_fields(post: Any, endpoint: str) -> dict:
    """
    Validate that a single post object from Arctic Shift has expected fields.

    We check for required fields and type-check the ones we use in scoring.
    Unexpected extra fields are ignored rather than rejected — the API may
    return more fields than we use, and that is fine.

    Fields we intentionally do NOT use (body, selftext, author) are not checked
    for presence and are never read downstream.
    """
    if not isinstance(post, dict):
        raise ValueError(
            f"Arctic Shift post from {endpoint} was not a dict. "
            f"Got type: {type(post).__name__}"
        )

    required = ["id", "title", "subreddit"]
    missing = [field for field in required if field not in post]
    if missing:
        raise ValueError(
            f"Arctic Shift post from {endpoint} missing required fields: "
            + ", ".join(missing)
        )

    if not isinstance(post.get("title", ""), str):
        raise ValueError(f"Arctic Shift post 'title' field is not a string.")

    if not isinstance(post.get("subreddit", ""), str):
        raise ValueError(f"Arctic Shift post 'subreddit' field is not a string.")

    return post


def validate_subreddit_fields(subreddit: Any, endpoint: str) -> dict:
    """
    Validate that a subreddit object from Arctic Shift has expected fields.
    """
    if not isinstance(subreddit, dict):
        raise ValueError(
            f"Arctic Shift subreddit from {endpoint} was not a dict. "
            f"Got type: {type(subreddit).__name__}"
        )

    if "name" not in subreddit and "subreddit" not in subreddit:
        raise ValueError(
            f"Arctic Shift subreddit from {endpoint} missing 'name' or 'subreddit' field."
        )

    return subreddit


# ---------------------------------------------------------------------------
# Rate-limit detection and backoff
# ---------------------------------------------------------------------------

def looks_like_rate_limit_error(exc: Exception) -> bool:
    """
    Best-effort rate-limit detection for requests library exceptions.

    Arctic Shift returns standard HTTP 429 responses when rate limited.
    The requests library raises HTTPError for 4xx responses when
    raise_for_status() is called.
    """
    text = str(exc).lower()

    if "429" in text or "too many requests" in text or "rate limit" in text:
        return True

    status_code = getattr(exc, "response", None)
    if status_code is not None:
        code = getattr(status_code, "status_code", None)
        if code == 429:
            return True

    return False


def get_retry_after_seconds(
    exc: Exception,
    default_seconds: int = DEFAULT_RATE_LIMIT_BACKOFF_SECONDS,
) -> int:
    """
    Use Retry-After header from Arctic Shift response if available.

    Arctic Shift includes X-RateLimit-Remaining to signal remaining budget.
    If we hit a 429, we respect Retry-After or fall back to a conservative default.
    """
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) or {}

    retry_after = headers.get("Retry-After") or headers.get("retry-after")

    if retry_after:
        try:
            return max(1, min(600, int(float(retry_after))))
        except ValueError:
            pass

    return default_seconds


def check_rate_limit_header(headers: dict) -> None:
    """
    Log a warning when the Arctic Shift rate limit budget is running low.

    This is a proactive check done after each successful response. If remaining
    budget is very low, we print a warning so the user knows why the tool may
    slow down.
    """
    remaining = headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining")

    if remaining is not None:
        try:
            remaining_int = int(float(remaining))
            if remaining_int < 5:
                print(
                    f"Note: Arctic Shift rate limit budget is low "
                    f"({remaining_int} requests remaining). "
                    "The tool will back off automatically if needed."
                )
        except ValueError:
            pass


def run_with_rate_limit_backoff(callable_obj, *, description: str):
    """
    Execute an HTTP call with conservative retries for rate-limit errors.

    Same pattern as the main branch's PRAW backoff, adapted for the requests
    library. Fails safely rather than retrying aggressively.
    """
    attempt = 0

    while True:
        try:
            return callable_obj()
        except Exception as exc:
            if not looks_like_rate_limit_error(exc):
                raise

            attempt += 1

            if attempt > MAX_RATE_LIMIT_RETRIES:
                raise RuntimeError(
                    f"Rate limit persisted after {MAX_RATE_LIMIT_RETRIES} "
                    f"retries during {description}."
                ) from exc

            wait_seconds = get_retry_after_seconds(exc)
            print(
                f"Rate limit detected during {description}. "
                f"Waiting {wait_seconds} seconds before retry "
                f"{attempt}/{MAX_RATE_LIMIT_RETRIES}."
            )
            time.sleep(wait_seconds)
