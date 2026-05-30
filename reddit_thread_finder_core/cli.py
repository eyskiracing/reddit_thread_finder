"""Command-line interface and orchestration."""

from __future__ import annotations

import argparse

from .constants import (
    ALLOWED_SORTS,
    DEFAULT_DELAY_SECONDS,
    MAX_CANDIDATE_LIMIT_PER_SEARCH,
    MAX_SEARCH_OPERATIONS,
    MAX_SUBREDDITS,
    MAX_TOP_K,
    MODEL_NAME,
    MODEL_REVISION,
)
from .focus import (
    create_search_brief,
    print_search_brief,
    run_focus_builder_interactive,
    split_terms,
)
from .models import SearchConfig
from .output import print_results, write_json
from .query import generate_search_queries
from .reddit_search import fetch_candidates
from .scoring import semantic_rank
from .security import get_reddit_client
from .validation import (
    enforce_limits,
    parse_positive_int,
    parse_score,
    parse_yyyy_mm_dd,
)


def prompt_for_config(args: argparse.Namespace) -> SearchConfig:
    """
    Build a SearchConfig from CLI arguments or interactive prompts.

    Interactive users are guided through the generic Pain Point Search Focus
    Builder. Scripted users can pass --topic and optional focus-builder fields.
    """
    raw_topic = args.topic or input(
        "Describe the pain point you want to find Reddit threads about: "
    ).strip()

    interactive_focus = not args.topic and not args.skip_focus_builder

    if args.focused_query:
        must_include_terms = split_terms(args.must_include or "")
        avoid_terms = split_terms(args.avoid or "")
        brief = create_search_brief(
            raw_topic=raw_topic,
            target_persona=args.persona or "",
            task_or_situation=args.task or "",
            current_friction=args.friction or "",
            desired_outcome=args.outcome or "",
            must_include_terms=must_include_terms,
            avoid_terms=avoid_terms,
        )
        brief.focused_query = args.focused_query
    elif interactive_focus:
        brief = run_focus_builder_interactive(raw_topic)
    else:
        must_include_terms = split_terms(args.must_include or "")
        avoid_terms = split_terms(args.avoid or "")
        brief = create_search_brief(
            raw_topic=raw_topic,
            target_persona=args.persona or "",
            task_or_situation=args.task or "",
            current_friction=args.friction or "",
            desired_outcome=args.outcome or "",
            must_include_terms=must_include_terms,
            avoid_terms=avoid_terms,
        )

        # Show the brief when CLI users provide focus fields, but keep scripted
        # behavior quiet when they pass only --topic.
        if any([args.persona, args.task, args.friction, args.outcome, args.must_include, args.avoid]):
            print_search_brief(brief)

    topic = brief.focused_query

    from_date_value = args.from_date or input(
        "Search from what date? YYYY-MM-DD: "
    ).strip()

    min_score_value = (
        args.min_score
        if args.min_score is not None
        else input("Minimum semantic match score? 0.0 to 1.0: ").strip()
    )

    top_k_value = (
        args.top_k
        if args.top_k is not None
        else input(f"How many thread links should be returned? Max {MAX_TOP_K}: ").strip()
    )

    subreddits_value = args.subreddits
    if not subreddits_value:
        subreddits_value = input(
            f"Search which subreddit(s)? Comma-separated, max {MAX_SUBREDDITS}; "
            "or press enter for all: "
        ).strip() or "all"

    from_date = parse_yyyy_mm_dd(from_date_value)
    min_score = parse_score(str(min_score_value))
    top_k = parse_positive_int(str(top_k_value), "top_k")

    subreddits = [
        s.strip().removeprefix("r/")
        for s in subreddits_value.split(",")
        if s.strip()
    ]

    if not subreddits:
        subreddits = ["all"]

    if args.rank_by not in {"semantic", "composite"}:
        raise ValueError("--rank-by must be either 'semantic' or 'composite'.")

    config = SearchConfig(
        topic=topic,
        from_date=from_date,
        min_score=min_score,
        top_k=top_k,
        subreddits=subreddits,
        candidate_limit=args.candidate_limit,
        rank_by=args.rank_by,
        json_output=args.json_output,
        delay_seconds=args.delay_seconds,
        max_search_operations=args.max_search_operations,
        raw_topic=raw_topic,
        additional_queries=brief.alternative_queries,
        avoid_terms=brief.avoid_terms,
    )

    return enforce_limits(config)


