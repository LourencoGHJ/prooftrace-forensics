<div align="center">

# ProofTrace

**Digital Evidence & Document Forensics**

A local-first forensic toolkit for acquiring, preserving, examining and verifying digital documents.

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-early%20development-orange?style=flat-square)]()
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

</div>

ProofTrace is an independent, educational digital forensics project focused on **document integrity, provenance, revision analysis and evidence handling**. It aims to help an examiner determine what can be verified about a file, what changes can be identified, and where available evidence is insufficient.

> **Important:** ProofTrace does not certify documents, establish the truth of their contents, identify the person who made an edit, or guarantee court admissibility. It reports technical observations, verification results and limitations. Legal acceptance depends on jurisdiction, collection authority, examiner competence, validated methods and case context.

## Core principles

- **Preserve before examining:** retain the received bytes unchanged and perform analysis on a working copy.
- **Hash at acquisition:** calculate cryptographic digests when the file enters the documented evidence workflow.
- **Never invent history:** a file's first-ever hash cannot be recovered unless it was previously recorded by a trusted process.
- **Separate fact from inference:** metadata, timestamps and embedded revision data have different evidential strength.
- **Make work reproducible:** record tools, versions, parameters, timestamps, errors and examiner actions.
- **Protect evidence records:** use signed manifests, independently verifiable timestamps and append-only audit records where configured.
- **Be format-aware:** PDF, DOCX and image formats preserve different kinds of information and have different limitations.

## Planned capabilities

| Module | Purpose | Status |
|---|---|---|
| Evidence acquisition | Record source, context, custody and acquisition time | Planned |
| Hash engine | SHA-256 / SHA-512 digests and independent re-verification | Initial implementation |
| Evidence manifest | Machine-readable acquisition record | Planned |
| PDF examination | Metadata, signatures, incremental revisions and structure | Planned |
| DOCX examination | ZIP/XML structure, properties, comments and tracked changes | Planned |
| Image examination | EXIF/XMP metadata, pixel comparison and provenance | Planned |
| Signature validation | Validate supported digital signatures and certificate chains | Planned |
| Trusted timestamps | RFC 3161 timestamp tokens for manifests | Planned |
| Comparison engine | Byte, text, structure and visual comparisons | Planned |
| Reporting | Findings, methods, hashes and limitations | Planned |

## Hash vs. document history

A SHA-256 digest identifies the exact bytes hashed at a particular point in the workflow. If a file changes, its digest will normally change. The digest does **not** contain earlier digests, previous file content, author identity, edit history or creation time.

ProofTrace therefore distinguishes:

1. **Acquisition digest:** calculated when ProofTrace receives the file.
2. **Reference digest:** supplied by a trusted earlier record, if one exists.
3. **Embedded history:** revisions or metadata recoverable from the file format.
4. **External provenance:** signed manifests, trusted timestamps or records from other systems.
5. **Comparison evidence:** differences between explicitly identified versions.

Without a trusted prior reference or surviving provenance artefact, ProofTrace cannot establish that the received file is the first/original version.

## Evidence workflow

1. Record evidence ID, source, collector, date/time and acquisition context.
2. Preserve the received file and calculate SHA-256 (optionally SHA-512).
3. Store a protected original and analyze a separate working copy.
4. Examine format structure, metadata, signatures, embedded revisions and content.
5. Compare with any known reference versions.
6. Recalculate the preserved original's digest to verify it has not changed during handling.
7. Export a report and evidence manifest, including limitations and tool versions.

## Project structure

```text
prooftrace-forensics/
├── docs/                  # Methodology, architecture and evidence model
├── src/prooftrace/
│   ├── core/              # Hashing, acquisition and verification
│   ├── analyzers/         # PDF, DOCX and image examination
│   ├── evidence/          # Manifest, ledger and chain of custody
│   └── reporting/         # Forensic reports
└── tests/                 # Automated and fixture-based tests
```

## Development

Requirements: Python 3.12 or newer.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

The first milestone is a tested hashing and acquisition core. Format-specific analyzers will be added only after the evidence model and preservation workflow are established.

## Safety and privacy

ProofTrace is designed for local analysis. Evidence files should not be uploaded to public repositories, issue trackers or third-party services. Use synthetic or explicitly authorized test material when developing and validating analyzers. Never modify the acquired original.

## Research references

- [NISTIR 8387 — Digital Evidence Preservation: Considerations for Evidence Handlers](https://doi.org/10.6028/NIST.IR.8387)
- [SWGDE — Best Practices for Computer Forensic Acquisitions](https://www.swgde.org/documents/published-complete-listing/17-f-002-best-practices-for-computer-forensic-acquisitions/)
- [SWGDE — Best Practices for Computer Forensic Examinations](https://www.swgde.org/documents/published-complete-listing/18-f-001-2/)
- [IETF RFC 3161 — Internet X.509 Public Key Infrastructure Time-Stamp Protocol](https://www.rfc-editor.org/rfc/rfc3161)
- [C2PA Technical Specifications](https://spec.c2pa.org/)

These references provide guidance and technical specifications; implementing the project does not confer forensic accreditation or legal admissibility.

## Current status

ProofTrace is in its initial development stage. The repository contains project documentation and an initial hashing/acquisition foundation is the first implementation target. Features listed as planned are not yet implemented.

---

**Built as an independent digital forensics and cybersecurity project.**
