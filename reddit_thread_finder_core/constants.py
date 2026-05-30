"""Constants and hard guardrails for Reddit Thread Finder.

These values are intentionally conservative. The tool is meant to find a bounded
set of Reddit thread links for human review, not to monitor or mine Reddit at
scale.
"""

from __future__ import annotations


# ---------------------------------------------------------------------
# Abuse-prevention / purpose-limitation guardrails
# ---------------------------------------------------------------------

MAX_TOP_K = 100
MAX_SUBREDDITS = 5
MAX_QUERY_VARIANTS = 8
MAX_CANDIDATE_LIMIT_PER_SEARCH = 100
MAX_SEARCH_OPERATIONS = 40
MAX_UNIQUE_CANDIDATES = 1000

DEFAULT_DELAY_SECONDS = 0.25
DEFAULT_RATE_LIMIT_BACKOFF_SECONDS = 60
MAX_RATE_LIMIT_RETRIES = 2

# Conservative sort modes. Additional sorts would increase retrieval volume and
# could make the tool drift toward monitoring rather than link discovery.
ALLOWED_SORTS = ["relevance", "new"]

# This tool intentionally does not retrieve comments or use selftext/body content.
# Semantic matching is done against titles and lightweight metadata only.
USE_THREAD_BODY = False
USE_COMMENTS = False

# Pinned semantic model dependency.
# The revision is the Hugging Face repository SHA observed when this package was
# hardened. Keeping it pinned makes model loading more reproducible and reduces
# model supply-chain drift.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by",
    "can", "could", "did", "do", "does", "doing", "for", "from", "had",
    "has", "have", "having", "how", "i", "if", "in", "into", "is", "it",
    "its", "me", "my", "of", "on", "or", "our", "should", "so", "that",
    "the", "their", "them", "there", "these", "they", "this", "to",
    "too", "us", "use", "using", "was", "we", "were", "what", "when",
    "where", "which", "who", "why", "with", "would", "you", "your",
}

PAIN_PATTERNS = [
    r"\bstruggl(e|ing|ed)\b",
    r"\bpain\b",
    r"\bproblem\b",
    r"\bissue\b",
    r"\bmanual\b",
    r"\btedious\b",
    r"\bannoying\b",
    r"\bfrustrat(ed|ing|ion)\b",
    r"\bstuck\b",
    r"\bconfus(ed|ing|ion)\b",
    r"\boverwhelm(ed|ing)\b",
    r"\btoo much\b",
    r"\btakes forever\b",
    r"\bhow do i\b",
    r"\bwhat tool\b",
    r"\bwhich tool\b",
    r"\bany tool\b",
    r"\banyone using\b",
    r"\blooking for\b",
    r"\brecommend\b",
    r"\brecommendation\b",
    r"\balternative\b",
    r"\bvs\.\b",
    r"\bversus\b",
    r"\bworth it\b",
    r"\bneed help\b",
    r"\bhelp with\b",
]
