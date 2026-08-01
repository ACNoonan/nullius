#!/usr/bin/env python3
"""PreToolUse gate: an identifier must belong to a namespace someone declared.

WHY (2026-07-29)
    Twenty-nine ID namespaces were in daily use across this repo with ZERO
    definitions anywhere on disk, and they were not the same kind of thing:
    `AB-01` is a published paper, `AB-06` a branch in a register, `AB-07` a gate
    whose pre-registration lives in a DIFFERENT repository, `AB-09` somebody
    else's dataset, `AB-10` a test local to one directory. Five categories
    wearing identical syntax, so a sentence built out of them ("AB-08 failed,
    AB-07's pool is accruing, AB-06 is unblocked") could not be parsed by anyone
    who was not in the room when the names were coined.

    The names were mostly coined mid-session, by me, and never written down. That
    is the specific behaviour this blocks.

WHAT THIS BLOCKS
    A Write/Edit that introduces an identifier in a namespace no VOCAB.md
    declares, or a qualified `lane/K-NN` naming a lane that does not exist, or a
    NEW single-letter namespace (banned: indistinguishable from algebra —
    `print((M-1)/(2*M))` was flagged as an identifier on the first lint run).

WHAT IT DELIBERATELY DOES NOT DO
    It does not check that a registered ID is *used correctly*, and it does not
    complain about legacy IDs — every namespace in use on 2026-07-29 was
    registered as-is, without renaming. It stops the vocabulary from GROWING
    silently, which is the only part a text hook can honestly enforce.

    It also stays silent on LEAK and UNDEFINED (see vocab.py). Those are real but
    advisory; blocking on them would make every cross-lane citation a fight.

FAIL-OPEN
    Any internal error, unreadable input, missing VOCAB.md or absent vocab.py =>
    allow. A gate that blocks work because the gate broke gets deleted within a
    day, and then nothing is enforced at all.
"""
from __future__ import annotations

import json
import os
import re
import sys

DOC_RE = re.compile(r"\.(md|txt|py)$", re.I)
# Same exclusions as the linter: other people's prose, and machine output.
EXEMPT_RE = re.compile(r"/(papers/(text|pdfs)|sources|build|cache)/", re.I)


def find_repo(path):
    """Walk up from a file to the nearest directory holding a root VOCAB.md."""
    d = os.path.dirname(os.path.abspath(path))
    while d and d != "/":
        if os.path.isfile(os.path.join(d, "VOCAB.md")) and \
           os.path.isfile(os.path.join(d, "vocab.py")):
            return d
        d = os.path.dirname(d)
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0                                     # fail-open

    try:
        if payload.get("tool_name", "") not in ("Write", "Edit"):
            return 0

        ti = payload.get("tool_input", {}) or {}
        path = ti.get("file_path", "")
        if not path or not DOC_RE.search(path) or EXEMPT_RE.search(path):
            return 0
        if os.path.basename(path) in ("VOCAB.md", "vocab.py"):
            return 0                                 # the registry may name anything

        repo = find_repo(path)
        if repo is None:
            return 0

        sys.path.insert(0, repo)
        try:
            import vocab                             # single source of truth
        except Exception:
            return 0                                 # fail-open
        namespaces, _defined, lanes = vocab.load_registry(repo)
        if not namespaces:
            return 0

        text = ti.get("content") or ti.get("new_string") or ""
        if not text:
            return 0

        prose = os.path.splitext(path)[1].lower() in (".md", ".txt")
        bad_ns, bad_lane, bad_short = {}, {}, {}
        for m in vocab.BARE_RE.finditer(text):
            if m.group(1) not in namespaces:
                bad_ns.setdefault(m.group(1), m.group(0))
        if prose:
            for m in vocab.BARE_SHORT_RE.finditer(text):
                if m.group(1) not in namespaces:
                    bad_short.setdefault(m.group(1), m.group(0))
        for m in vocab.QUAL_RE.finditer(text):
            if m.group(1) not in lanes:
                bad_lane.setdefault(m.group(1), m.group(0))

        if not (bad_ns or bad_lane or bad_short):
            return 0

        lines = []
        if bad_ns:
            lines.append("  Undeclared namespace(s): "
                         + ", ".join(f"`{p}-` (e.g. {t})"
                                     for p, t in sorted(bad_ns.items())))
        if bad_short:
            lines.append("  New SINGLE-LETTER namespace(s), which the grammar bans: "
                         + ", ".join(f"`{p}-` (e.g. {t})"
                                     for p, t in sorted(bad_short.items())))
        if bad_lane:
            lines.append("  Unknown lane(s): "
                         + ", ".join(f"`{p}/` (e.g. {t})"
                                     for p, t in sorted(bad_lane.items())))

        reason = (
            "BLOCKED — an identifier with no entry in VOCAB.md.\n\n"
            f"In {os.path.basename(path)}:\n" + "\n".join(lines) + "\n\n"
            "Names coined mid-session and never written down are why a sentence "
            "like \"AB-08 failed, AB-07's pool is accruing, AB-06 is unblocked\" "
            "cannot be read by anyone who was not there. Twenty-nine namespaces "
            "were in use with zero definitions before this gate existed.\n\n"
            "To proceed, do ONE of:\n"
            f"  1. Reuse an existing namespace — `python3 {os.path.relpath(repo)}/vocab.py "
            "--namespaces` lists all of them with their scope and owner.\n"
            "  2. Use the current grammar instead of a new prefix: `lane/T-01` for a "
            "test, `G` gate, `D` dataset, `Q` question, `R` result. The lane prefix "
            "is what tells a reader which arm of which project it belongs to.\n"
            "  3. If it genuinely needs a new namespace, add the row to VOCAB.md "
            "FIRST — kind, scope, owner, meaning — then write this file.\n\n"
            "Do not invent a meaning for an identifier you did not coin. Ask."
        )
        try:                                   # firing ledger; never fatal
            from _gatelog import record as _rec
            _l = locals()
            _rec("vocab-gate", _l.get("reason", ""),
                 _l.get("path") or _l.get("file_path") or _l.get("target") or "")
        except Exception:
            pass
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))
        return 0
    except Exception:
        return 0                                     # fail-open, always


if __name__ == "__main__":
    sys.exit(main())
