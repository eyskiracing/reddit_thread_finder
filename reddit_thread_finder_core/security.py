"""Credential handling, .env checks, and Reddit client creation."""

from __future__ import annotations

import os
import re
import stat
import time
from pathlib import Path

import praw
from dotenv import load_dotenv

from .constants import DEFAULT_RATE_LIMIT_BACKOFF_SECONDS, MAX_RATE_LIMIT_RETRIES

# Resolve .env path relative to the package root, not the caller's CWD.
# This ensures the file is found and permission-checked regardless of
# which directory the user launches the tool from.
_ENV_PATH = Path(__file__).parent.parent / ".env"

# Reddit's required User-Agent format:
# <platform>:<app_id>:<version> (by /u/<username>)
# https://github.com/reddit-archive/reddit/wiki/API
_USER_AGENT_PATTERN = re.compile(r".+:.+:.+\s+\(by /u/.+\)")


def warn_if_env_file_permissions_are_loose(env_path: str = str(_ENV_PATH)) -> None:
    """
    Warn when .env is readable by group/other users on macOS/Linux.

    This is a local safety check only. Windows permissions are managed differently,
    so the check is skipped there.
    """
    path = Path(env_path)

    if not path.exists():
        return

    if os.name == "nt":
        return

    mode = path.stat().st_mode

    group_or_other_can_read = bool(mode & (stat.S_IRGRP | stat.S_IROTH))
    group_or_other_can_write = bool(mode & (stat.S_IWGRP | stat.S_IWOTH))

    if group_or_other_can_read or group_or_other_can_write:
        print(
            "Security warning: your .env file may be readable or writable by "
            "other local users. Recommended fix: chmod 600 .env"
        )


def _warn_if_user_agent_format_invalid(user_agent: str) -> None:
    """
    Warn when REDDIT_USER_AGENT does not follow Reddit's required API format.

    Reddit requires: <platform>:<app_id>:<version> (by /u/<username>)
    Non-compliant User-Agents may result in request throttling or bans.
    See: https://github.com/reddit-archive/reddit/wiki/API
    """
    if not _USER_AGENT_PATTERN.match(user_agent):
        print(
            "Compliance warning: REDDIT_USER_AGENT does not follow Reddit's "
            "required format: '<platform>:<app_id>:<version> (by /u/<username>)'. "
            "Example: script:com.yourname.reddit-thread-finder:v0.1.0 (by /u/yourusername). "
            "Non-compliant User-Agents may be throttled. "
            "See: https://github.com/reddit-archive/reddit/wiki/API"
        )


def get_reddit_client() -> praw.Reddit:
    """
    Create a PRAW Reddit client using local environment variables.

    The .env file is resolved relative to the project root, not the caller's
    working directory. The client is forced into read-only mode — even if future
    code accidentally introduces write-capable methods, the Reddit client will
    not be authenticated for posting or commenting.
    """
    warn_if_env_file_permissions_are_loose(str(_ENV_PATH))
    load_dotenv(dotenv_path=_ENV_PATH)

    required = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
    ]

    missing = [name for name in required if not os.getenv(name)]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + f". Add them to your .env file at: {_ENV_PATH}"
        )

    if os.getenv("REDDIT_USERNAME") or os.getenv("REDDIT_PASSWORD"):
        print(
            "Security note: this read-only tool does not use Reddit username/password. "
            "Remove REDDIT_USERNAME and REDDIT_PASSWORD from .env if present."
        )

    user_agent = os.getenv("REDDIT_USER_AGENT", "")
    _warn_if_user_agent_format_invalid(user_agent)

    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=user_agent,
    )

    reddit.read_only = True

    return reddit


def looks_like_rate_limit_error(exc: Exception) -> bool:
    """
    Best-effort rate-limit detection across PRAW/prawcore versions.

    PRAW often handles Reddit API rate limits internally, but this guard catches
    common 429 / ratelimit cases and backs off instead of retrying aggressively.
    """
    text = str(exc).lower()

    if "ratelimit" in text or "rate limit" in text or "too many requests" in text:
        return True

    status = getattr(exc, "status_code", None)
    if status == 429:
        return True

    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    if response_status == 429:
        return True

    return False


def get_retry_after_seconds(
    exc: Exception,
    default_seconds: int = DEFAULT_RATE_LIMIT_BACKOFF_SECONDS,
) -> int:
    """Use Retry-After if available; otherwise use a conservative default."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) or {}

    retry_after = headers.get("Retry-After") or headers.get("retry-after")

    if retry_after:
        try:
            return max(1, min(600, int(float(retry_after))))
        except ValueError:
            pass

    return default_seconds


def run_with_rate_limit_backoff(callable_obj, *, description: str):
    """
    Execute a PRAW call with limited, conservative retries for rate-limit errors.

    The goal is to respect rate limits and fail safely rather than aggressively
    retrying. This helper is intentionally generic so Reddit search code stays
    focused on retrieval logic.
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
