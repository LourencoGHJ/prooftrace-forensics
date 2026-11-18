from __future__ import annotations

import hashlib
import mimetypes
import os
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ExifTags
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation


CHUNK_SIZE = 1024 * 1024
MAX_METADATA_ITEMS = 5000


def _hash_file(path: Path) -> dict[str, str]:
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()

    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            sha256.update(chunk)
            sha512.update(chunk)

    return {
        "sha256": sha256.hexdigest(),
        "sha512": sha512.hexdigest(),
    }


def _timestamp(value: float) -> str:
    return datetime.fromtimestamp(
        value, timezone.utc
    ).isoformat()


def _filesystem_metadata(path: Path) -> dict[str, Any]:
    stat = path.stat()

    result: dict[str, Any] = {
        "size_bytes": stat.st_size,
        "modified": _timestamp(stat.st_mtime),
        "accessed": _timestamp(stat.st_atime),
    }

    if os.name == "nt":
        result["created"] = _timestamp(stat.st_ctime)
        result["creation_time_semantics"] = "windows_creation_time"

        try:
            import ctypes
            from ctypes import wintypes

            class FILETIME(ctypes.Structure):
                _fields_ = [
                    ("dwLowDateTime", wintypes.DWORD),
                    ("dwHighDateTime", wintypes.DWORD),
                ]

            class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("dwFileAttributes", wintypes.DWORD),
                    ("ftCreationTime", FILETIME),
                    ("ftLastAccessTime", FILETIME),
                    ("ftLastWriteTime", FILETIME),
                    ("dwVolumeSerialNumber", wintypes.DWORD),
                    ("nFileSizeHigh", wintypes.DWORD),
                    ("nFileSizeLow", wintypes.DWORD),
                    ("nNumberOfLinks", wintypes.DWORD),
                    ("nFileIndexHigh", wintypes.DWORD),
                    ("nFileIndexLow", wintypes.DWORD),
                ]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

            create_file = kernel32.CreateFileW
            create_file.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.LPVOID,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.HANDLE,
            ]
            create_file.restype = wintypes.HANDLE

            get_info = kernel32.GetFileInformationByHandle
            get_info.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(BY_HANDLE_FILE_INFORMATION),
            ]
            get_info.restype = wintypes.BOOL

            close_handle = kernel32.CloseHandle
            close_handle.argtypes = [wintypes.HANDLE]
            close_handle.restype = wintypes.BOOL

            handle = create_file(
                str(path),
                0,
                0x00000001 | 0x00000002 | 0x00000004,
                None,
                3,
                0x02000000,
                None,
            )

            invalid_handle = ctypes.c_void_p(-1).value

            if handle in (None, invalid_handle):
                error_code = ctypes.get_last_error()
                raise OSError(error_code, "CreateFileW failed")

            try:
                info = BY_HANDLE_FILE_INFORMATION()

                if not get_info(handle, ctypes.byref(info)):
                    error_code = ctypes.get_last_error()
                    raise OSError(
                        error_code,
                        "GetFileInformationByHandle failed",
                    )

                result["windows_volume_serial"] = (
                    f"{info.dwVolumeSerialNumber:08X}"
                )
                result["windows_file_id"] = (
                    f"{info.nFileIndexHigh:08X}"
                    f"{info.nFileIndexLow:08X}"
                )

            finally:
                close_handle(handle)

        except (OSError, AttributeError, ValueError) as exc:
            result["windows_file_id_status"] = "UNAVAILABLE"
            result["windows_file_id_error"] = (
                f"{type(exc).__name__}: {exc}"
            )

    else:
        result["created"] = _timestamp(stat.st_ctime)
        result["creation_time_semantics"] = (
            "posix_metadata_change_time_not_creation_time"
        )

    return result


