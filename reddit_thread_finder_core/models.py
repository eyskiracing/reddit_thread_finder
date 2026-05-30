"""Dataclasses and output schema definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


ALLOWED_OUTPUT_FIELDS = {
    "title",
    "subreddit",
    "url",
    "reddit_id",
    "created_at",
    "reddit_score",
    "num_comments",
    "semantic_score",
    "pain_score",
    "engagement_score",
    "recency_score",
    "composite_score",
    "matched_queries",
}

DISALLOWED_OUTPUT_FIELDS = {
    "author",
    "username",
    "user",
    "body",
    "selftext",
    "comments",
    "comment",
    "comment_body",
    "text_preview",
    "content",
}


@dataclass
class SearchBrief:
    """
    Generic product-agnostic search brief created by the focus builder.

    The brief turns messy natural language into a focused search intent. It is
    intentionally generic so the tool can work for any product category.
    """

    raw_pain_point: str
    focused_query: str
    target_persona: str = ""
    task_or_situation: str = ""
    current_friction: str = ""
    desired_outcome: str = ""
    must_include_terms: List[str] = field(default_factory=list)
    avoid_terms: List[str] = field(default_factory=list)
    alternative_queries: List[str] = field(default_factory=list)
    specificity_score: float = 0.0
    specificity_warnings: List[str] = field(default_factory=list)


@dataclass
class SearchConfig:
    """
    User-configurable search settings after validation and limit enforcement.

    The limits are intentionally conservative because this tool is meant for
    bounded, human-reviewed research rather than high-volume monitoring.
    """

    topic: str
    from_date: datetime
    min_score: float
    top_k: int
    subreddits: List[str]
    candidate_limit: int = 50
    rank_by: str = "composite"
    json_output: Optional[str] = None
    delay_seconds: float = 0.25
    max_search_operations: int = 40
    raw_topic: str = ""
    additional_queries: List[str] = field(default_factory=list)
    avoid_terms: List[str] = field(default_factory=list)


@dataclass
class RedditThreadResult:
    """
    Safe output record for one Reddit thread candidate.

    This dataclass intentionally excludes author, body/selftext, comments, and
    any field that would turn the tool into a content-collection system.
    """

    title: str
    subreddit: str
    url: str
    reddit_id: str
    created_at: str
    reddit_score: int
    num_comments: int
    semantic_score: float
    pain_score: float
    engagement_score: float
    recency_score: float
    composite_score: float
    matched_queries: List[str]
