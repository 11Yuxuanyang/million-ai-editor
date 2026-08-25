#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system.assets.classification import build_review_batch, classify_catalog
from system.assets.identity import build_identity_report, write_link_reports
from system.assets.inventory import load_summary, scan_workspace
from system.assets.references import (
    create_contact_sheet,
    init_reference,
    validate_reference,
    validate_reference_library,
)


def command_audit(args: argparse.Namespace) -> int:
    summary = scan_workspace(Path(args.root), Path(args.output), workers=args.workers)
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_status(args: argparse.Namespace) -> int:
    summary = load_summary(Path(args.catalog))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_classify(args: argparse.Namespace) -> int:
    summary = classify_catalog(Path(args.catalog))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_review_batch(args: argparse.Namespace) -> int:
    batch = build_review_batch(
        Path(args.catalog), status=args.status, group_by=args.group_by
    )
    print(json.dumps(batch, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_hash(args: argparse.Namespace) -> int:
    if args.scope != "duplicate-candidates":
        raise ValueError("only duplicate-candidates scope is supported")
    summary = build_identity_report(
        Path(args.root), Path(args.catalog), workers=args.workers
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_links(args: argparse.Namespace) -> int:
    summary = write_link_reports(Path(args.catalog))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_reference_init(args: argparse.Namespace) -> int:
    asset_id = args.asset_id or args.asset
    if not asset_id:
        raise ValueError("reference init requires an asset id")
    if args.asset_id and args.asset and args.asset_id != args.asset:
        raise ValueError("positional asset id and --asset must match")
    result = init_reference(
        asset_id=asset_id,
        time_range=args.range,
        destination=Path(args.destination),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_reference_validate(args: argparse.Namespace) -> int:
    if args.all:
        if args.reference_id or args.path:
            raise ValueError("reference validate --all cannot be combined with an id or --path")
        result = validate_reference_library(Path(args.library))
    else:
        target = Path(args.path) if args.path else Path(args.library) / str(args.reference_id)
        if not args.path and not args.reference_id:
            raise ValueError("reference validate requires a reference id, --path, or --all")
        result = validate_reference(target)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


def command_reference_contact_sheet(args: argparse.Namespace) -> int:
    result = create_contact_sheet(
        Path(args.input),
        time_range=args.range,
        output=Path(args.output),
        columns=args.columns,
        rows=args.rows,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portable asset inventory and migration control")
    commands = parser.add_subparsers(dest="command", required=True)

    audit = commands.add_parser("audit", help="Scan a workspace without mutating source files")
    audit.add_argument("--root", required=True)
    audit.add_argument("--output", required=True)
    audit.add_argument("--workers", type=int, default=8)
    audit.set_defaults(handler=command_audit)

    status = commands.add_parser("status", help="Read a generated catalog summary")
    status.add_argument("--catalog", required=True)
    status.set_defaults(handler=command_status)

    classify = commands.add_parser("classify", help="Write proposal-only asset dispositions")
    classify.add_argument("--catalog", required=True)
    classify.set_defaults(handler=command_classify)

    review = commands.add_parser("review-batch", help="Read a grouped proposal review batch")
    review.add_argument("--catalog", required=True)
    review.add_argument("--status", required=True)
    review.add_argument("--group-by", choices=("project", "reason"), default="project")
    review.set_defaults(handler=command_review_batch)

    hash_command = commands.add_parser("hash", help="Full-hash only equal-size duplicate candidates")
    hash_command.add_argument("--root", required=True)
    hash_command.add_argument("--catalog", required=True)
    hash_command.add_argument("--scope", choices=("duplicate-candidates",), required=True)
    hash_command.add_argument("--workers", type=int, default=8)
    hash_command.set_defaults(handler=command_hash)

    links = commands.add_parser("links", help="Write broken and external symlink reports")
    links.add_argument("--catalog", required=True)
    links.set_defaults(handler=command_links)

    reference = commands.add_parser("reference", help="Create and validate compact shot references")
    reference_commands = reference.add_subparsers(dest="reference_command", required=True)

    reference_init = reference_commands.add_parser("init", help="Create a portable draft reference card")
    reference_init.add_argument("asset_id", nargs="?")
    reference_init.add_argument("--asset")
    reference_init.add_argument("--range", required=True)
    reference_init.add_argument("--destination", required=True)
    reference_init.set_defaults(handler=command_reference_init)

    reference_validate = reference_commands.add_parser("validate", help="Validate one reference directory")
    reference_validate.add_argument("reference_id", nargs="?")
    reference_validate.add_argument("--path")
    reference_validate.add_argument("--all", action="store_true")
    reference_validate.add_argument("--library", default="library/references")
    reference_validate.set_defaults(handler=command_reference_validate)

    contact_sheet = reference_commands.add_parser("contact-sheet", help="Extract a compact visual index")
    contact_sheet.add_argument("--input", required=True)
    contact_sheet.add_argument("--range", required=True)
    contact_sheet.add_argument("--output", required=True)
    contact_sheet.add_argument("--columns", type=int, default=4)
    contact_sheet.add_argument("--rows", type=int, default=2)
    contact_sheet.set_defaults(handler=command_reference_contact_sheet)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.handler(args))
    except (FileNotFoundError, ValueError, PermissionError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
