#!/usr/bin/env python3
"""Run a gate against text on purpose, and label the firing as a control.

    tools/selftest.py ownership_gate PAPER/sections/08.md < offending.md
    tools/selftest.py research_depth_gate notes.md --expect allow < fixed.md

WHY THIS IS A TOOL AND NOT A NOTE IN THE README
    Proving a gate works means feeding it the thing it should refuse — usually
    the exact passage the gate was built from — and watching it refuse. That is
    a positive control and it is the right way to check a gate.

    It also writes a ledger row identical to a real catch. Same gate, same real
    path, same reason. `provenance.py` reads that ledger to derive a published
    paper's firing count, and one such row in the author's own ledger had
    `ownership_gate` looking like it had caught something in the wild. It never
    has: the over-concession was found by hand, and the gate was validated
    against it afterwards.

    `_gatelog` will mark the row when `NULLIUS_CONTROL` is set. But a flag you
    have to remember is a flag you forget, and forgetting inflates the count —
    the same direction every other error in this project ran. So the flag lives
    here, set by the only thing anyone should be running controls with. You
    cannot use this tool without labelling the row, which is what makes an
    UNlabelled row worth trusting.

    Same move as `adapters/git/install.sh`: when correct use depends on someone
    remembering a step, put the step inside a program.

EXIT STATUS
    0 the gate did what you said it would.   1 it did not.   2 usage error.
    So this is usable in CI, and a gate that has quietly stopped firing fails a
    build instead of looking like a clean repo.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
GATES = os.path.join(HERE, "..", "gates")


def run(gate: str, target: str, content: str, expect: str) -> bool:
    """Feed one gate a PreToolUse payload. True when it matched `expect`."""
    path = os.path.join(GATES, gate if gate.endswith(".py") else f"{gate}.py")
    if not os.path.isfile(path):
        sys.exit(f"no such gate: {path}")

    env = dict(os.environ)
    env["NULLIUS_CONTROL"] = "1"          # the point of this file

    payload = json.dumps({"tool_name": "Write",
                          "tool_input": {"file_path": os.path.abspath(target),
                                         "content": content}})
    p = subprocess.run([sys.executable, path], input=payload,
                       capture_output=True, text=True, timeout=30, env=env)

    denied = '"deny"' in p.stdout
    got = "deny" if denied else "allow"
    ok = (got == expect)
    print(f"  {'ok  ' if ok else 'FAIL'}  {os.path.basename(path):<32} "
          f"expected {expect}, got {got}")
    if denied and expect == "deny":
        try:
            reason = json.loads(p.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
            print(f"          {reason.splitlines()[0]}")
        except Exception:
            pass
    if p.stderr.strip():
        print(f"          stderr: {p.stderr.strip()[:200]}")
    return ok


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2

    expect = "deny"
    if "--expect" in argv:
        i = argv.index("--expect")
        expect = argv[i + 1] if i + 1 < len(argv) else ""
        del argv[i:i + 2]
        if expect not in ("deny", "allow"):
            sys.exit("--expect takes 'deny' or 'allow'")

    if len(argv) < 2:
        sys.exit("usage: selftest.py <gate> <target-path> [--expect deny|allow] < content")

    gate, target = argv[0], argv[1]
    content = sys.stdin.read()
    if not content.strip():
        sys.exit("no content on stdin — pipe the text the gate should judge")

    print(f"\ncontrol run (ledger rows will be marked control=true)")
    return 0 if run(gate, target, content, expect) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
