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

WHERE IT LIVES, AND WHY THAT IS NOT A CONSTANT
    The path was `~/.claude/hooks/gate-firings.jsonl`, hardcoded. Two things
    were wrong with that, and the second one poisoned the evidence.

    It is Claude-Code-shaped. Someone who installed only the git adapter — the
    portable enforcement layer, the one this project tells them to install
    first — gets a ledger under an agent directory they may not have.

    And a constant cannot be redirected, so `tests/test_gates.py` appended
    every one of its own firings to the user's real ledger. Measured
    2026-08-03: 177 of 220 rows were test rows, 80% of an artifact whose entire
    purpose is to be the thing you check instead of taking a claim on trust.
    `provenance.py` reads that same ledger to derive a published paper's
    firing count, so the stamp would have disclosed 220 where 43 had happened —
    a typed-looking number in the one block of a paper that exists to contain
    no typed numbers.

    So the path is resolved per call, in this order:

        $NULLIUS_LEDGER                              — explicit wins
        ~/.claude/hooks/gate-firings.jsonl           — if it already exists
        $XDG_STATE_HOME/nullius/gate-firings.jsonl   — new installs

    The legacy path is kept when present so an existing ledger is not orphaned
    by an upgrade; nothing migrates it, because moving someone's evidence file
    out from under them is worse than leaving it where they put it.
"""
import json
import os
import time

LEGACY = os.path.expanduser("~/.claude/hooks/gate-firings.jsonl")


def ledger_path():
    """Resolve the ledger fresh on every call. Never raises."""
    try:
        env = os.environ.get("NULLIUS_LEDGER")
        if env:
            return os.path.expanduser(env)
        if os.path.exists(LEGACY):
            return LEGACY
        state = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
        return os.path.join(state, "nullius", "gate-firings.jsonl")
    except Exception:
        return LEGACY


def is_control():
    """True when this firing was provoked on purpose, to prove a gate works.

    THE CASE THIS EXISTS FOR
        A positive control replays text a gate is supposed to refuse — usually
        the very passage the gate was built from — and checks that it refuses.
        The write is real and the path is real, so the row it produces is
        byte-for-byte what a genuine catch produces. Nothing downstream could
        tell them apart, and one row in the author's own ledger is exactly this:
        the §8 over-concession that `ownership_gate` was written for, replayed
        after the fact. Counted raw, it made the gate look like it had caught
        something in the wild. It never has.

        Location filtering does not reach this. A temp path or a `_gatetest.md`
        is detectable precisely because it is fake; a positive control is
        undetectable precisely because everything about it is real except the
        intent, and intent is not in the file.

    SO THE CONTROL DECLARES ITSELF
        `NULLIUS_CONTROL=1` in the environment marks every firing underneath it.
        The gate still blocks — refusing is the whole point of the control — and
        the row is still written. Only its status changes.

        Prefer `tools/selftest.py` over setting this by hand. It sets the
        variable itself, so a control cannot be run without being labelled, and
        an unlabelled row therefore stays trustworthy. Remembering a flag is a
        discipline; not being able to forget it is a design.

    THE DIRECTION IT FAILS IN, STATED
        Forget the flag and a control is counted as a real catch, which inflates
        — the same direction every other error here ran. That is why the label
        belongs on a tool rather than on a habit.
    """
    try:
        return os.environ.get("NULLIUS_CONTROL", "").strip().lower() not in ("", "0", "false", "no")
    except Exception:
        return False


def record(gate, reason="", target=""):
    """Append one firing row. Silent on every failure, by design."""
    try:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "gate": str(gate)[:64],
            "target": str(target or "")[:400],
            "reason": str(reason or "").strip().split("\n")[0][:300],
        }
        if is_control():
            entry["control"] = True
        row = json.dumps(entry, ensure_ascii=False)
        path = ledger_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # One write() on an O_APPEND fd is atomic for a line this size, which
        # matters: ~20 concurrent sessions share this ledger.
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(row + "\n")
    except Exception:
        pass
