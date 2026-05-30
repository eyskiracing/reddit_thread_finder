"""Generic Pain Point Search Focus Builder.

The focus builder helps users turn messy natural-language pain descriptions into
specific, product-agnostic search briefs. It avoids assuming any particular
market, product, or domain.
"""

from __future__ import annotations

import re
from typing import List

from .models import SearchBrief
from .text_utils import clean_text


BROAD_TERMS = {
    "ai",
    "automation",
    "automate",
    "platform",
    "solution",
    "tool",
    "software",
    "workflow",
    "productivity",
    "dashboard",
    "analytics",
    "management",
    "compliance",
    "security",
    "sales",
    "marketing",
    "operations",
    "business",
    "process",
    "data",
}

FRICTION_TERMS = {
    "manual",
    "manually",
    "spreadsheet",
    "spreadsheets",
    "script",
    "scripts",
    "copy",
    "paste",
    "tedious",
    "nightmare",
    "slow",
    "hard",
    "difficult",
    "stuck",
    "confusing",
    "takes forever",
    "maintain",
    "build",
    "reconcile",
    "track",
}

INTENT_TERMS = {
    "tool",
    "solution",
    "software",
    "recommend",
    "recommendation",
    "alternative",
    "better way",
    "how do",
    "anyone use",
    "is there",
}

ACTION_PATTERNS = [
    r"\bturn\b.+\binto\b",
    r"\bconvert\b.+\binto\b",
    r"\bmap\b.+\bto\b",
    r"\bmove\b.+\bfrom\b.+\bto\b",
    r"\bcentralize\b",
    r"\btrack\b",
    r"\bmanage\b",
    r"\bfind\b",
    r"\bprioritize\b",
    r"\banalyze\b",
]


def split_terms(value: str) -> List[str]:
    """Split comma-separated terms into clean, unique values."""
    terms = []
    seen = set()

    for item in (value or "").split(","):
        term = clean_text(item)
        key = term.lower()
        if term and key not in seen:
            seen.add(key)
            terms.append(term)

    return terms


def analyze_topic_specificity(raw_topic: str) -> tuple[float, List[str]]:
    """
    Score whether the raw topic is likely specific enough for Reddit search.

    This is a lightweight heuristic. It rewards concrete pain signals and warns
    when the input is mostly broad product/category language.
    """
    text = clean_text(raw_topic)
    lower = text.lower()
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_\-]+", lower)
    unique_words = set(words)

    score = 0.0
    warnings: List[str] = []

    if len(words) >= 8:
        score += 0.15
    else:
        warnings.append("The topic is very short; it may not contain enough context.")

    if any(re.search(pattern, lower) for pattern in ACTION_PATTERNS):
        score += 0.20
    else:
        warnings.append("Add a concrete action, such as 'turn X into Y' or 'track X across Y'.")

    if any(term in lower for term in FRICTION_TERMS):
        score += 0.20
    else:
        warnings.append("Add the current friction, such as manual work, spreadsheets, scripts, or rework.")

    if any(term in lower for term in INTENT_TERMS):
        score += 0.10

    broad_hits = sorted(unique_words.intersection(BROAD_TERMS))
    if broad_hits:
        score -= min(0.20, len(broad_hits) * 0.04)
        warnings.append(
            "Broad terms detected: "
            + ", ".join(broad_hits[:6])
            + ". Anchor them to a specific workflow or object of pain."
        )

    concreteish_words = [
        word for word in unique_words
        if len(word) >= 5 and word not in BROAD_TERMS
    ]
    if len(concreteish_words) >= 5:
        score += 0.20
    else:
        warnings.append("Add more specific nouns, systems, workflows, or artifacts.")

    if " for " in lower or " as " in lower or " customers" in lower or " team" in lower:
        score += 0.15
    else:
        warnings.append("Add who has the problem: a role, team, customer type, or persona.")

    score = max(0.0, min(1.0, score))
    return round(score, 2), warnings


def compact_join(parts: List[str], max_chars: int = 220) -> str:
    """Join non-empty parts into a compact search query."""
    text = clean_text(" ".join(part for part in parts if clean_text(part)))
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0]


def build_focused_query(
    raw_topic: str,
    target_persona: str = "",
    task_or_situation: str = "",
    current_friction: str = "",
    desired_outcome: str = "",
    must_include_terms: List[str] | None = None,
) -> str:
    """
    Build a concise product-agnostic focused query.

    The query always anchors to raw_topic so the original pain description is
    never lost, even when structured fields are only partially filled.
    The query should describe the pain, not the vendor category. It prioritizes
    persona, task, object of pain, friction, outcome, and must-include terms.
    """
    must_include_terms = must_include_terms or []

    structured_parts = [p for p in [target_persona, task_or_situation, current_friction, desired_outcome] if p]

    if structured_parts:
        # Always include raw_topic as the anchor, then layer in structured context.
        return compact_join(
            [raw_topic] + structured_parts + [" ".join(must_include_terms)]
        )

    return compact_join([raw_topic, " ".join(must_include_terms)])


