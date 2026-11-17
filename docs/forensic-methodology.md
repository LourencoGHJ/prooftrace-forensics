# Forensic Methodology

This document describes the intended workflow for ProofTrace. It is an engineering methodology and not legal advice, an accredited laboratory procedure, or a substitute for jurisdiction-specific rules and organizational SOPs.

## 1. Preparation and authority

Before collection, record purpose, scope, legal/organizational authority, source, collection method, known constraints and responsible person. Do not access or analyze material without appropriate authorization.

## 2. Acquisition

For each item, record:

- Unique evidence ID.
- Original filename and observed file type.
- Source and person/system providing it.
- Collector and acquisition workstation identity.
- Acquisition start/end time in UTC, plus original timezone when known.
- Tool name, version and acquisition method.
- File size and relevant errors.
- SHA-256 digest; SHA-512 may be calculated as an additional digest.

The digest is calculated over the exact bytes acquired. Preserve the received item without format conversion.

## 3. Preservation and working copies

Create a preserved evidence copy and verify its digest against the acquired stream. Restrict write access and document storage controls. Perform parsing, rendering, extraction and comparisons on a working copy. Re-verify the preserved copy after examination.

A filesystem read-only flag is a useful precaution but is not equivalent to a hardware write blocker or a complete tamper-proof storage system.

## 4. Examination

Use format-specific parsers. Record parser versions, configuration, warnings, errors and extracted artefacts. Distinguish artefact absent, present and valid, present but invalid, unsupported/not examined, and inconclusive.

Do not treat metadata timestamps as trusted timestamps. Metadata can be edited, removed, copied or regenerated.

## 5. Comparison

Compare only explicitly identified versions. Report byte-level digest differences separately from semantic changes, extracted-text differences, structural differences and visual differences. A rendering difference does not necessarily mean visible content was intentionally edited; software re-saving can change bytes and internal structures.

## 6. Trusted time and provenance

When configured, submit a digest to an RFC 3161-compliant Time-Stamp Authority and retain the complete token and validation material. A valid token supports the proposition that the committed digest existed at or before the TSA time, subject to token validation and trust policy.

C2PA manifests and embedded signatures may offer provenance assertions. Validate signatures, certificate chains, claim/content bindings, revocation status and supported specification version. Absence of a C2PA manifest is not evidence of manipulation.

## 7. Chain of custody

Every custody event should include evidence ID, event ID, handler, action, date/time (UTC), source/destination, reason, verification result and supporting record. Events should be append-only and cryptographically linked. Event chaining detects later edits only when the expected chain head is protected independently.

## 8. Reporting

Every report must include scope, authority/context supplied, evidence identifiers, acquisition details, cryptographic digests, tool versions, methods, results, limitations, exceptions and examiner identity. Preserve original logs and machine-readable manifests alongside the human-readable report.

## 9. Interpretation categories

Use restrained language:

- **MATCH:** supplied digest/reference matches acquired bytes.
- **MISMATCH:** supplied digest/reference does not match acquired bytes.
- **CHANGE OBSERVED:** a specific difference or later revision was identified.
- **SIGNATURE VALID / INVALID / INDETERMINATE:** according to the validation performed and scope.
- **PROVENANCE FOUND / NOT FOUND / INDETERMINATE:** based only on examined artefacts.
- **NO CONCLUSION:** evidence is insufficient.

Never infer the first-ever hash, original creation date, identity of an editor, intent to deceive, or legal admissibility from a file alone.
