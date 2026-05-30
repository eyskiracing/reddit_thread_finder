"""Semantic and heuristic scoring for candidate thread links."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sentence_transformers import SentenceTransformer, util

from .constants import MODEL_NAME, MODEL_REVISION, PAIN_PATTERNS
from .models import RedditThreadResult, SearchConfig
from .text_utils import clean_text

# Module-level cache so the model is loaded once per process.
# If semantic_rank() is called multiple times (e.g. in tests or batch use),
# the model is not re-downloaded or re-initialized on each call.
_model_cache: Optional[SentenceTransformer] = None


def normalize_cosine_score(raw_score: float) -> float:
    """
    Convert cosine similarity from roughly -1..1 into a user-facing 0..1 score.

    The normalized score is easier for users to reason about when setting the
    --min-score threshold.
    """
    return max(0.0, min(1.0, (raw_score + 1.0) / 2.0))


def compute_pain_score(text: str) -> float:
    """
    Estimate whether the title/metadata contains pain or buying-intent language.

    This is a lightweight heuristic, not an LLM classification step. It is only
    used as a ranking signal after semantic relevance passes the minimum score.
    """
    lower = text.lower()
    hits = 0

    for pattern in PAIN_PATTERNS:
        if re.search(pattern, lower):
            hits += 1

    return min(1.0, hits / 4.0)


def compute_engagement_score(reddit_score: int, num_comments: int) -> float:
    """
    Convert Reddit score and comment count into a bounded engagement signal.

    Log scaling prevents very large threads from overwhelming the ranking.
    """
    raw = max(0, reddit_score) + (2 * max(0, num_comments))
    return min(1.0, math.log1p(raw) / math.log1p(1000))


def compute_recency_score(created_utc: float, from_date: datetime) -> float:
    """
    Score how recent a thread is within the user's requested search window.

    A newer thread receives a higher score. This is a ranking signal only; exact
    inclusion/exclusion is handled earlier by the from_date filter.
    """
    now = datetime.now(timezone.utc)
    created = datetime.fromtimestamp(created_utc, tz=timezone.utc)

    total_window_seconds = max(1.0, (now - from_date).total_seconds())
    age_seconds = max(0.0, (now - created).total_seconds())

    return max(0.0, min(1.0, 1.0 - (age_seconds / total_window_seconds)))


def compute_composite_score(
    semantic_score: float,
    pain_score: float,
    engagement_score: float,
    recency_score: float,
) -> float:
    """
    Combine relevance and discovery signals into one ranking score.

    Semantic relevance remains the dominant factor. Pain, engagement, and recency
    help prioritize which already-relevant links a human may want to inspect.
    """
    return (
        0.75 * semantic_score
        + 0.10 * pain_score
        + 0.10 * engagement_score
        + 0.05 * recency_score
    )


def load_embedding_model() -> SentenceTransformer:
    """
    Load the pinned embedding model with remote code execution disabled.

    Uses a module-level cache so repeated calls within the same process do not
    re-initialize the model. Keeping load logic in a separate function makes the
    model supply-chain control easy to audit and test.
    """
    global _model_cache
    if _model_cache is None:
        _model_cache = SentenceTransformer(
            MODEL_NAME,
            revision=MODEL_REVISION,
            trust_remote_code=False,
        )
    return _model_cache


def semantic_rank(
    config: SearchConfig,
    candidates: Dict[str, Tuple[object, str, List[str]]],
) -> List[RedditThreadResult]:
    """
    Embed the user pain point and candidate metadata, then rank thread links.

    The candidate text intentionally contains title/subreddit/flair only. This
    preserves the tool's link-discovery purpose and avoids processing Reddit
    bodies, comments, or author data.
    """
    if not candidates:
        return []

    model = load_embedding_model()

    items = list(candidates.items())

    # Filter out items with empty semantic text before encoding to avoid
    # wasting embedding compute on blank entries.
    items = [(rid, (sub, text, queries)) for rid, (sub, text, queries) in items if text.strip()]

    if not items:
        return []

    texts = [item[1][1] for item in items]

    query_embedding = model.encode(config.topic, convert_to_tensor=True)
    thread_embeddings = model.encode(texts, convert_to_tensor=True)

    similarities = util.cos_sim(query_embedding, thread_embeddings)[0]

    results: List[RedditThreadResult] = []

    for idx, raw_similarity in enumerate(similarities):
        reddit_id, (submission, semantic_text, matched_queries) = items[idx]
        semantic_score = normalize_cosine_score(float(raw_similarity))

        if semantic_score < config.min_score:
            continue

        pain_score = compute_pain_score(semantic_text)
        engagement_score = compute_engagement_score(
            reddit_score=getattr(submission, "score", 0),
            num_comments=getattr(submission, "num_comments", 0),
        )
        recency_score = compute_recency_score(
            created_utc=getattr(submission, "created_utc", 0),
            from_date=config.from_date,
        )
        composite_score = compute_composite_score(
            semantic_score=semantic_score,
            pain_score=pain_score,
            engagement_score=engagement_score,
            recency_score=recency_score,
        )

        created_at = datetime.fromtimestamp(
            submission.created_utc,
            tz=timezone.utc,
        ).strftime("%Y-%m-%d")

        results.append(
            RedditThreadResult(
                title=clean_text(getattr(submission, "title", "")),
                subreddit=str(getattr(submission, "subreddit", "")),
                url=f"https://www.reddit.com{submission.permalink}",
                reddit_id=reddit_id,
                created_at=created_at,
                reddit_score=int(getattr(submission, "score", 0)),
                num_comments=int(getattr(submission, "num_comments", 0)),
                semantic_score=round(semantic_score, 4),
                pain_score=round(pain_score, 4),
                engagement_score=round(engagement_score, 4),
                recency_score=round(recency_score, 4),
                composite_score=round(composite_score, 4),
                matched_queries=matched_queries,
            )
        )

    if config.rank_by == "semantic":
        results.sort(key=lambda r: (r.semantic_score, r.composite_score), reverse=True)
    else:
        results.sort(key=lambda r: (r.composite_score, r.semantic_score), reverse=True)

    return results[: config.top_k]
