
from pathlib import Path

import pytest
from pypdf import PdfWriter

from prooftrace.analyzers.pdf_revisions import (
    PDFRevisionError,
    find_startxref,
    inspect_revision_chain,
)


def make_pdf(path: Path, title: str = "Original") -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.add_metadata({"/Title": title})

    with path.open("wb") as stream:
        writer.write(stream)


def make_incremental_pdf(original: Path, updated: Path) -> None:
    writer = PdfWriter(original, incremental=True)
    writer.add_metadata({"/Title": "Updated"})

    with updated.open("wb") as stream:
        writer.write(stream)


def test_find_terminal_startxref(tmp_path):
    path = tmp_path / "sample.pdf"
    make_pdf(path)

    data = path.read_bytes()
    offset = find_startxref(data)

    assert 0 <= offset < len(data)
    assert data[offset:offset + 4] == b"xref" or data[offset:offset + 1].isdigit()


def test_inspect_single_revision_pdf(tmp_path):
    path = tmp_path / "single.pdf"
    make_pdf(path)

    result = inspect_revision_chain(path.read_bytes())

    assert result["revision_count"] == 1
    assert result["status"] == "INDETERMINATE"
    assert len(result["warnings"]) > 0
    assert result["revisions"][0]["previous_xref"] is None


def test_inspect_incremental_revision_chain(tmp_path):
    original = tmp_path / "original.pdf"
    updated = tmp_path / "updated.pdf"

    make_pdf(original)
    make_incremental_pdf(original, updated)

    result = inspect_revision_chain(updated.read_bytes())

    assert result["revision_count"] == 2
    assert result["revisions"][0]["previous_xref"] is not None
    assert result["revisions"][1]["type"] == "TABLE"


def test_reject_terminal_startxref_outside_file():
    data = b"%PDF-1.7\nstartxref\n9999\n%%EOF\n"

    with pytest.raises(PDFRevisionError):
        inspect_revision_chain(data)


def test_reject_missing_terminal_startxref():
    data = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF"

    with pytest.raises(PDFRevisionError):
        find_startxref(data)


def test_reject_revision_chain_cycle():
    data = (
        b"%PDF-1.7\n"
        b"xref\n"
        b"0 1\n"
        b"0000000000 65535 f \n"
        b"trailer\n"
        b"<< /Size 1 /Prev 9 >>\n"
        b"startxref\n"
        b"9\n"
        b"%%EOF\n"
    )

    with pytest.raises(PDFRevisionError):
        inspect_revision_chain(data)
