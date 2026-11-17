"""Verification helpers for comparing acquired bytes with recorded references."""

from __future__ import annotations

from pathlib import Path

from prooftrace.core.hashing import hash_file


def verify_file(path: str | Path, expected: dict[str, str]) -> dict[str, object]:
    """Recalculate digests and compare them to explicitly supplied references."""
    if not expected:
        raise ValueError("At least one expected digest is required.")

    actual = hash_file(path, expected.keys())
    comparisons = {
        algorithm: {
            "expected": expected[algorithm].lower(),
            "actual": actual[algorithm],
            "matches": actual[algorithm] == expected[algorithm].lower(),
        }
        for algorithm in expected
    }
    return {
        "path": str(Path(path)),
        "status": "match" if all(item["matches"] for item in comparisons.values()) else "mismatch",
        "digests": comparisons,
    }
