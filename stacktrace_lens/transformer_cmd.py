"""CLI sub-command: transform – rewrite frame paths / names via rules."""
from __future__ import annotations

import argparse
import re
import sys
from typing import List

from stacktrace_lens.parser import Frame, parse_stacktrace
from stacktrace_lens.transformer import TransformRule, transform_trace


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("transform", help="Rewrite frame filenames and function names")
    p.add_argument("--rename-file", metavar="OLD=NEW", action="append", default=[],
                   help="Replace OLD substring in filename with NEW")
    p.add_argument("--rename-func", metavar="OLD=NEW", action="append", default=[],
                   help="Replace OLD substring in function name with NEW")
    p.add_argument("--strip-prefix", metavar="PREFIX", action="append", default=[],
                   help="Strip PREFIX from the start of every filename")
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    return p


def _parse_kv(pairs: List[str]) -> List[tuple[str, str]]:
    result = []
    for pair in pairs:
        if "=" not in pair:
            continue
        old, new = pair.split("=", 1)
        result.append((old, new))
    return result


def transformer_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        if args.file:
            with open(args.file) as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError as exc:
        err.write(f"error: {exc}\n")
        return 1

    trace = parse_stacktrace(raw)
    if not trace:
        err.write("error: no stack trace found in input\n")
        return 1

    rules: List[TransformRule] = []
    for old, new in _parse_kv(args.rename_file):
        rules.append(TransformRule(
            name=f"rename-file:{old}->{new}",
            apply=lambda f, o=old, n=new: Frame(
                filename=f.filename.replace(o, n),
                lineno=f.lineno,
                function=f.function,
                context=f.context,
            ),
        ))
    for old, new in _parse_kv(args.rename_func):
        rules.append(TransformRule(
            name=f"rename-func:{old}->{new}",
            apply=lambda f, o=old, n=new: Frame(
                filename=f.filename,
                lineno=f.lineno,
                function=f.function.replace(o, n),
                context=f.context,
            ),
        ))
    for prefix in args.strip_prefix:
        rules.append(TransformRule(
            name=f"strip-prefix:{prefix}",
            apply=lambda f, p=prefix: Frame(
                filename=f.filename[len(p):] if f.filename.startswith(p) else f.filename,
                lineno=f.lineno,
                function=f.function,
                context=f.context,
            ),
        ))

    report = transform_trace(trace, rules)
    out.write(f"{report.summary_line()}\n")
    for tf in report.frames:
        tag = f" [{', '.join(tf.rules_applied)}]" if tf.rules_applied else ""
        out.write(f"  {tf.result.filename}:{tf.result.lineno} in {tf.result.function}{tag}\n")
    return 0
