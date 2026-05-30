"""Core package for Reddit Thread Finder Secure v6.

The package is intentionally modular:

- constants.py: safety limits and dependency pins
- models.py: dataclasses and output schema
- security.py: .env checks and Reddit client construction
- focus.py: generic pain-point search brief builder
- query.py: conservative query expansion
- reddit_search.py: bounded Reddit candidate retrieval
- scoring.py: semantic and heuristic scoring
- output.py: terminal/JSON output with schema enforcement
- cli.py: user input and command-line orchestration
"""
