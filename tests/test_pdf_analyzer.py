from pathlib import Path

import pytest

pypdf = pytest.importorskip("pypdf")
from pypdf import PdfWriter

from prooftrace.analyzers.pdf import compare_pdf_versions, inspect_pdf


def make_pdf(path: Path, text: str) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    # Minimal PDFs are sufficient to exercise parser and digest reporting.
    writer.add_metadata({"/Title": text})
    with path.open("wb") as stream:
        writer.write(stream)


def test_inspect_pdf_reports_digest_and_structure(tmp_path):
    path = tmp_path / "sample.pdf"
    make_pdf(path, "Original")
    result = inspect_pdf(path)

    assert len(result["sha256"]) == 64
    assert result["page_count"] == 1
    assert result["metadata"]["/Title"] == "Original"
    assert result["signature_validation"] == "NOT_PERFORMED"


def test_compare_pdf_versions_reports_byte_and_metadata_changes(tmp_path):
    before = tmp_path / "before.pdf"
    after = tmp_path / "after.pdf"
    make_pdf(before, "Original")
    make_pdf(after, "Updated")

    result = compare_pdf_versions(before, after)

    assert result["same_bytes"] is False
    assert "/Title" in result["metadata_changes"]
