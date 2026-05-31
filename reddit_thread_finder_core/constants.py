"""Constants and hard guardrails for Reddit Thread Finder.

These values are intentionally conservative. The tool is meant to find a bounded
set of Reddit thread links for human review, not to monitor or mine Reddit at
scale.

This branch uses Arctic Shift (https://arctic-shift.photon-reddit.com) instead
of the Reddit official API. No credentials are required.
"""

from __future__ import annotations


# ---------------------------------------------------------------------
# Arctic Shift API
# ---------------------------------------------------------------------

# Base URL for the Arctic Shift public API.
# Arctic Shift is an independent open source project making archived Reddit
# data accessible. It is not affiliated with Reddit.
# See: https://github.com/ArthurHeitmann/arctic_shift
ARCTIC_SHIFT_BASE_URL = "https://arctic-shift.photon-reddit.com/api"

# User-Agent sent with all Arctic Shift requests.
# Identifies the tool so the server operator can understand traffic patterns.
ARCTIC_SHIFT_USER_AGENT = "reddit-thread-finder/arctic-shift-backend (github.com/Eyskiracing/reddit-thread-finder)"

# Request timeout in seconds. Arctic Shift documentation notes that complex
# queries can take over 5 seconds. This ceiling gives headroom without
# hanging indefinitely.
ARCTIC_SHIFT_TIMEOUT_SECONDS = 30

# Approximate data lag for Arctic Shift. Posts from within this many days of
# today may be missing or incomplete. Used to warn users when from_date is
# very recent.
ARCTIC_SHIFT_DATA_LAG_DAYS = 30

# ---------------------------------------------------------------------
# Abuse-prevention / purpose-limitation guardrails
# ---------------------------------------------------------------------

MAX_TOP_K = 100
# Increased from 5 to 10 to support subreddit discovery results.
MAX_SUBREDDITS = 10
MAX_QUERY_VARIANTS = 8
MAX_CANDIDATE_LIMIT_PER_SEARCH = 100
MAX_SEARCH_OPERATIONS = 40
MAX_UNIQUE_CANDIDATES = 1000

# Subreddit discovery limits
MAX_DISCOVERY_CANDIDATES = 20
MAX_DISCOVERY_VALIDATION_POSTS = 5

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
