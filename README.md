<div align="center">

# ProofTrace

**Digital Evidence & Document Forensics**

A local-first toolkit for acquiring, preserving, examining and verifying digital documents.

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-early%20development-orange?style=flat-square)]()
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

</div>

ProofTrace is an independent digital forensics project focused on **document integrity, provenance, revision analysis and evidence handling**. It helps an examiner understand what can be verified about a file, which differences can be identified, and where evidence is insufficient.

> ProofTrace reports technical observations; it does not certify documents, identify an editor, establish intent, or guarantee legal admissibility.

## Current features

- Streaming SHA-256 and SHA-512 hashing.
- File acquisition into a separate evidence directory, with digest verification of the preserved copy.
- Reference digest verification with explicit MATCH / MISMATCH results.
- Initial PDF inspection: metadata, page count, text extraction, signature-field presence and lexical revision markers.
- PDF-to-PDF comparison: byte digests, page text and metadata differences.
- JSON output for acquisition and analysis records.

## Quick start

Requirements: Python 3.12+.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## CLI examples

```powershell
# Calculate SHA-256 and SHA-512
prooftrace hash ".\sample.pdf"

# Acquire and preserve a received file
prooftrace acquire ".\sample.pdf" --collector "Examiner" --source "Authorized test submission"

# Verify against a known SHA-256 reference
prooftrace verify ".\sample.pdf" --sha256 "<expected-sha256>"

# Inspect a PDF
prooftrace pdf-inspect ".\sample.pdf" --output ".\pdf-report.json"

# Compare two PDF versions
prooftrace pdf-compare ".\before.pdf" ".\after.pdf" --output ".\comparison.json"

# Run automated tests
python -m pytest
```

## Important forensic distinctions

A hash identifies exact bytes at the time they are hashed. It does not contain earlier hashes or reveal the document's first-ever creation time. A hash calculated today is an **acquisition digest**, not proof of an original digest.

PDF EOF markers can indicate possible incremental-save boundaries, but lexical markers alone do not prove valid revisions. Signature fields can be detected separately from cryptographic signature validation. Metadata timestamps are not trusted timestamps.

## Planned development

1. Robust PDF revision parsing and digital signature validation.
2. Evidence manifests, chain-of-custody events and protected audit records.
3. DOCX analysis (tracked changes, comments, document properties and package structure).
4. Image analysis (EXIF/XMP, metadata and visual comparison).
5. RFC 3161 trusted timestamp integration and C2PA provenance validation.
6. Forensic report generation and a desktop interface.

## Preservation and limitations

Never analyze by modifying the acquired original. Keep the received file, preserved copy, working copy and generated reports distinct. Use synthetic or explicitly authorized evidence during development. Do not upload sensitive evidence to public repositories or third-party services.

The current PDF analyzer is an initial triage component, not a complete forensic parser. It does not yet validate signatures, prove revision authenticity, recover deleted content or guarantee detection of all modifications.

## Research references

- [NISTIR 8387 — Digital Evidence Preservation](https://doi.org/10.6028/NIST.IR.8387)
- [SWGDE — Best Practices for Computer Forensic Acquisitions](https://www.swgde.org/documents/published-complete-listing/17-f-002-best-practices-for-computer-forensic-acquisitions/)
- [IETF RFC 3161 — Time-Stamp Protocol](https://www.rfc-editor.org/rfc/rfc3161)
- [C2PA Technical Specifications](https://spec.c2pa.org/)

---

**Built as an independent digital forensics and cybersecurity project.**
