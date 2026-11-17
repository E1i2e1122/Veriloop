"""Helpers for joining user-supplied path segments onto trusted base directories."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException


def is_within(base: Path | str, candidate: Path | str) -> bool:
    """Return True when ``candidate`` resolves to ``base`` or a path inside it."""
    resolved_base = Path(base).resolve()
    resolved = Path(candidate).resolve()
    return resolved == resolved_base or resolved_base in resolved.parents


def safe_join(base: Path | str, *parts: str | Path) -> Path:
    """
    Join user-supplied segments onto ``base`` and refuse anything that escapes it.

    Blocks ``..`` traversal, absolute paths, and symlink escapes. Returns the joined
    path in the same (unresolved) form as ``base / part`` so callers' existing
    ``relative_to`` and string handling keeps working.

    Raises:
        HTTPException 400: if the joined path would leave ``base``.
    """
    joined = Path(base).joinpath(*(str(part) for part in parts))
    if not is_within(base, joined):
        raise HTTPException(status_code=400, detail="Invalid path")
    return joined
