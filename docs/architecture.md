# ProofTrace Architecture

## Goals

ProofTrace is a local-first, modular evidence examination toolkit. Its first engineering priority is trustworthy acquisition and repeatable verification, not a large interface.

## High-level pipeline

```text
Evidence source
    |
    v
Acquisition service
    |-- source/context record
    |-- byte-preserving copy
    |-- SHA-256 / SHA-512
    v
Evidence manifest
    |
    +--> PDF analyzer
    +--> DOCX analyzer
    +--> Image analyzer
    +--> Signature / provenance validators
    |
    v
Comparison and findings
    |
    v
Signed report + verification package
```

## Components

### Core

- `hashing.py`: streaming digest calculation.
- `acquisition.py`: create an acquisition record and preserve incoming bytes.
- `verification.py`: re-hash preserved evidence and compare with recorded digests.

### Analyzers

Each format analyzer must be read-only against the preserved original and return structured findings. It must identify parser/tool versions and distinguish unsupported, absent and invalid artefacts.

- PDF: object structure, incremental updates, embedded files, signatures and revisions.
- DOCX: ZIP members, OOXML properties, tracked revisions, comments, relationships and embedded content.
- Images: EXIF/XMP, dimensions, encoding information, pixel comparisons and C2PA manifests where supported.

### Evidence

- Manifest: versioned acquisition and analysis record.
- Ledger: append-only event history with event chaining and verification.
- Custody: transfers, handlers, timestamps, purpose and signatures.

### Reporting

Reports must separate observations, test results, interpretation and limitations. No automated finding should label a file fraudulent or identify an editor without independent evidence.

## Trust boundaries

1. The host operating system and acquisition environment are outside ProofTrace's trust boundary unless independently secured and documented.
2. A local SQLite database alone is not tamper-proof.
3. A hash stored beside a file can be replaced alongside it unless protected by an independent signature, timestamp or trusted system.
4. Trusted timestamps attest that a digest existed no later than the TSA time; they do not prove when the document was first created.
5. A valid digital signature supports integrity/authentication claims within its signed scope and certificate-validation context; it does not prove that statements in a document are true.

## Preservation design

- Open source files read-only where possible.
- Copy evidence into a controlled evidence store.
- Hash the input stream and preserved copy; require equality.
- Keep analysis outputs separate from evidence bytes.
- Verify the preserved copy before and after analysis.
- Record failures and interruptions.
- Never silently normalize, repair, re-save or convert the original.

## Future interface

A desktop interface (PySide6) is a later layer over the same application services. The core must remain usable from Python APIs and a CLI so tests and independent verification do not depend on the UI.
