"""Safe terminal and JSON output helpers."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .constants import MAX_TOP_K
from .models import (
    ALLOWED_OUTPUT_FIELDS,
    DISALLOWED_OUTPUT_FIELDS,
    RedditThreadResult,
)


def print_results(results: Sequence[RedditThreadResult], rank_by: str) -> None:
    """Print safe thread-link results to the terminal without body/comment data."""
    if not results:
        print("\nNo matching threads found.")
        return

    print(f"\nTop matching Reddit thread links, ranked by {rank_by}:\n")

    for idx, result in enumerate(results, start=1):
        print(f"{idx}. {result.title}")
        print(f"   r/{result.subreddit} | {result.created_at}")
        print(f"   Semantic: {result.semantic_score:.4f}")
        print(f"   Composite: {result.composite_score:.4f}")
        print(f"   Pain signal: {result.pain_score:.4f}")
        print(f"   Reddit score: {result.reddit_score}")
        print(f"   Comments: {result.num_comments}")
        print(f"   URL: {result.url}")
        print(f"   Matched queries: {', '.join(result.matched_queries[:5])}")
        print()


def result_to_safe_dict(result: RedditThreadResult) -> dict:
    """
    Convert a result to JSON-safe output while enforcing the output contract.

    This function fails closed: if a future code change adds unexpected fields,
    JSON export raises an error instead of silently writing sensitive content.
    """
    data = asdict(result)
    keys = set(data.keys())

    disallowed = keys.intersection(DISALLOWED_OUTPUT_FIELDS)
    if disallowed:
        raise RuntimeError(
            "Unsafe output field(s) detected: " + ", ".join(sorted(disallowed))
        )

    unexpected = keys.difference(ALLOWED_OUTPUT_FIELDS)
    if unexpected:
        raise RuntimeError(
            "Unexpected output field(s) detected: " + ", ".join(sorted(unexpected))
        )

    return data


def _resolve_safe_output_path(output_path: str) -> Path:
    """
    Resolve the output path and reject paths that escape the current directory.

    This prevents a --json-output argument like '../../etc/something' or an
    absolute path outside the working directory from writing files in unexpected
    locations. Tilde expansion is also resolved before the check.
    """
    resolved = Path(output_path).expanduser().resolve()
    cwd = Path.cwd().resolve()

    try:
        resolved.relative_to(cwd)
    except ValueError:
        raise ValueError(
            f"Output path must be within the current working directory.\n"
            f"  Requested: {resolved}\n"
            f"  Working directory: {cwd}"
        )

    return resolved


def write_json(results: Sequence[RedditThreadResult], output_path: str) -> None:
    """Write capped, schema-validated metadata results to a JSON file."""
    safe_path = _resolve_safe_output_path(output_path)
    safe_results = [result_to_safe_dict(result) for result in results[:MAX_TOP_K]]

    # Ensure the parent directory exists (e.g. if --json-output is output/results.json).
    safe_path.parent.mkdir(parents=True, exist_ok=True)

    with open(safe_path, "w", encoding="utf-8") as f:
        json.dump(safe_results, f, indent=2)
