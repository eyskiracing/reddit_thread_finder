"""Thin CLI entrypoint for Reddit Thread Finder Secure v6.

The implementation lives in the reddit_thread_finder_core package so the code is
easier to review and maintain.
"""

from reddit_thread_finder_core.cli import main


if __name__ == "__main__":
    main()
