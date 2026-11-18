"""Local web application for ProofTrace."""

from __future__ import annotations

import tempfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from prooftrace.analyzers.pdf import inspect_pdf, compare_pdf_versions
from prooftrace.analyzers.universal import inspect_file

MAX_FILE_SIZE = 50 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
STATIC_DIR = Path(__file__).parent / "static"

# Session-only activity. Nothing is written to disk.
_activity: deque[dict[str, str]] = deque(maxlen=10)
_inspections = 0
_comparisons = 0


def record_activity(operation: str, filename: str) -> None:
    global _inspections, _comparisons

    if operation in ("PDF inspection", "Evidence inspection"):
        _inspections += 1
    elif operation == "PDF comparison":
        _comparisons += 1

    _activity.appendleft({
        "operation": operation,
        "filename": filename,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


app = FastAPI(
    title="ProofTrace",
    version="0.2.0",
    description="Local-first digital document inspection.",
    docs_url="/docs",
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "application": "ProofTrace"}


@app.get("/api/dashboard")
async def dashboard_data() -> dict[str, Any]:
    return {
        "status": "online",
        "storage": "session-only",
        "total_operations": _inspections + _comparisons,
        "inspections": _inspections,
        "comparisons": _comparisons,
        "recent_activity": list(_activity),
    }


async def save_upload(upload: UploadFile, destination: Path) -> None:
    """Save an upload to temporary storage with a strict size limit."""
    total = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break

                total += len(chunk)
                if total > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds the 50 MB upload limit.",
                    )

                output.write(chunk)
    finally:
        await upload.close()

    if total == 0:
        raise HTTPException(status_code=400, detail="Empty file.")



@app.post("/api/evidence/inspect")
async def evidence_inspect(file: UploadFile = File(...)) -> dict[str, Any]:
    """Inspect supported evidence formats without modifying the original."""
    original_name = Path(file.filename or "evidence.bin").name
    suffix = Path(original_name).suffix[:20]

    with tempfile.TemporaryDirectory(prefix="prooftrace-") as temp_dir:
        path = Path(temp_dir) / f"evidence{suffix}"
        await save_upload(file, path)

        try:
            result = inspect_file(path)

            if result["identification"]["detected_format"] == "PDF":
                try:
                    result["pdf_analysis"] = inspect_pdf(path)
                except Exception as exc:
                    result["pdf_analysis_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )

            # Do not expose the server's temporary filesystem path.
            result.pop("file_path", None)

            # These timestamps describe the server-side uploaded copy,
            # not the original file's filesystem history.
            result["filesystem"]["timestamp_scope"] = (
                "temporary_server_upload_copy"
            )

            result["file_name"] = original_name
            record_activity("Evidence inspection", original_name)
            return result

        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail="The evidence file could not be inspected.",
            ) from exc
@app.post("/api/pdf/inspect")
async def pdf_inspect(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = Path(file.filename or "document.pdf").name

    with tempfile.TemporaryDirectory(prefix="prooftrace-") as temp_dir:
        path = Path(temp_dir) / "evidence.pdf"
        await save_upload(file, path)

        try:
            result = inspect_pdf(path)
            record_activity("PDF inspection", filename)
            return result
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail="The PDF could not be inspected.",
            ) from exc


@app.post("/api/pdf/compare")
async def pdf_compare(
    first: UploadFile = File(...),
    second: UploadFile = File(...),
) -> dict[str, Any]:
    first_name = Path(first.filename or "original.pdf").name
    second_name = Path(second.filename or "modified.pdf").name

    with tempfile.TemporaryDirectory(prefix="prooftrace-") as temp_dir:
        root = Path(temp_dir)
        first_path = root / "before.pdf"
        second_path = root / "after.pdf"

        await save_upload(first, first_path)
        await save_upload(second, second_path)

        try:
            result = compare_pdf_versions(first_path, second_path)
            record_activity("PDF comparison", f"{first_name} ↔ {second_name}")
            return result
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail="The PDF versions could not be compared.",
            ) from exc