def build_alternative_queries(
    focused_query: str,
    target_persona: str = "",
    task_or_situation: str = "",
    current_friction: str = "",
    desired_outcome: str = "",
    must_include_terms: List[str] | None = None,
) -> List[str]:
    """Create a few bounded alternative queries for candidate retrieval."""
    must_include_terms = must_include_terms or []
    must = " ".join(must_include_terms)

    candidates = [
        focused_query,
        compact_join([target_persona, task_or_situation, current_friction]),
        compact_join([task_or_situation, desired_outcome, "tool"]),
        compact_join([current_friction, desired_outcome, "help"]),
        compact_join([must, task_or_situation]),
    ]

    unique = []
    seen = set()
    for query in candidates:
        q = clean_text(query)
        key = q.lower()
        if q and key not in seen:
            seen.add(key)
            unique.append(q)

    return unique[:5]


def create_search_brief(
    raw_topic: str,
    target_persona: str = "",
    task_or_situation: str = "",
    current_friction: str = "",
    desired_outcome: str = "",
    must_include_terms: List[str] | None = None,
    avoid_terms: List[str] | None = None,
) -> SearchBrief:
    """Create a generic search brief from raw and structured pain-point inputs."""
    must_include_terms = must_include_terms or []
    avoid_terms = avoid_terms or []

    specificity_score, warnings = analyze_topic_specificity(raw_topic)
    focused_query = build_focused_query(
        raw_topic=raw_topic,
        target_persona=target_persona,
        task_or_situation=task_or_situation,
        current_friction=current_friction,
        desired_outcome=desired_outcome,
        must_include_terms=must_include_terms,
    )
    alternative_queries = build_alternative_queries(
        focused_query=focused_query,
        target_persona=target_persona,
        task_or_situation=task_or_situation,
        current_friction=current_friction,
        desired_outcome=desired_outcome,
        must_include_terms=must_include_terms,
    )

    return SearchBrief(
        raw_pain_point=clean_text(raw_topic),
        focused_query=focused_query,
        target_persona=clean_text(target_persona),
        task_or_situation=clean_text(task_or_situation),
        current_friction=clean_text(current_friction),
        desired_outcome=clean_text(desired_outcome),
        must_include_terms=must_include_terms,
        avoid_terms=avoid_terms,
        alternative_queries=alternative_queries,
        specificity_score=specificity_score,
        specificity_warnings=warnings,
    )


def print_search_brief(brief: SearchBrief) -> None:
    """Display the search brief in plain language before Reddit retrieval."""
    print("\nPain Point Search Focus Builder")
    print("--------------------------------")
    print(f"Specificity score: {brief.specificity_score:.2f} / 1.00")

    if brief.specificity_warnings:
        print("\nSpecificity notes:")
        for warning in brief.specificity_warnings:
            print(f" - {warning}")

    print("\nSearch brief:")
    print(f"Pain point: {brief.raw_pain_point}")
    print(f"Target persona: {brief.target_persona or 'not specified'}")
    print(f"Task / situation: {brief.task_or_situation or 'not specified'}")
    print(f"Current friction: {brief.current_friction or 'not specified'}")
    print(f"Desired outcome: {brief.desired_outcome or 'not specified'}")
    print(f"Must include: {', '.join(brief.must_include_terms) if brief.must_include_terms else 'none'}")
    print(f"Avoid: {', '.join(brief.avoid_terms) if brief.avoid_terms else 'none'}")
    print(f"\nFocused query: {brief.focused_query}")

    if brief.alternative_queries:
        print("\nAlternative queries:")
        for query in brief.alternative_queries:
            print(f" - {query}")


def run_focus_builder_interactive(raw_topic: str) -> SearchBrief:
    """
    Guide an interactive user through generic scope-narrowing questions.

    The prompts are product-agnostic and work for any market or pain point.
    """
    print("\nLet's make the search more specific before searching Reddit.")
    print("Use plain English. Press Enter to skip anything you do not know.")

    target_persona = input(
        "\nWho has this problem? "
        "(role, team, customer type, or persona): "
    ).strip()

    task_or_situation = input(
        "What are they trying to do? "
        "(the job, workflow, or situation): "
    ).strip()

    current_friction = input(
        "What makes it painful today? "
        "(manual work, spreadsheets, scripts, rework, scattered tools, etc.): "
    ).strip()

    desired_outcome = input(
        "What outcome do they want instead? "
        "(what would be better, faster, easier, or more accurate): "
    ).strip()

    must_include = split_terms(
        input(
            "Any words that must be included? "
            "(comma-separated, optional): "
        ).strip()
    )

    avoid_terms = split_terms(
        input(
            "Any words or topics to avoid? "
            "(comma-separated, optional): "
        ).strip()
    )

    brief = create_search_brief(
        raw_topic=raw_topic,
        target_persona=target_persona,
        task_or_situation=task_or_situation,
        current_friction=current_friction,
        desired_outcome=desired_outcome,
        must_include_terms=must_include,
        avoid_terms=avoid_terms,
    )

    print_search_brief(brief)

    override = input(
        "\nPress Enter to use this focused query, or type a better focused query: "
    ).strip()

    if override:
        brief.focused_query = clean_text(override)
        brief.alternative_queries = build_alternative_queries(
            focused_query=brief.focused_query,
            target_persona=brief.target_persona,
            task_or_situation=brief.task_or_situation,
            current_friction=brief.current_friction,
            desired_outcome=brief.desired_outcome,
            must_include_terms=brief.must_include_terms,
        )

    return brief
