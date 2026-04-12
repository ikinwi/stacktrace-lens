"""CLI sub-command: archive – save / list stack traces in a JSON archive."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stacktrace_lens.archiver import Archive, add_to_archive, load_archive, save_archive
from stacktrace_lens.parser import parse_stacktrace


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("archive", help="Save or list stack traces in a JSON archive")
    p.add_argument("archive_file", help="Path to the archive JSON file")
    p.add_argument("--add", metavar="FILE", help="Stack trace file to add (stdin if omitted)")
    p.add_argument("--label", metavar="LABEL", help="Optional label for the new entry")
    p.add_argument("--list", action="store_true", help="List all entries in the archive")
    return p


def archiver_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    archive_path = Path(args.archive_file)
    archive = load_archive(archive_path) if archive_path.exists() else Archive()

    if args.list:
        if archive.count == 0:
            out.write("Archive is empty.\n")
            return 0
        for i, entry in enumerate(archive.entries, 1):
            label = entry.label or "(no label)"
            out.write(f"{i:>3}. [{label}] {entry.trace.exception_type}: {entry.trace.exception_message}\n")
        return 0

    # Add mode
    if args.add:
        file_path = Path(args.add)
        if not file_path.exists():
            err.write(f"error: file not found: {args.add}\n")
            return 1
        raw = file_path.read_text()
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        err.write("error: no input\n")
        return 1

    trace = parse_stacktrace(raw)
    add_to_archive(archive, trace, label=getattr(args, "label", None))
    save_archive(archive, archive_path)
    out.write(f"Archived {trace.exception_type} ({archive.count} total entries).\n")
    return 0
