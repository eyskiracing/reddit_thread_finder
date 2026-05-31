# Security Notes

## Branch context

This is the `arctic-shift-backend` branch. It uses the Arctic Shift public API instead of the Reddit official API.

For the credential-based Reddit API version, see the `main` branch.

---

## Security changes in this branch vs main

### Removed

| Item | Reason |
|---|---|
| `.env` file and credential handling | No credentials needed — Arctic Shift requires no API key |
| `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` | Not used |
| `warn_if_env_file_permissions_are_loose()` | No credentials to protect at rest |
| `_warn_if_user_agent_format_invalid()` | No User-Agent requirement |
| `praw` dependency | Replaced by direct HTTP requests |
| `python-dotenv` dependency | No `.env` file to load |
| Read-only Reddit client enforced via `reddit.read_only = True` | No Reddit client exists; Arctic Shift is read-only by design |

### Added

| Item | Purpose |
|---|---|
| HTTP response validation | Validates structure, types, and field presence of all Arctic Shift API responses before they enter the pipeline |
| URL construction validation | Prevents user-supplied subreddit names and query strings from injecting unexpected parameters into HTTP requests |
| Third-party server trust disclosure | Documented below; users are informed of the dependency |
| `X-RateLimit-Remaining` header monitoring | Backs off when Arctic Shift rate limit is approaching |

### Carried forward unchanged

| Item | Notes |
|---|---|
| Rate limit backoff logic | Adapted from PRAW version; same pattern, different trigger |
| Output contract validation | JSON export still validates against allowed/disallowed field schema |
| Path traversal protection on `--json-output` | Unchanged |
| Semantic model pinned revision | Unchanged |
| `trust_remote_code=False` | Unchanged |
| Abuse-prevention caps | Unchanged; `MAX_SUBREDDITS` increased from 5 to 10 to support discovery results |

---

## Third-party server trust

This branch sends HTTP requests to:

```text
https://arctic-shift.photon-reddit.com
```

Arctic Shift is an independent open source project. It is not affiliated with Reddit.

**Risks to be aware of:**

**Availability** — Arctic Shift is maintained by one developer. If the server is unavailable, the tool fails with a clear error message rather than silently retrying forever.

**Data integrity** — The tool parses JSON from a third-party server it does not control. All responses are validated for structure and field types before use. If a response is malformed or contains unexpected fields, the tool raises a clear error rather than processing unknown data.

**No sensitive data is sent** — Requests contain only search query strings and subreddit names. No personal data, credentials, or user account information is transmitted.

**Mitigation summary:**

```text
- HTTP response validation on all API responses
- URL construction validation on all user inputs before request
- Rate limit header monitoring
- Clear error messages on server unavailability
- No credentials or personal data in requests
- Open source server code is publicly auditable
```

---

## No credentials

This branch has no credential attack surface.

There is no `.env` file, no API key, no client secret, and no OAuth token. The tool makes unauthenticated read-only HTTP requests to a public API.

This eliminates the most common real-world risk for tools like this: accidentally committing credentials to a public GitHub repository.

---

## Output safety

JSON output contains links and lightweight metadata only.

Disallowed output fields remain enforced:

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

The output contract validation fails closed — if an unexpected field appears, JSON export raises an error rather than silently writing it.

---

## HTTP request safety

All outbound HTTP requests:

- go only to `arctic-shift.photon-reddit.com`
- use HTTPS
- include a descriptive `User-Agent` header identifying the tool
- are read-only GET requests
- do not transmit personal data

---

## Rate-limit behavior

The tool monitors the `X-RateLimit-Remaining` header from Arctic Shift responses. When the remaining budget is low, the tool backs off before continuing. If a `429` response is received, the tool waits and retries with a cap on maximum retries.

Arctic Shift's rate limits are lenient for normal use. The tool's abuse-prevention caps on search operations and candidate limits provide an additional layer of protection against excessive requests.

---

## Dependency security

Runtime dependencies in this branch:

```text
requests>=2.31.0,<3.0.0
sentence-transformers>=3.1.1,<4.0.0
```

`praw` and `python-dotenv` are not present in this branch.

The `sentence-transformers` minimum blocks the vulnerable `<3.1.0` range.

Run a local audit after installation:

```bash
./scripts/audit_dependencies.sh
```

---

## Model supply-chain hardening

```python
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
trust_remote_code = False
```

---

## Code annotation

Security-sensitive logic lives in:

```text
reddit_thread_finder_core/security.py    HTTP validation, rate limit backoff
reddit_thread_finder_core/models.py      output schema contract
reddit_thread_finder_core/output.py      JSON export validation, path traversal protection
reddit_thread_finder_core/constants.py   Arctic Shift base URL, abuse-prevention limits
reddit_thread_finder_core/reddit_search.py HTTP request construction and response handling
reddit_thread_finder_core/discovery.py  subreddit discovery HTTP requests and validation
```

---

## What this tool does not do

This tool does not:

- post, comment, vote, message, or moderate on Reddit
- collect Reddit usernames, thread bodies, or comments
- store data beyond the current session
- send user data to any external service
- run background processes or scheduled jobs
- require or request any user account credentials
