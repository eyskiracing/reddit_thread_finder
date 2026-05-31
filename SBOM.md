# Software Bill of Materials — Reddit Thread Finder (arctic-shift-backend branch)

## Branch context

This SBOM covers the `arctic-shift-backend` branch.

For the `main` branch SBOM (which uses `praw` and `python-dotenv`), see `main`.

---

## Dependency changes from main branch

| Change | Detail |
|---|---|
| Removed `praw>=7.7.1,<8.0.0` | Reddit official API client no longer used |
| Removed `python-dotenv>=1.0.1,<2.0.0` | No `.env` credential file in this branch |
| Added `requests>=2.31.0,<3.0.0` | HTTP client for Arctic Shift API calls |
| Added `reddit_thread_finder_core/discovery.py` | New subreddit discovery module |

---

## Project components

| Component | Type | Purpose |
|---|---|---|
| `reddit_thread_finder.py` | Application | Thin CLI entrypoint |
| `reddit_thread_finder_core/constants.py` | Application | Hard limits, model pins, Arctic Shift base URL |
| `reddit_thread_finder_core/models.py` | Application | Dataclasses, output schema, DiscoveredSubreddit |
| `reddit_thread_finder_core/text_utils.py` | Application | Text cleaning helpers |
| `reddit_thread_finder_core/validation.py` | Application | Input parsing and limit enforcement |
| `reddit_thread_finder_core/security.py` | Application | HTTP response validation, rate limit backoff |
| `reddit_thread_finder_core/query.py` | Application | Conservative query expansion |
| `reddit_thread_finder_core/discovery.py` | Application | Subreddit discovery and relevance validation |
| `reddit_thread_finder_core/reddit_search.py` | Application | Arctic Shift HTTP candidate retrieval |
| `reddit_thread_finder_core/scoring.py` | Application | Semantic and heuristic scoring |
| `reddit_thread_finder_core/output.py` | Application | Terminal and JSON output validation |
| `reddit_thread_finder_core/cli.py` | Application | Argument parsing and orchestration |
| `reddit_thread_finder_core/focus.py` | Application | Pain point scope narrowing |
| `tests/test_output_contract.py` | Test | Output contract, security, and dependency checks |
| `README.md` | Documentation | Technical usage and setup |
| `SECURITY.md` | Documentation | Security posture and third-party trust |
| `QUICKSTART_NON_TECHNICAL.md` | Documentation | Non-technical user guide |
| `SBOM.md` | Documentation | This file |
| `requirements.txt` | Dependency manifest | Runtime dependency constraints |
| `requirements-dev.txt` | Dependency manifest | Audit and SBOM tooling |
| `.gitignore` | Configuration | Prevents committing generated outputs |
| `scripts/audit_dependencies.sh` | Script | Runs pip-audit |
| `scripts/generate_lockfile.sh` | Script | Creates requirements.lock.txt |
| `scripts/generate_resolved_sbom.sh` | Script | Creates sbom.resolved.cyclonedx.json |

---

## Direct runtime Python dependencies

| Package | Constraint | Purpose |
|---|---|---|
| `requests` | `>=2.31.0,<3.0.0` | HTTP client for Arctic Shift API |
| `sentence-transformers` | `>=3.1.1,<4.0.0` | Semantic similarity scoring |

---

## Development / audit dependencies

| Package | Constraint | Purpose |
|---|---|---|
| `pip-audit` | `>=2.10.0,<3.0.0` | Vulnerability auditing |
| `cyclonedx-bom` | `>=6.0.0,<8.0.0` | Resolved CycloneDX SBOM generation |

---

## Important transitive dependency families

| Parent | Expected transitive dependencies |
|---|---|
| `requests` | `urllib3`, `certifi`, `charset-normalizer`, `idna` |
| `sentence-transformers` | `transformers`, `torch`, `huggingface-hub`, `scikit-learn`, `scipy`, `numpy`, `tqdm`, `Pillow` |

---

## Model dependency

| Model | Revision | Purpose |
|---|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | `c9745ed1d9f207416be6d2e6f8de32d1f16199bf` | Embedding model for semantic scoring |

---

## External services and network dependencies

| Service | Required? | Purpose |
|---|---|---|
| Arctic Shift API (`arctic-shift.photon-reddit.com`) | Yes | Reddit post search and subreddit discovery |
| Hugging Face Hub | First run only | Download pinned model if not cached |
| PyPI | Install-time only | Install Python packages |

Note: Arctic Shift is a community-run open source service, not an official Reddit service. See SECURITY.md for trust considerations.

---

## Runtime / OS dependencies

| Dependency | Required? | Notes |
|---|---|---|
| Python | Yes | 3.10+ recommended |
| pip | Yes | Package installation |
| venv | Strongly recommended | Dependency isolation |
| Terminal / shell | Yes | CLI execution |
| Internet access | Yes | Arctic Shift API calls and first-time model download |

---

## Data intentionally not handled or exported

- Reddit usernames / authors
- Reddit thread body / selftext
- Comments or comment bodies
- Generated replies
- Any user account credentials

---

## Known SBOM limitations

1. This is a declared SBOM. Run `./scripts/generate_resolved_sbom.sh` locally for a fully resolved version.
2. Runtime OS libraries selected by PyTorch/NumPy/SciPy wheels depend on your machine.
3. `pip-audit` checks known Python package vulnerabilities only; it is not a static code analyzer.
4. The model revision is pinned but first-time download requires trust in Hugging Face transport integrity.
