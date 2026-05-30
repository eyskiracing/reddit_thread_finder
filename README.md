# Reddit Thread Finder — Secure v6 Modular

Generated: 2026-05-29T19:24:35+00:00

A constrained, local Python CLI for finding Reddit thread links that are semantically relevant to a specific pain point.

The purpose is simple:

```text
Find Reddit threads that a human can open, read, and decide whether to respond to manually.
```

This tool is **not** designed to automate Reddit engagement, scrape Reddit content, build a Reddit dataset, or generate/post replies.

---



---

## Non-technical user quickstart

If you are not comfortable with Terminal, Python, virtual environments, or dependency tooling, start here:

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

The full README remains the technical reference. The quickstart is the step-by-step user guide.

## What this tool does

1. Accepts a natural-language pain point.
2. Asks for / accepts:
   - a start date
   - a minimum semantic match score from `0.0` to `1.0`
   - the number of thread links to return, capped at 100
   - optional subreddit targeting
3. Generates a small number of conservative Reddit search query variants.
4. Searches Reddit through the official Reddit API using PRAW.
5. Filters results from the requested start date to the current time.
6. Uses semantic matching against thread title and lightweight metadata only.
7. Returns Reddit thread links and lightweight metadata for human review.

---

## What this tool does not do

This tool intentionally does **not**:

- retrieve thread body / selftext
- retrieve comments
- retrieve or export Reddit usernames / authors
- generate Reddit replies
- post comments
- submit posts
- vote
- message users
- moderate communities
- use Reddit username/password credentials
- use OAuth refresh tokens
- build a Reddit content dataset
- train or fine-tune an AI model
- run continuous Reddit monitoring by default

The output is limited to metadata such as:

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

## Important local audit note

I did **not** run a real dependency audit inside this packaged download because that has to happen in your local virtual environment after installation.

Once you unzip the package locally, run:

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python -m unittest discover -s tests

./scripts/audit_dependencies.sh
./scripts/generate_lockfile.sh
./scripts/generate_resolved_sbom.sh
```

That will generate local, environment-specific files:

```text
requirements.lock.txt
sbom.resolved.cyclonedx.json
```

Those files are more accurate than the included declared SBOM because they reflect the exact package versions installed on your machine.

---

## Installation

### 1. Unzip the project

```bash
unzip reddit_thread_finder_secure_v4.zip
cd reddit_thread_finder_secure_v4
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

---

## Reddit API credentials

This tool runs locally from your Terminal and uses a local `.env` file.

Create your `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=reddit-thread-finder/0.1 by u/yourusername
```

On macOS / Linux, restrict file permissions:

```bash
chmod 600 .env
```

The script checks for overly broad `.env` permissions on Unix-like systems and warns you if the file may be readable or writable by other local users.

---

## Credential security rules

Do **not**:

- hard-code credentials in the Python file
- pass credentials as command-line arguments
- commit `.env` to Git
- paste credentials into ChatGPT, Slack, Google Docs, screenshots, or GitHub
- use Reddit username/password credentials for this tool
- add OAuth refresh tokens

The tool only needs:

```text
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT
```

It does **not** need:

```text
REDDIT_USERNAME
REDDIT_PASSWORD
REFRESH_TOKEN
```

The included `.gitignore` excludes:

```text
.env
.env.*
requirements.lock.txt
sbom.resolved.cyclonedx.json
*.json
*.log
```

---

## Read-only guardrail

The Reddit client is explicitly forced into read-only mode:

```python
reddit.read_only = True
```

The code does not include posting, commenting, voting, messaging, or moderation functions.

This is a technical guardrail to keep the project aligned with its purpose:

```text
Find links for human review.
Do not automate engagement.
```

---

## Abuse-prevention limits

The tool includes hard caps:

```text
MAX_TOP_K = 100
MAX_SUBREDDITS = 5
MAX_QUERY_VARIANTS = 8
MAX_CANDIDATE_LIMIT_PER_SEARCH = 100
MAX_SEARCH_OPERATIONS = 40
MAX_UNIQUE_CANDIDATES = 1000
```

It also uses conservative sort modes:

```text
relevance
new
```

And it includes small delays plus rate-limit backoff behavior.

---

## Rate-limit behavior

The script includes best-effort rate-limit detection for common `429`, `ratelimit`, and `too many requests` cases.

When a likely rate limit is detected, the tool:

1. waits before retrying
2. uses `Retry-After` if available
3. caps retries
4. fails safely instead of retrying aggressively

Even if Reddit allows more volume, the intended use is conservative, manual research.

---

