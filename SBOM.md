# Software Bill of Materials — Reddit Thread Finder Secure v3

Generated: 2026-05-29T19:22:07+00:00

## Scope

This SBOM covers `reddit_thread_finder_secure_v3`.

This is a declared dependency SBOM based on the project files and `requirements.txt`. A fully resolved SBOM should be generated locally after installation using:

```bash
./scripts/generate_resolved_sbom.sh
```

## v3 hardening changes

| Area | Change |
|---|---|
| `sentence-transformers` | Raised to `>=3.1.1,<4.0.0` to block the known vulnerable `<3.1.0` range |
| Model supply chain | Pinned `sentence-transformers/all-MiniLM-L6-v2` to revision `c9745ed1d9f207416be6d2e6f8de32d1f16199bf` |
| Model execution | Loads model with `trust_remote_code=False` |
| Dependency drift | Added upper bounds on direct runtime dependencies |
| Audit workflow | Added `requirements-dev.txt` and scripts for `pip-audit`, lockfile generation, and resolved SBOM generation |
| Tests | Added tests to enforce model revision and dependency constraints |

## Project components

| Component | Type | Version / Constraint | Purpose |
|---|---:|---:|---|
| `reddit_thread_finder.py` | Application code | local | CLI script for Reddit thread link discovery |
| `tests/test_output_contract.py` | Test code | local | Ensures output contract, abuse-prevention limits, and dependency controls remain in place |
| `README.md` | Documentation | local | Usage and setup documentation |
| `SECURITY.md` | Documentation | local | Credential and security guidance |
| `requirements.txt` | Dependency manifest | local | Runtime dependency constraints |
| `requirements-dev.txt` | Dependency manifest | local | Audit/SBOM tooling dependencies |
| `.env.example` | Configuration template | local | Template for Reddit API credentials |
| `.gitignore` | Configuration | local | Prevents committing secrets and generated outputs |
| `scripts/audit_dependencies.sh` | Script | local | Runs `pip-audit` |
| `scripts/generate_lockfile.sh` | Script | local | Creates `requirements.lock.txt` |
| `scripts/generate_resolved_sbom.sh` | Script | local | Creates `requirements.lock.txt` and `sbom.resolved.cyclonedx.json` |

## Direct runtime Python dependencies

| Package | Declared constraint | Purpose |
|---|---:|---|
| `praw` | `>=7.7.1,<8.0.0` | Reddit API client |
| `python-dotenv` | `>=1.0.1,<2.0.0` | Loads local `.env` credentials |
| `sentence-transformers` | `>=3.1.1,<4.0.0` | Semantic similarity scoring |

## Development / audit dependencies

| Package | Declared constraint | Purpose |
|---|---:|---|
| `pip-audit` | `>=2.10.0,<3.0.0` | Vulnerability auditing of Python dependencies |
| `cyclonedx-bom` | `>=6.0.0,<8.0.0` | Resolved CycloneDX SBOM generation |

## Important transitive dependency families

| Parent package | Expected transitive dependencies / families |
|---|---|
| `praw` | `prawcore`, `update_checker`, `websocket-client`, HTTP stack dependencies |
| `sentence-transformers` | `transformers`, `torch`, `huggingface-hub`, `scikit-learn`, `scipy`, `numpy`, `tqdm`, `Pillow`, packaging utilities |

## Model dependency

| Model | Revision | Purpose |
|---|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | `c9745ed1d9f207416be6d2e6f8de32d1f16199bf` | Embedding model for semantic scoring |

## Runtime / OS dependencies

| Dependency | Required? | Notes |
|---|---:|---|
| Python | Yes | Python 3.10+ recommended |
| pip | Yes | Used to install dependencies |
| venv / virtualenv | Strongly recommended | Keeps dependencies isolated |
| Terminal / shell | Yes | Local CLI execution |
| OS | macOS, Linux, or Windows | `.env` permission warning applies to Unix-like systems |
| Internet access | Yes | Required for Reddit API calls and first-time package/model downloads |
| Reddit API credentials | Yes | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` |
| Hugging Face model cache | Yes, first run | Model is downloaded and cached locally unless already present |

## External services and network dependencies

| Service | Required? | Purpose |
|---|---:|---|
| Reddit API | Yes | Read-only Reddit search and metadata retrieval |
| Hugging Face Hub | Usually yes on first run | Download pinned model revision if not cached |
| PyPI | Install-time only | Install Python packages |

## Data intentionally not handled/exported

The application intentionally does not export or store:

- Reddit usernames / authors
- Reddit thread body / selftext
- comments
- comment bodies
- generated replies
- Reddit account username/password
- OAuth refresh tokens

## Known limitations

1. This is still a declared SBOM until you run the local resolved SBOM script.
2. Runtime OS libraries selected by PyTorch/NumPy/SciPy wheels depend on your machine.
3. `pip-audit` checks known Python package vulnerabilities; it is not a static code analyzer and does not guarantee detection of malicious packages.
4. The model revision is pinned, but first-time model download still requires trust in Hugging Face transport and repository integrity.


---

## v6 modularization update

Generated: 2026-05-29T20:48:27+00:00

The application component is now organized as a local Python package:

```text
reddit_thread_finder_core
```

This does not add third-party dependencies. It only changes internal source-file organization.

New local application components:

```text
reddit_thread_finder.py
reddit_thread_finder_core/constants.py
reddit_thread_finder_core/models.py
reddit_thread_finder_core/text_utils.py
reddit_thread_finder_core/validation.py
reddit_thread_finder_core/security.py
reddit_thread_finder_core/query.py
reddit_thread_finder_core/reddit_search.py
reddit_thread_finder_core/scoring.py
reddit_thread_finder_core/output.py
reddit_thread_finder_core/cli.py
```


---

## v7 usability update

Generated: 2026-05-29T20:52:39+00:00

v7 adds non-technical user documentation and local helper scripts:

```text
QUICKSTART_NON_TECHNICAL.md
setup_mac.command
run_mac.command
setup_windows.bat
run_windows.bat
```

These are local project files and do not add third-party dependencies.


---

## v8 focus builder update

Generated: 2026-05-29T23:16:11+00:00

v8 adds one local source file:

```text
reddit_thread_finder_core/focus.py
```

This is local deterministic code for product-agnostic pain-point scope narrowing.
It does not add third-party dependencies or external services.
