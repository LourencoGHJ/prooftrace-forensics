import hashlib
import zipfile

from PIL import Image

from prooftrace.analyzers.universal import inspect_file


def test_inspect_text_file(tmp_path):
    path = tmp_path / "evidence.txt"
    content = b"ProofTrace test evidence"
    path.write_bytes(content)

    result = inspect_file(path)

    assert result["file_name"] == "evidence.txt"
    assert result["filesystem"]["size_bytes"] == len(content)
    assert result["hashes"]["sha256"] == hashlib.sha256(content).hexdigest()
    assert result["hashes"]["sha512"] == hashlib.sha512(content).hexdigest()
    assert result["assessment"] == "INDETERMINATE"


def test_identify_pdf_signature(tmp_path):
    path = tmp_path / "sample.pdf"
    path.write_bytes(b"%PDF-1.7\nProofTrace test")

    result = inspect_file(path)

    assert result["identification"]["detected_format"] == "PDF"
    assert any("dedicated PDF analyzer" in warning
               for warning in result["warnings"])


def test_inspect_png_metadata(tmp_path):
    path = tmp_path / "sample.png"
    Image.new("RGB", (20, 10), "white").save(path)

    result = inspect_file(path)

    assert result["identification"]["detected_format"] == "PNG"
    assert result["internal_metadata"]["width"] == 20
    assert result["internal_metadata"]["height"] == 10


def test_inspect_zip_entries(tmp_path):
    path = tmp_path / "evidence.zip"

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("document.txt", "Evidence content")

    result = inspect_file(path)

    assert result["identification"]["detected_format"] == "ZIP_BASED"
    assert result["internal_metadata"]["entry_count"] == 1
    assert result["internal_metadata"]["entries"][0]["name"] == "document.txt"


def test_missing_file_raises_error(tmp_path):
    path = tmp_path / "missing.txt"

    try:
        inspect_file(path)
    except FileNotFoundError:
        return

    raise AssertionError("Expected FileNotFoundError")


def test_analysis_does_not_modify_original(tmp_path):
    path = tmp_path / "original.txt"
    original = b"Original evidence"
    path.write_bytes(original)

    inspect_file(path)

    assert path.read_bytes() == original
from prooftrace.analyzers.universal import inspect_file


def test_windows_filesystem_metadata(tmp_path):
    import os
    import pytest

    if os.name != "nt":
        pytest.skip("Windows-specific filesystem test")

    path = tmp_path / "windows-evidence.txt"
    path.write_bytes(b"Windows filesystem evidence")

    result = inspect_file(path)
    metadata = result["filesystem"]

    assert metadata["creation_time_semantics"] == (
        "windows_creation_time"
    )

    assert "created" in metadata
    assert "modified" in metadata
    assert "accessed" in metadata

    if "windows_file_id" in metadata:
        assert len(metadata["windows_file_id"]) == 16
        assert len(metadata["windows_volume_serial"]) == 8
    else:
        assert metadata["windows_file_id_status"] == "UNAVAILABLE"


def _create_odf_archive(path, mimetype):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", mimetype)
        archive.writestr("content.xml", "<document/>")
        archive.writestr(
            "META-INF/manifest.xml",
            "<manifest/>"
        )


def test_identify_odt_format(tmp_path):
    from prooftrace.analyzers.universal import _identify_format

    path = tmp_path / "document.odt"
    _create_odf_archive(
        path,
        "application/vnd.oasis.opendocument.text"
    )

    result = _identify_format(path)

    assert result["detected_format"] == "ODT"
    assert result["structural_validation"] == "VALID_ODF_STRUCTURE"
    assert result["warnings"] == []


def test_identify_ods_format(tmp_path):
    from prooftrace.analyzers.universal import _identify_format

    path = tmp_path / "spreadsheet.ods"
    _create_odf_archive(
        path,
        "application/vnd.oasis.opendocument.spreadsheet"
    )

    result = _identify_format(path)

    assert result["detected_format"] == "ODS"
    assert result["structural_validation"] == "VALID_ODF_STRUCTURE"
    assert result["warnings"] == []


def test_identify_odp_format(tmp_path):
    from prooftrace.analyzers.universal import _identify_format

    path = tmp_path / "presentation.odp"
    _create_odf_archive(
        path,
        "application/vnd.oasis.opendocument.presentation"
    )

    result = _identify_format(path)

    assert result["detected_format"] == "ODP"
    assert result["structural_validation"] == "VALID_ODF_STRUCTURE"
    assert result["warnings"] == []


def test_odf_wrong_mimetype_is_not_misidentified(tmp_path):
    from prooftrace.analyzers.universal import _identify_format

    path = tmp_path / "document.odt"
    _create_odf_archive(
        path,
        "application/vnd.oasis.opendocument.spreadsheet"
    )

    result = _identify_format(path)

    assert result["detected_format"] == "ODS"
    assert result["structural_validation"] == "VALID_ODF_STRUCTURE"
    assert any("mismatch" in warning.lower()
               for warning in result["warnings"])


def test_generic_zip_with_content_xml_is_not_odf(tmp_path):
    from prooftrace.analyzers.universal import _identify_format

    path = tmp_path / "generic.zip"

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", "<document/>")
        archive.writestr("mimetype", "application/octet-stream")

    result = _identify_format(path)

    assert result["detected_format"] == "ZIP_BASED"
    assert result["structural_validation"] == "VALID_ZIP_CONTAINER"