def _identify_format(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        header = file.read(32)

    ext = path.suffix.lower()

    declared_formats = {
        ".docx": "DOCX",
        ".xlsx": "XLSX",
        ".pptx": "PPTX",
        ".odt": "ODT",
        ".ods": "ODS",
        ".odp": "ODP",
        ".pdf": "PDF",
        ".png": "PNG",
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".tif": "TIFF",
        ".tiff": "TIFF",
        ".zip": "ZIP_BASED",
    }

    signatures = [
        (b"%PDF-", "PDF"),
        (b"\x89PNG\r\n\x1a\n", "PNG"),
        (b"\xff\xd8\xff", "JPEG"),
        (b"GIF87a", "GIF"),
        (b"GIF89a", "GIF"),
        (b"II*\x00", "TIFF"),
        (b"MM\x00*", "TIFF"),
        (b"BM", "BMP"),
        (b"\x7fELF", "ELF_EXECUTABLE"),
        (b"MZ", "WINDOWS_EXECUTABLE"),
        (b"ID3", "MP3"),
        (b"\xff\xfb", "MP3"),
        (b"\xff\xf3", "MP3"),
        (b"\xff\xf2", "MP3"),
        (b"fLaC", "FLAC"),
        (b"OggS", "OGG"),
        (b"RIFF", "RIFF_CONTAINER"),
    ]

    detected = next(
        (
            name
            for signature, name in signatures
            if header.startswith(signature)
        ),
        None,
    )

    validation = "SIGNATURE_MATCH" if detected else "NOT_IDENTIFIED"
    warnings: list[str] = []

    if header.startswith(b"PK"):
        detected = "ZIP_BASED"
        validation = "ZIP_STRUCTURE_NOT_CHECKED"

        try:
            with zipfile.ZipFile(path, "r") as archive:
                names = set(archive.namelist())

                validation = "VALID_ZIP_CONTAINER"

                office_requirements = {
                    "DOCX": {
                        "[Content_Types].xml",
                        "_rels/.rels",
                        "word/document.xml",
                    },
                    "XLSX": {
                        "[Content_Types].xml",
                        "_rels/.rels",
                        "xl/workbook.xml",
                    },
                    "PPTX": {
                        "[Content_Types].xml",
                        "_rels/.rels",
                        "ppt/presentation.xml",
                    },
                }

                odf_mime_types = {
                    "ODT": "application/vnd.oasis.opendocument.text",
                    "ODS": "application/vnd.oasis.opendocument.spreadsheet",
                    "ODP": "application/vnd.oasis.opendocument.presentation",
                }

                for office_kind, required in office_requirements.items():
                    if required.issubset(names):
                        detected = office_kind
                        validation = "VALID_OFFICE_STRUCTURE"
                        break

                if detected == "ZIP_BASED" and {
                    "mimetype", "content.xml", "META-INF/manifest.xml"
                }.issubset(names):
                    try:
                        mime_info = archive.getinfo("mimetype")

                        if mime_info.file_size <= 256:
                            mime_content = archive.read("mimetype").decode(
                                "ascii"
                            ).strip()

                            for odf_kind, expected_mime in odf_mime_types.items():
                                if mime_content == expected_mime:
                                    detected = odf_kind
                                    validation = "VALID_ODF_STRUCTURE"
                                    break
                    except (KeyError, UnicodeDecodeError, RuntimeError):
                        pass

        except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
            detected = "ZIP_INVALID"
            validation = "INVALID_ZIP_CONTAINER"
            warnings.append(
                f"ZIP structure validation failed: "
                f"{type(exc).__name__}: {exc}"
            )

    declared = declared_formats.get(ext)

    if declared and detected != declared:
        warnings.append(
            f"Extension/content mismatch: extension suggests "
            f"{declared}, detected content is {detected}."
        )

    if detected is None:
        detected = "UNKNOWN"

    mime_type = mimetypes.guess_type(path.name)[0] or (
        "application/octet-stream"
    )

    return {
        "extension": ext,
        "declared_format": declared or "UNKNOWN",
        "detected_format": detected,
        "mime_type": mime_type,
        "structural_validation": validation,
        "warnings": warnings,
    }


def _office_core_properties(path: Path, kind: str) -> dict[str, Any]:
    workbook = None

    try:
        if kind == "DOCX":
            document = Document(path)
            props = document.core_properties

        elif kind == "XLSX":
            workbook = load_workbook(
                path, read_only=True, data_only=False
            )
            props = workbook.properties

        elif kind == "PPTX":
            presentation = Presentation(path)
            props = presentation.core_properties

        else:
            return {}

        property_map = {
            "title": "title",
            "subject": "subject",
            "author": "author" if kind == "DOCX" else "creator",
            "keywords": "keywords",
            "comments": "comments",
            "last_modified_by": (
                "last_modified_by"
                if kind == "DOCX"
                else "lastModifiedBy"
            ),
            "category": "category",
            "identifier": "identifier",
            "language": "language",
            "created": "created",
            "modified": "modified",
            "revision": "revision",
            "version": "version",
        }

        result: dict[str, Any] = {}

        for output_name, source_name in property_map.items():
            try:
                value = getattr(props, source_name, None)

                if value is not None and value != "":
                    result[output_name] = (
                        value.isoformat()
                        if hasattr(value, "isoformat")
                        else str(value)
                    )

            except (AttributeError, TypeError, ValueError):
                continue

        return result

    finally:
        if workbook is not None:
            workbook.close()

def _image_metadata(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}

    with Image.open(path) as image:
        result["format"] = image.format
        result["width"] = image.width
        result["height"] = image.height
        result["mode"] = image.mode

        exif = image.getexif()
        tags = {}

        for tag_id, value in exif.items():
            name = ExifTags.TAGS.get(tag_id, str(tag_id))

            if isinstance(value, bytes):
                value = value.hex()

            if isinstance(value, (str, int, float)):
                tags[name] = value

        result["exif"] = tags

        if image.info:
            result["embedded_info_keys"] = sorted(
                str(key) for key in image.info.keys()
            )[:100]

    return result


def _zip_metadata(path: Path) -> dict[str, Any]:
    result = {
        "entries": [],
        "entry_count": 0,
        "total_uncompressed_bytes": 0,
        "warnings": [],
    }

    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()

        result["entry_count"] = len(infos)

        for info in infos[:MAX_METADATA_ITEMS]:
            result["entries"].append({
                "name": info.filename,
                "size_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "modified": info.date_time,
                "crc32": f"{info.CRC:08X}",
            })
            result["total_uncompressed_bytes"] += info.file_size

        if len(infos) > MAX_METADATA_ITEMS:
            result["warnings"].append(
                "Entry listing truncated at configured limit."
            )

    return result


def inspect_file(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError("The supplied path is not a regular file.")

    result: dict[str, Any] = {
        "file_name": path.name,
        "file_path": str(path),
        "analysis_time": datetime.now(timezone.utc).isoformat(),
        "filesystem": _filesystem_metadata(path),
        "hashes": _hash_file(path),
        "identification": _identify_format(path),
        "internal_metadata": {},
        "warnings": [],
        "assessment": "INDETERMINATE",
    }

    kind = result["identification"]["detected_format"]

    try:
        if kind in ("DOCX", "XLSX", "PPTX"):
            result["internal_metadata"] = (
                _office_core_properties(path, kind)
            )

        elif kind in ("JPEG", "PNG", "TIFF", "GIF", "BMP"):
            result["internal_metadata"] = _image_metadata(path)

        elif kind == "ZIP_BASED":
            result["internal_metadata"] = _zip_metadata(path)

        elif kind == "PDF":
            result["warnings"].append(
                "Use the dedicated PDF analyzer for revision and "
                "signature inspection."
            )

        else:
            result["warnings"].append(
                "No format-specific metadata analyzer is available."
            )

    except Exception as exc:
        result["warnings"].append(
            f"Metadata analysis incomplete: {type(exc).__name__}: {exc}"
        )

    result["warnings"].append(
        "Filesystem timestamps are not proof of original creation."
    )
    result["warnings"].append(
        "A single file inspection cannot establish a complete "
        "history of modifications."
    )

    return result
