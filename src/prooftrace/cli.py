"""Command-line interface for initial ProofTrace workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prooftrace.analyzers.pdf import compare_pdf_versions, inspect_pdf
from prooftrace.core.acquisition import acquire_file
from prooftrace.core.hashing import hash_file
from prooftrace.core.verification import verify_file


def _write_json(data: object, output: str | None) -> None:
    rendered = json.dumps(data, indent=2, ensure_ascii=False)
    if output:
        Path(output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


def main() -> None:
    parser = argparse.ArgumentParser(prog="prooftrace", description="Digital evidence integrity toolkit")
    commands = parser.add_subparsers(dest="command", required=True)

    hash_cmd = commands.add_parser("hash", help="Calculate SHA-256 and SHA-512")
    hash_cmd.add_argument("file")

    verify_cmd = commands.add_parser("verify", help="Verify a file against a SHA-256 reference")
    verify_cmd.add_argument("file")
    verify_cmd.add_argument("--sha256", required=True)

    acquire_cmd = commands.add_parser("acquire", help="Preserve a file and create an acquisition record")
    acquire_cmd.add_argument("file")
    acquire_cmd.add_argument("--evidence-dir", default="evidence")
    acquire_cmd.add_argument("--collector", required=True)
    acquire_cmd.add_argument("--source", required=True)
    acquire_cmd.add_argument("--output")

    pdf_cmd = commands.add_parser("pdf-inspect", help="Inspect PDF structure and metadata")
    pdf_cmd.add_argument("file")
    pdf_cmd.add_argument("--output")

    compare_cmd = commands.add_parser("pdf-compare", help="Compare two PDF versions")
    compare_cmd.add_argument("before")
    compare_cmd.add_argument("after")
    compare_cmd.add_argument("--output")

    args = parser.parse_args()
    if args.command == "hash":
        _write_json({"file": args.file, "digests": hash_file(args.file)}, None)
    elif args.command == "verify":
        result = verify_file(args.file, {"sha256": args.sha256})
        _write_json(result, None)
        if result["status"] != "match":
            raise SystemExit(1)
    elif args.command == "acquire":
        record = acquire_file(
            args.file,
            args.evidence_dir,
            collector=args.collector,
            source_description=args.source,
        )
        _write_json(record.to_dict(), args.output)
    elif args.command == "pdf-inspect":
        _write_json(inspect_pdf(args.file), args.output)
    elif args.command == "pdf-compare":
        _write_json(compare_pdf_versions(args.before, args.after), args.output)


if __name__ == "__main__":
    main()
