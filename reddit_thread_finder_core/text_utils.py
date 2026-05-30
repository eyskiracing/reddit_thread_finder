"""Small text-processing helpers."""

from __future__ import annotations

import re


def clean_text(value: str) -> str:
    """Collapse whitespace and safely handle None-like text values."""
    return re.sub(r"\s+", " ", value or "").strip()
