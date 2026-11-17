"""Initial acquisition workflow.

This module does not claim write-blocked or immutable storage. It copies incoming bytes,
computes digests and verifies the preserved copy.
"""

from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from prooftrace.core.hashing import hash_file


@dataclass(frozen=True)
class AcquisitionRecord:
    evidence_id: str
    original_filename: str
    size_bytes: int
    acquired_at_utc: str
    collector: str
    source_description: str
    digests: dict[str, str]
    preserved_copy: str
    preserved_copy_verified: bool
    tool_name: str = "ProofTrace"
    tool_version: str = "0.1.0"
    schema: str = "prooftrace.evidence.v1"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def acquire_file(
    source: str | Path,
    evidence_directory: str | Path,
    *,
    collector: str,
    source_description: str,
) -> AcquisitionRecord:
    """Copy a file, hash source and preserved copy, then compare their digests."""
    source_path = Path(source)
    target_root = Path(evidence_directory)

    if not source_path.is_file():
        raise FileNotFoundError(f"Evidence source is not a regular file: {source_path}")
    if not collector.strip():
        raise ValueError("collector must not be empty.")
    if not source_description.strip():
        raise ValueError("source_description must not be empty.")

    target_root.mkdir(parents=True, exist_ok=True)
    evidence_id = f"PT-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:8].upper()}"
    target_path = target_root / f"{evidence_id}_{source_path.name}"

    shutil.copyfile(source_path, target_path)
    source_digests = hash_file(source_path)
    preserved_digests = hash_file(target_path)
    verified = source_digests == preserved_digests

    if not verified:
        target_path.unlink(missing_ok=True)
        raise RuntimeError("Preserved copy digest mismatch; acquisition was not recorded.")

    return AcquisitionRecord(
        evidence_id=evidence_id,
        original_filename=source_path.name,
        size_bytes=source_path.stat().st_size,
        acquired_at_utc=datetime.now(timezone.utc).isoformat(),
        collector=collector,
        source_description=source_description,
        digests=source_digests,
        preserved_copy=str(target_path),
        preserved_copy_verified=True,
    )