## Dependency security hardening

The runtime dependencies are constrained in `requirements.txt`:

```text
praw>=7.7.1,<8.0.0
python-dotenv>=1.0.1,<2.0.0
sentence-transformers>=3.1.1,<4.0.0
```

The `sentence-transformers` minimum is intentionally set above the vulnerable `<3.1.0` range associated with unsafe model-loading risk.

Development and audit tooling is separated into `requirements-dev.txt`:

```text
pip-audit>=2.10.0,<3.0.0
cyclonedx-bom>=6.0.0,<8.0.0
```

---

## Model supply-chain hardening

The semantic model is pinned in code:

```python
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
```

The model loads with:

```python
trust_remote_code=False
```

This reduces model supply-chain drift and avoids executing remote custom model code.

The model may still need to be downloaded from Hugging Face the first time you run the tool unless it is already cached locally.

---

## SBOM

This package includes a declared SBOM:

```text
SBOM.md
sbom.cyclonedx.json
```

Important limitation:

```text
The included SBOM is a declared dependency SBOM, not a fully resolved lockfile SBOM.
```

That means it reflects the project’s declared dependencies and expected dependency families, but not the exact versions installed on your machine.

To generate a fully resolved local SBOM, run:

```bash
./scripts/generate_resolved_sbom.sh
```

This creates:

```text
requirements.lock.txt
sbom.resolved.cyclonedx.json
```

---

## Vulnerability audit

To audit installed dependencies locally, run:

```bash
./scripts/audit_dependencies.sh
```

This installs audit tooling from `requirements-dev.txt` and runs `pip-audit`.

Important limitation:

```text
pip-audit checks known Python package vulnerabilities.
It does not prove the application is secure.
It does not replace code review.
It does not fully assess OS-level libraries, model safety, Reddit API usage, or operational risk.
```

---

## Typical usage

Search all of Reddit:

```bash
python reddit_thread_finder.py \
  --topic "small businesses struggling with SOC 2 evidence collection" \
  --from-date 2026-01-01 \
  --min-score 0.70 \
  --top-k 25 \
  --subreddits "all" \
  --rank-by composite \
  --json-output results.json
```

Search targeted subreddits:

```bash
python reddit_thread_finder.py \
  --topic "manual SOC 2 evidence collection pain for startups" \
  --from-date 2026-01-01 \
  --min-score 0.68 \
  --top-k 50 \
  --subreddits "startups,cybersecurity,sysadmin,compliance"
```

---

## Scoring

The tool calculates:

```text
semantic_score
pain_score
engagement_score
recency_score
composite_score
```

The semantic score is based only on:

```text
thread title
subreddit name
flair, if available
```

It does **not** use:

```text
thread body
comments
author
user profile data
```

The composite score is intended to help find threads that may be useful for human review, not to decide whether or how to respond.

---

## Recommended human workflow

1. Run the tool.
2. Open the Reddit thread link.
3. Read the full thread manually.
4. Check the subreddit rules.
5. Decide whether a response is appropriate.
6. Respond as a human.
7. Disclose affiliation when relevant.
8. Do not paste AI-generated replies directly into Reddit without judgment.
9. Do not spam threads or communities.

The tool is meant to help find conversations, not automate participation in them.

---

## Compliance and Reddit API use

Use Reddit’s official API through PRAW.

Do not modify this tool to:

- scrape Reddit pages directly
- bypass Reddit limits
- continuously monitor Reddit at scale
- collect large datasets
- resell Reddit-derived intelligence
- train or fine-tune models on Reddit content
- automate posting or commenting

If you turn this into a commercial product, monitoring service, or high-volume research system, review Reddit’s API/data terms and get appropriate permission if needed.

---

## Files included

```text
reddit_thread_finder.py
README.md
SECURITY.md
SBOM.md
sbom.cyclonedx.json
requirements.txt
requirements-dev.txt
.env.example
.gitignore
scripts/audit_dependencies.sh
scripts/generate_lockfile.sh
scripts/generate_resolved_sbom.sh
tests/test_output_contract.py
```

---

## Known limitations

1. Semantic matching is less precise because the tool intentionally avoids thread bodies and comments.
2. Reddit search time filters are coarse, so the tool over-fetches and applies exact date filtering locally.
3. The included SBOM is declared, not fully resolved.
4. A real vulnerability audit must be run locally after install.
5. The embedding model is pinned, but first-time download still depends on Hugging Face availability and repository integrity.
6. The ML stack is larger than the rest of the tool and should be kept isolated in a virtual environment.
7. The tool finds candidate links; a human must verify relevance before responding.
8. This is not legal advice, compliance advice, or an API terms-of-service opinion.