def build_arg_parser() -> argparse.ArgumentParser:
    """Define the command-line interface for interactive or scripted local use."""
    parser = argparse.ArgumentParser(
        description=(
            "Find Reddit thread links semantically related to a pain point. "
            "Returns links and metadata only; does not fetch comments or thread bodies."
        )
    )

    parser.add_argument("--topic", help="Natural-language pain point to search for.")
    parser.add_argument(
        "--focused-query",
        help="Optional focused query to use after scope narrowing.",
    )
    parser.add_argument(
        "--persona",
        help="Who has the problem? Role, team, customer type, or persona.",
    )
    parser.add_argument(
        "--task",
        help="What the persona is trying to do; the job, workflow, or situation.",
    )
    parser.add_argument(
        "--friction",
        help="What makes the situation painful today.",
    )
    parser.add_argument(
        "--outcome",
        help="What better outcome the persona wants.",
    )
    parser.add_argument(
        "--must-include",
        help="Comma-separated terms that should anchor the search.",
    )
    parser.add_argument(
        "--avoid",
        help="Comma-separated terms/topics to filter out from title/metadata.",
    )
    parser.add_argument(
        "--skip-focus-builder",
        action="store_true",
        help="Skip the interactive focus builder and use --topic directly.",
    )
    parser.add_argument("--from-date", help="Start date in YYYY-MM-DD format.")
    parser.add_argument(
        "--min-score",
        type=float,
        help="Minimum semantic score from 0.0 to 1.0.",
    )
    parser.add_argument("--top-k", type=int, help=f"Number of links to return. Max {MAX_TOP_K}.")
    parser.add_argument(
        "--subreddits",
        help=f"Comma-separated subreddit list. Max {MAX_SUBREDDITS}. Use 'all' for r/all.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=50,
        help=f"Candidate limit per search operation. Max {MAX_CANDIDATE_LIMIT_PER_SEARCH}.",
    )
    parser.add_argument(
        "--rank-by",
        choices=["semantic", "composite"],
        default="composite",
        help="Rank by semantic match or composite discovery score.",
    )
    parser.add_argument(
        "--json-output",
        help="Optional path to write link results as JSON (must be within current directory).",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help="Small pause between Reddit search operations.",
    )
    parser.add_argument(
        "--max-search-operations",
        type=int,
        default=MAX_SEARCH_OPERATIONS,
        help=f"Maximum Reddit search operations. Hard cap {MAX_SEARCH_OPERATIONS}.",
    )

    return parser


def print_purpose_limitations(json_output: str | None = None) -> None:
    """Show runtime guardrails before retrieval begins."""
    print("\nPurpose limitation:")
    print(" - Returns Reddit links and lightweight metadata only.")
    print(" - Does not retrieve comments.")
    print(" - Does not use thread bodies for semantic matching.")
    print(" - Does not generate or post replies.")
    print(" - Reddit API client is forced into read-only mode.")
    print(f" - Returns at most {MAX_TOP_K} thread links.")
    print(f" - Conservative Reddit sort modes: {', '.join(ALLOWED_SORTS)}.")
    if json_output:
        print(f" - Results will be written to: {json_output}")


def main() -> None:
    """
    CLI entrypoint.

    Prints the purpose limitations at runtime so users see the guardrails before
    retrieval begins.
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    config = prompt_for_config(args)

    print_purpose_limitations(json_output=config.json_output)

    print(f"\nFocused search query: {config.topic}")
    print("\nQuery variants:")
    for query in generate_search_queries(config.topic, seed_queries=config.additional_queries):
        print(f" - {query}")

    reddit = get_reddit_client()

    print("\nFetching Reddit candidates...")
    candidates = fetch_candidates(reddit, config)
    print(f"Fetched {len(candidates)} unique candidate links after date filtering.")

    print(f"\nUsing semantic model: {MODEL_NAME} @ {MODEL_REVISION}")
    print("Running semantic ranking on titles and lightweight metadata only...")
    results = semantic_rank(config, candidates)

    print_results(results, rank_by=config.rank_by)

    if config.json_output:
        write_json(results, config.json_output)
        print(f"Saved JSON link results to: {config.json_output}")
