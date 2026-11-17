from __future__ import annotations

import hashlib

import pytest

from prooftrace.core.hashing import hash_file


def test_hash_file_matches_hashlib(tmp_path):
    content = b"ProofTrace evidence fixture\x00\x01"
    path = tmp_path / "fixture.bin"
    path.write_bytes(content)

    result = hash_file(path)

    assert result["sha256"] == hashlib.sha256(content).hexdigest()
    assert result["sha512"] == hashlib.sha512(content).hexdigest()


def test_hash_file_empty_file(tmp_path):
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")

    assert hash_file(path) == {
        "sha256": hashlib.sha256(b"").hexdigest(),
        "sha512": hashlib.sha512(b"").hexdigest(),
    }


def test_rejects_unsupported_algorithm(tmp_path):
    path = tmp_path / "fixture.bin"
    path.write_bytes(b"data")

    with pytest.raises(ValueError, match="Unsupported algorithm"):
        hash_file(path, ["md5"])


def test_rejects_invalid_chunk_size(tmp_path):
    path = tmp_path / "fixture.bin"
    path.write_bytes(b"data")

    with pytest.raises(ValueError, match="chunk_size"):
        hash_file(path, chunk_size=0)
