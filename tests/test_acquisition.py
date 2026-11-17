from pathlib import Path

import pytest

from prooftrace.core.acquisition import acquire_file


def test_acquisition_copies_and_verifies_file(tmp_path):
    source = tmp_path / "report.txt"
    source.write_text("Synthetic test evidence", encoding="utf-8")
    evidence_dir = tmp_path / "evidence"

    record = acquire_file(
        source,
        evidence_dir,
        collector="test-examiner",
        source_description="Synthetic fixture created for automated testing",
    )

    preserved = Path(record.preserved_copy)
    assert preserved.read_bytes() == source.read_bytes()
    assert record.preserved_copy_verified is True
    assert record.digests["sha256"]
    assert record.digests["sha512"]
    assert record.evidence_id.startswith("PT-")


def test_acquisition_rejects_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        acquire_file(
            tmp_path / "missing.pdf",
            tmp_path / "evidence",
            collector="examiner",
            source_description="test",
        )
