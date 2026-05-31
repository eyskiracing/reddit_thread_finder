# Reddit Thread Finder

A constrained, local Python CLI for finding Reddit thread links semantically relevant to a specific pain point.

```text
Find Reddit threads that a human can open, read, and decide whether to respond to manually.
```

This tool is **not** designed to automate Reddit engagement, scrape Reddit content, build a Reddit dataset, or generate or post replies.

---

## Two versions available

| Branch | Data source | Credentials required | Status |
|---|---|---|---|
| `arctic-shift-backend` (this branch) | Arctic Shift API | None | Works immediately |
| `main` | Reddit official API via PRAW | Reddit API approval required | Blocked pending Reddit approval |

**If you are a new user, you are in the right place.** This branch requires no API credentials and no Reddit account. Just install and run.

If you have been granted Reddit API access and want to use the official Reddit API version, switch to the `main` branch.

---

## Why two versions?

Reddit updated their API policy in May 2026 to require explicit approval before any application can access their API. The approval process is not self-serve and may take days or weeks.

This branch uses [Arctic Shift](https://github.com/ArthurHeitmann/arctic_shift) — an open source project that makes archived Reddit data accessible through a free public API with no credentials required.

The tradeoff is documented clearly in the [Known limitations](#known-limitations) section below.

---

## Non-technical user quickstart

If you are not comfortable with Terminal, Python, or virtual environments, start here:

```text
QUICKSTART_NON_TECHNICAL.md
```

This package also includes simple setup and run scripts:

```text
setup_mac.command
run_mac.command
setup_windows.bat
run_windows.bat
```

---

## What this tool does

1. Accepts a natural-language pain point.
2. Runs the Pain Point Search Focus Builder to narrow the search.
3. **Automatically discovers relevant subreddits** — no Reddit knowledge required.
4. Confirms the subreddit list with you before searching.
5. Searches Arctic Shift for posts matching your topic within those subreddits.
6. Filters results by date, semantic score, and optional avoid terms.
7. Uses semantic matching against thread title and lightweight metadata only.
8. Returns Reddit thread links and lightweight metadata for human review.

---

## What this tool does not do

This tool intentionally does **not**:

- retrieve thread body / selftext
- retrieve comments
- retrieve or export Reddit usernames / authors
- generate Reddit replies
- post comments or submit posts
- vote, message users, or moderate communities
- build a Reddit content dataset
- train or fine-tune an AI model
- run continuous Reddit monitoring

The output is limited to:

```text
title
subreddit
URL
created date
Reddit score
number of comments
semantic score
pain signal score
engagement score
recency score
composite score
matched search queries
```

---

## Installation

### 1. Clone or download the project

```bash
git clone https://github.com/Eyskiracing/reddit-thread-finder.git
cd reddit-thread-finder
git checkout arctic-shift-backend
```

### 2. Create a virtual environment

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install runtime dependencies

```bash
pip install -r requirements.txt
```

### 4. Run tests

```bash
python -m unittest discover -s tests
```

### 5. Run the tool

```bash
python reddit_thread_finder.py
```

No `.env` file needed. No Reddit credentials needed. The tool will ask you questions interactively.

---

## Subreddit discovery

Because Arctic Shift requires subreddit-scoped searches, this branch adds an automatic subreddit discovery step.

Before searching, the tool will:

1. Use your focused query to find candidate subreddits by keyword
2. Validate each candidate by checking how many relevant posts it contains
3. Present you with a ranked shortlist, for example:

```text
Discovering relevant subreddits...
Found 12 candidates. Validating...

Suggested subreddits to search:
  1. r/customerservice     (relevance: high,   847k members)
  2. r/sysadmin            (relevance: high,   2.1M members)
  3. r/ITManagers          (relevance: medium, 124k members)
  4. r/helpdesk            (relevance: medium,  89k members)
  5. r/startups            (relevance: medium, 1.2M members)
  ... 4 more

Search all of these? [Y/n] or type numbers to remove (e.g. 2,4):
```

You can confirm, remove subreddits, or type additional ones before the search begins.

---

## Typical usage

Interactive (recommended for most users):

```bash
python reddit_thread_finder.py
```

Scripted with focus builder fields:

```bash
python reddit_thread_finder.py \
  --topic "support teams manually tagging tickets to find product issues" \
  --persona "support team leads" \
  --task "find recurring product issues from customer tickets" \
  --friction "manually tagging and reviewing tickets in spreadsheets" \
  --outcome "automatically surface patterns without manual review" \
  --from-date 2026-01-01 \
  --min-score 0.70 \
  --top-k 25 \
  --rank-by composite \
  --json-output results.json
```

Skip the focus builder and use a topic directly:

```bash
python reddit_thread_finder.py \
  --topic "small businesses struggling with SOC 2 evidence collection" \
  --skip-focus-builder \
  --from-date 2026-01-01 \
  --min-score 0.70 \
  --top-k 25
```

---

## Data source: Arctic Shift

This branch uses the Arctic Shift public API at `https://arctic-shift.photon-reddit.com`.

Arctic Shift is an independent open source project maintained by [ArthurHeitmann](https://github.com/ArthurHeitmann/arctic_shift). It is not affiliated with Reddit.

**What this means for users:**

- No credentials, no Reddit account, no API approval needed
- Data covers posts across all public subreddits
- Data may be 2–4 weeks behind real-time (see Known limitations)
- The API is free and rate-limited; normal use will not hit limits

**Trust considerations:**

This tool makes HTTP requests to a community-run third-party server. The project is open source, actively maintained, and widely used by researchers. However, it is run by one developer, not a company. Users should be aware of this dependency. See [SECURITY.md](SECURITY.md) for full details.

---

## Abuse-prevention limits

```text
MAX_TOP_K = 100
MAX_SUBREDDITS = 10
MAX_QUERY_VARIANTS = 8
MAX_CANDIDATE_LIMIT_PER_SEARCH = 100
MAX_SEARCH_OPERATIONS = 40
MAX_UNIQUE_CANDIDATES = 1000
MAX_DISCOVERY_CANDIDATES = 20
```

---

## Dependency security hardening

Runtime dependencies:

```text
requests>=2.31.0,<3.0.0
sentence-transformers>=3.1.1,<4.0.0
```

The `sentence-transformers` minimum is intentionally set above the vulnerable `<3.1.0` range.

`praw` and `python-dotenv` are not used in this branch.

---

## Model supply-chain hardening

```python
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
```

The model loads with:

```python
trust_remote_code=False
```

---

## SBOM

```text
SBOM.md
sbom.cyclonedx.json
```

To generate a fully resolved local SBOM:

```bash
./scripts/generate_resolved_sbom.sh
```

---

## Known limitations

1. **Data recency** — Arctic Shift data may be 2–4 weeks behind real-time. Searches with a very recent `--from-date` may return fewer results than expected. The tool warns you when this is likely.
2. **Subreddit-scoped search** — Arctic Shift does not support Reddit-wide full text search. The discovery step mitigates this but cannot guarantee every relevant community is found.
3. **Community-run server** — Arctic Shift is maintained by one developer. If the server is unavailable, the tool will fail with a clear error message rather than silently.
4. **Semantic matching uses title and metadata only** — thread bodies and comments are intentionally not retrieved.
5. **The included SBOM is declared, not fully resolved** — run the local resolved SBOM script after install for a fully accurate dependency picture.
6. **The embedding model is pinned** — first-time download still depends on Hugging Face availability.
7. **This is not legal advice, compliance advice, or an API terms-of-service opinion.**

---

## Recommended human workflow

1. Run the tool.
2. Open the Reddit thread link.
3. Read the full thread manually.
4. Check the subreddit rules.
5. Decide whether a response is appropriate.
6. Respond as a human.
7. Disclose affiliation when relevant.
8. Do not paste AI-generated replies directly into Reddit.
9. Do not spam threads or communities.

---

## Quick checklist before use

```text
[ ] Create and activate a virtual environment
[ ] Install requirements.txt
[ ] Run unit tests
[ ] Run dependency audit locally
[ ] Generate requirements.lock.txt
[ ] Generate resolved SBOM
[ ] Use the tool only for human-reviewed thread discovery
```

---

## Code structure

```text
reddit_thread_finder.py                    thin CLI entrypoint
reddit_thread_finder_core/__init__.py
reddit_thread_finder_core/constants.py    hard limits, model pins, patterns, Arctic Shift URL
reddit_thread_finder_core/models.py       dataclasses, output schema, DiscoveredSubreddit
reddit_thread_finder_core/text_utils.py   small text helpers
reddit_thread_finder_core/validation.py   input parsing and limit enforcement
reddit_thread_finder_core/security.py     HTTP response validation, rate limit backoff
reddit_thread_finder_core/query.py        conservative query expansion
reddit_thread_finder_core/discovery.py    subreddit discovery and validation
reddit_thread_finder_core/reddit_search.py Arctic Shift HTTP candidate retrieval
reddit_thread_finder_core/scoring.py      semantic and heuristic scoring
reddit_thread_finder_core/output.py       terminal and JSON output validation
reddit_thread_finder_core/cli.py          argument parsing and orchestration
reddit_thread_finder_core/focus.py        pain point scope narrowing
```

---

## Local audit workflow

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests
./scripts/audit_dependencies.sh
./scripts/generate_lockfile.sh
./scripts/generate_resolved_sbom.sh
```

---

## Author

[Eyskiracing](https://github.com/Eyskiracing) — MIT License
