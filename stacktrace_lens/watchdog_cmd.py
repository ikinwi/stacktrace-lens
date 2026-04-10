"""CLI sub-command: watch a log file for stack traces."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .formatter import FormatOptions, StackTraceFormatter
from .severity import format_severity
from .watchdog import WatchAlert, WatchOptions, tail_file


def _build_subparser(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("file", help="Log file to watch")
    sub.add_argument(
        "--min-score",
        type=int,
        default=0,
        metavar="N",
        help="Only alert on traces with severity score >= N (default: 0)",
    )
    sub.add_argument(
        "--max-alerts",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N alerts",
    )
    sub.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colour output",
    )
    sub.add_argument(
        "--poll",
        type=float,
        default=1.0,
        metavar="SECS",
        help="Polling interval in seconds (default: 1.0)",
    )


def watchdog_command(args: argparse.Namespace) -> int:
    """Entry point for the *watch* sub-command. Returns an exit code."""
    target = Path(args.file)
    if not target.exists():
        print(f"error: file not found: {target}", file=sys.stderr)
        return 1

    opts = WatchOptions(
        poll_interval=args.poll,
        min_severity_score=args.min_score,
        max_alerts=args.max_alerts,
    )
    fmt_opts = FormatOptions(color=not args.no_color)
    formatter = StackTraceFormatter(fmt_opts)

    print(f"Watching {target} …  (Ctrl-C to stop)", file=sys.stderr)

    def _on_alert(alert: WatchAlert) -> None:
        sep = "─" * 60
        print(sep)
        print(format_severity(alert.severity))
        print(formatter.format(alert.trace))
        print()

    try:
        tail_file(target, opts, _on_alert)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nWatchdog stopped.", file=sys.stderr)

    return 0
