# Security Notes

This tool is designed to run locally from your Terminal and use Reddit API credentials safely.

## Credential handling

Use a local `.env` file or environment variables.

Do **not**:
- hard-code credentials in Python files
- pass credentials as command-line arguments
- commit `.env` to Git
- paste credentials into shared docs, prompts, screenshots, or logs
- use a Reddit username/password for this read-only tool

The tool only needs:

```bash
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
```

It does **not** need:

```bash
REDDIT_USERNAME=
REDDIT_PASSWORD=
```

## Recommended local setup

Create `.env` from the example:

```bash
cp .env.example .env
```

Set restrictive file permissions on macOS/Linux:

```bash
chmod 600 .env
```

The `.gitignore` file prevents `.env` and common secret files from being committed.

## Least privilege

Create a dedicated Reddit API app for this tool.

Use it only for read-only search. This code does not contain posting, commenting, voting, messaging, or moderation functions.

## Output safety

JSON output contains links and lightweight metadata only. It does not include Reddit thread bodies or comments.


## v2 hardening

The v2 version adds several additional controls:

### Forced read-only mode

The Reddit client is explicitly set to:

```python
reddit.read_only = True
```

This reinforces that the script is only for discovering links and cannot drift into posting, commenting, voting, or messaging behavior without deliberate code changes.

### Rate-limit backoff

The script detects common 429 / rate-limit cases and waits before retrying. Retries are capped so the script does not aggressively hammer the API.

### Output contract

Before writing JSON, the script validates that output fields are limited to safe metadata fields only.

Disallowed fields include:

```text
author
username
body
selftext
comments
comment_body
content
text_preview
```

### Tests

The included tests check that:
- `MAX_TOP_K` remains 100
- query expansion remains capped
- allowed sort modes remain conservative
- exported result fields exclude body, author, and comments


## v3 dependency hardening

The v3 package addresses the SBOM concerns identified in review:

### `sentence-transformers` vulnerable range blocked

`requirements.txt` now requires:

```text
sentence-transformers>=3.1.1,<4.0.0
```

This blocks the vulnerable `<3.1.0` range associated with unsafe PyTorch model loading.

### Model revision pinned

The semantic model is pinned to a specific Hugging Face repository SHA:

```text
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
```

The code also passes:

```python
trust_remote_code=False
```

when loading the model.

### Local audit workflow added

The package includes:

```text
requirements-dev.txt
scripts/audit_dependencies.sh
scripts/generate_lockfile.sh
scripts/generate_resolved_sbom.sh
```

Use these from a clean virtual environment to create a pinned local lockfile, run `pip-audit`, and generate a fully resolved CycloneDX SBOM.


## README alignment

The README has been expanded to include all major operational and security caveats discussed during project design, including:

- local audit limitations
- credential handling
- `.env` file security
- read-only mode
- abuse-prevention limits
- rate-limit behavior
- SBOM limitations
- vulnerability audit workflow
- model revision pinning
- human response guardrails
- Reddit API usage boundaries

The README should be treated as the primary user-facing operating guide.


## Code annotation

The main script now includes module-level and function-level documentation explaining:

- the purpose and non-goals of the tool
- why Reddit is used in read-only mode
- why thread bodies and comments are not retrieved
- why output schema validation fails closed
- why candidate/search/result limits exist
- how semantic and composite scoring are used


## v6 modularization

The v6 package keeps the same security posture but separates the code into focused modules.

Security-sensitive logic is easier to review because it lives in predictable places:

```text
reddit_thread_finder_core/security.py
reddit_thread_finder_core/models.py
reddit_thread_finder_core/output.py
reddit_thread_finder_core/constants.py
reddit_thread_finder_core/reddit_search.py
```

The root `reddit_thread_finder.py` file is now only a thin entrypoint.


## Non-technical quickstart and launchers

v7 adds a user-facing quickstart and simple setup/run scripts:

```text
QUICKSTART_NON_TECHNICAL.md
setup_mac.command
run_mac.command
setup_windows.bat
run_windows.bat
```

These scripts do not add new capabilities. They only make the same local setup and run workflow easier for non-technical users.


## v8 focus builder

The v8 focus builder does not add external services or LLM calls.

It is a local, deterministic prompt-and-rewrite workflow that helps users provide
more specific pain-point search criteria. It remains product-agnostic and does
not assume any compliance, security, or GRC use case.
