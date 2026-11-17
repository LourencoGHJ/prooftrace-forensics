# Evidence Data Model

The evidence model must be portable, explicit, versioned and independently verifiable.

## Acquisition manifest (draft)

```json
{
  "schema": "prooftrace.evidence.v1",
  "evidence_id": "PT-YYYY-000001",
  "item": {
    "original_filename": "document.pdf",
    "media_type": "application/pdf",
    "size_bytes": 12345
  },
  "acquisition": {
    "started_at_utc": "RFC3339 timestamp",
    "completed_at_utc": "RFC3339 timestamp",
    "collector": "recorded examiner identifier",
    "source_description": "documented source",
    "method": "ProofTrace acquisition workflow",
    "tool": {"name": "ProofTrace", "version": "0.1.0"}
  },
  "digests": {"sha256": "hex digest", "sha512": "hex digest"},
  "preservation": {"original_copy_verified": true, "working_copy_created": true},
  "external_attestations": [],
  "analysis_events": [],
  "custody_events": [],
  "limitations": []
}
```

This is an illustrative schema, not yet a stable public API. The actual implementation must validate required fields and use a formal schema version.

## Event model

Each event should have event ID and sequence number, evidence ID, type, UTC timestamp and clock source/quality where known, actor/handler identifier, action and reason, inputs/outputs and digests, tool/version, previous event digest and current event digest, plus optional digital signature or external timestamp reference.

## Hash-chained events

Each event digest can be computed over a canonical serialization containing the previous event digest. This reveals later edits to a chain if the expected chain head is known. It does not prevent an attacker with control over the whole database from rewriting the entire chain. Periodically export and externally protect, sign or timestamp the chain head.

## Reference types

- `acquisition_digest`: calculated by ProofTrace at acquisition.
- `provided_reference_digest`: supplied by an external source; record who supplied it and how authenticated.
- `embedded_digest`: extracted from an artefact within the file.
- `timestamped_digest`: digest bound to a validated TSA token.
- `signature_digest`: digest or signed byte-range information relevant to a digital signature.

Never merge these into a generic "original hash" field. Their origins and trust properties differ.
