"""Append-only firing ledger for the PreToolUse research gates.

WHY THIS EXISTS
    The gates' claim to work is that they caught real errors. Until 2026-07-30
    that claim rested on transcript archaeology: the denials were recoverable
    from ~/.claude/projects/*/*.jsonl, but only after filtering hook-source
    reads, uninstantiated {name} templates, deliberate .hooktest runs, and
    replayed duplicates from resume/compaction. Four contamination sources,
    each of which inflated a naive count. This file makes that unnecessary
    going forward.

WHAT IT RECORDS
    Gate name, target path, first line of the denial reason, timestamp.
    Deliberately NOT the file content or the offending text — the ledger is
    meant to be publishable as evidence without leaking the research.

THE ONE RULE
    record() may never raise. A logger that breaks turns a fail-open gate into
    a blocker, which is the single failure mode these gates may not have. Every
    path here is wrapped, and callers wrap the import too.
"""
import json
import os
import time

LEDGER = os.path.expanduser("~/.claude/hooks/gate-firings.jsonl")


def record(gate, reason="", target=""):
    """Append one firing row. Silent on every failure, by design."""
    try:
        row = json.dumps(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "gate": str(gate)[:64],
                "target": str(target or "")[:400],
                "reason": str(reason or "").strip().split("\n")[0][:300],
            },
            ensure_ascii=False,
        )
        # One write() on an O_APPEND fd is atomic for a line this size, which
        # matters: ~20 concurrent sessions share this ledger.
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(row + "\n")
    except Exception:
        pass
