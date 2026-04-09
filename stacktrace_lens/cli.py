"""Command-line interface for stacktrace-lens."""

import sys
import argparse
from typing import Optional

from .parser import parse_stacktrace
from .formatter import StackTraceFormatter, FormatOptions
from .suggestions import get_all_suggestions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stacktrace-lens",
        description="Parse and pretty-print Python stack traces with suggestions.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to a file containing a stack trace (reads stdin if omitted).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable color output.",
    )
    parser.add_argument(
        "--no-suggestions",
        action="store_true",
        default=False,
        help="Suppress context-aware suggestions.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        default=False,
        help="Print a compact one-line-per-frame summary.",
    )
    return parser


def read_input(file_path: Optional[str]) -> str:
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                return fh.read()
        except OSError as exc:
            print(f"stacktrace-lens: error reading file: {exc}", file=sys.stderr)
            sys.exit(1)
    if sys.stdin.isatty():
        print("stacktrace-lens: reading from stdin — paste a traceback then press Ctrl-D.",
              file=sys.stderr)
    return sys.stdin.read()


def main(argv=None) -> int:
    arg_parser = build_parser()
    args = arg_parser.parse_args(argv)

    raw = read_input(args.file)
    if not raw.strip():
        print("stacktrace-lens: no input provided.", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)

    options = FormatOptions(
        color=not args.no_color,
        compact=args.compact,
        show_suggestions=not args.no_suggestions,
    )
    formatter = StackTraceFormatter(options)
    print(formatter.format(trace))

    if not args.no_suggestions:
        suggestions = get_all_suggestions(trace)
        if suggestions:
            header = "\n\033[1;36m💡 Suggestions:\033[0m" if options.color else "\nSuggestions:"
            print(header)
            for suggestion in suggestions:
                bullet = "  \033[36m•\033[0m " if options.color else "  • "
                print(f"{bullet}{suggestion}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
