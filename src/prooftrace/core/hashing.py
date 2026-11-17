"""Streaming cryptographic digests for evidence files.

Digests identify exact byte sequences. They do not contain file history or prove
when a document was originally created.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

CHUNK_SIZE = 1024 * 1024
SUPPORTED_ALGORITHMS = ("sha256", "sha512")


def hash_file(
    path: str | Path,
    algorithms: Iterable[str] = ("sha256", "sha512"),
    *,
    chunk_size: int = CHUNK_SIZE,
) -> dict[str, str]:
    """Calculate one or more hashes without loading the complete file into memory."""
    file_path = Path(path)
    selected = tuple(dict.fromkeys(name.lower() for name in algorithms))

    if not selected:
        raise ValueError("At least one hashing algorithm must be selected.")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    hashers = {}
    for name in selected:
        if name not in SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {name}")
        hashers[name] = hashlib.new(name)

    with file_path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            for hasher in hashers.values():
                hasher.update(chunk)

    return {name: hasher.hexdigest() for name, hasher in hashers.items()}