---

## Quick checklist before use

```text
[ ] Create a dedicated Reddit API app
[ ] Copy .env.example to .env
[ ] Add only client ID, client secret, and user agent
[ ] Run chmod 600 .env on macOS/Linux
[ ] Create and activate a virtual environment
[ ] Install requirements.txt
[ ] Run unit tests
[ ] Run dependency audit locally
[ ] Generate requirements.lock.txt
[ ] Generate resolved SBOM
[ ] Use the tool only for human-reviewed thread discovery
```


---

## Code annotation status

The Python code is annotated with:

- a module-level purpose and non-goals docstring
- type hints on configuration, result objects, and function signatures
- docstrings for the main functions
- comments explaining the security and abuse-prevention guardrails
- explicit comments where the code intentionally avoids body/comment/author collection

The annotations are intended to make the code understandable to a technical user reviewing or modifying it locally.


---

## v6 modular code structure

Generated: 2026-05-29T20:48:27+00:00

v6 keeps the same requirements and guardrails, but splits the implementation into a small package:

```text
reddit_thread_finder.py                  thin CLI entrypoint
reddit_thread_finder_core/__init__.py
reddit_thread_finder_core/constants.py   hard limits, model pins, patterns
reddit_thread_finder_core/models.py      dataclasses and output schema
reddit_thread_finder_core/text_utils.py  small text helpers
reddit_thread_finder_core/validation.py  input parsing and limit enforcement
reddit_thread_finder_core/security.py    .env checks, read-only Reddit client, backoff
reddit_thread_finder_core/query.py       conservative query expansion
reddit_thread_finder_core/reddit_search.py bounded Reddit candidate retrieval
reddit_thread_finder_core/scoring.py     semantic and heuristic scoring
reddit_thread_finder_core/output.py      terminal and JSON output validation
reddit_thread_finder_core/cli.py         argument parsing and orchestration
```

Nothing has been removed from the requirements we discussed:

```text
read-only Reddit client
local .env credential handling
chmod 600 warning on Unix-like systems
no username/password requirement
no body/selftext retrieval
no comments retrieval
no author export
maximum 100 returned links
bounded subreddit/query/search/candidate limits
rate-limit/backoff handling
semantic score
pain score
engagement score
recency score
composite score
JSON output contract validation
pinned sentence-transformers model revision
trust_remote_code=False
SBOM and resolved SBOM workflow
pip-audit workflow
unit tests
```

Run the tool the same way:

```bash
python reddit_thread_finder.py \
  --topic "small businesses struggling with SOC 2 evidence collection" \
  --from-date 2026-01-01 \
  --min-score 0.70 \
  --top-k 25 \
  --subreddits "all" \
  --rank-by composite \
  --json-output results.json
```

Run tests:

```bash
python -m unittest discover -s tests
```


---

## v8 Pain Point Search Focus Builder

Generated: 2026-05-29T23:16:11+00:00

v8 adds a generic, product-agnostic scope-narrowing step before Reddit search.

The focus builder is designed to help users avoid broad searches like:

```text
AI automation platform
compliance evidence tool
customer support software
```

and guide them toward concrete pain-point searches like:

```text
support teams manually tagging customer tickets to find recurring product issues
small ecommerce operators tracking returns and refund status across Shopify warehouse emails and spreadsheets
clients asking service providers to turn security findings into evidence manually
```

Interactive users are asked:

```text
Who has this problem?
What are they trying to do?
What makes it painful today?
What outcome do they want instead?
Any words that must be included?
Any words or topics to avoid?
```

The tool then creates a search brief:

```text
target persona
task / situation
current friction
desired outcome
must-include terms
avoid terms
focused query
alternative queries
specificity score
specificity notes
```

Scripted users can also pass these fields directly:

```bash
python reddit_thread_finder.py \
  --topic "returns are killing our ecommerce team" \
  --persona "small ecommerce operators" \
  --task "track returns and refund status" \
  --friction "checking Shopify warehouse emails and spreadsheets manually" \
  --outcome "know which customers are waiting for refunds" \
  --must-include "Shopify,returns" \
  --avoid "dropshipping" \
  --from-date 2026-01-01 \
  --min-score 0.70 \
  --top-k 25 \
  --subreddits "all"
```

To bypass the interactive focus builder and use the topic directly:

```bash
python reddit_thread_finder.py \
  --topic "your focused search topic" \
  --skip-focus-builder
```

The focus builder is local and deterministic. It does not call an LLM or any external service.
