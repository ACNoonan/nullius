#!/usr/bin/env python3
"""PreToolUse gate: a RESULT may not be written into a prereg whose §3 arms never ran.

WHY (2026-07-28)
    AB-03 §3 committed to a `p_search ∈ {0.0, 0.25, 0.50}` sensitivity arm and a
    verdict was reported without it. The gap was not laziness at the gate table —
    §4 was applied faithfully, every precondition passed. It was that
    preconditions are OBJECTS the code refuses to run without, and §3's
    robustness arms are PROSE that only a careful re-read enforces.

    `harness/prereg.py` closes that inside the verdict path: pass
    `emit_verdict(..., prereg=AB-03.md)` and an undischarged commitment voids the
    verdict. But AB-03 §6 was written BY HAND, in an editor, and the verdict
    script was never re-run for the robustness arm — so the runtime gate would
    have sat there unfired. This hook is the layer that covers that: the moment a
    result is written INTO the document, the document's own commitments are
    checked.

WHAT THIS BLOCKS
    A Write/Edit that puts a result marker (`## 6. RESULT`, `status: confirmed`,
    a `Verdict against §4`, a `Confidence tier`) into a pre-registration whose
    ```commitments block has entries with no artifact behind them. And a result
    written into a prereg that has no ```commitments block at all — because that
    is the pre-AB-03 state, where §3 binds nothing.

WHAT IT DELIBERATELY DOES NOT DO
    It cannot tell whether a §3 sentence was left out of the block. A commitment
    nobody encodes is invisible to it, exactly as before. That residue is why
    `prereg.py` requires `text` verbatim: the block diffs against the document by
    eye, and the weakest link should be the visible one. Presence, never quality —
    the same honest limit as the depth gate.

FAIL-OPEN
    Any internal error, unreadable input, or unexpected shape => allow. Same
    trade as the depth gate: a hook that blocks work because the hook itself
    broke gets retired within a day, and then nothing is enforced.
"""
from __future__ import annotations

import json
import os
import re
import sys

# Opted-in trees only; resolved per-write in main(). See _config.py.
try:
    from _config import roots_for
except Exception:                                # never let config break a gate
    def roots_for(_path):
        return ()

ROOTS: tuple = ()          # set by main() once the target path is known

HARNESS = os.path.expanduser("~/Documents/llm-study/harness")

# Only a pre-registration. A doc that never claims to be one is not gated —
# this is a discipline gate on prereg documents, not a global lint on markdown.
PREREG_RE = re.compile(r"pre-regist", re.I)

# The markers that turn a prereg into a REPORTED RESULT. Any one of them means a
# verdict is being committed to the document.
RESULT_RE = re.compile(
    r"^\s*#+\s*\d*\.?\s*RESULT\b"
    r"|^status:\s*(confirmed|refuted|superseded)\b"
    r"|Verdict against\b"
    r"|\*\*Confidence tier\*\*",
    re.I | re.M,
)

FENCE_RE = re.compile(r"^```commitments\s*$(.*?)^```\s*$", re.M | re.S)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    try:
        if payload.get("tool_name", "") not in ("Write", "Edit"):
            return 0

        ti = payload.get("tool_input", {}) or {}
        path = ti.get("file_path", "")
        if not path or not path.lower().endswith(".md"):
            return 0
        apath = os.path.abspath(path)
        global ROOTS
        ROOTS = roots_for(path)
        if not ROOTS:
            return 0                                 # repo did not opt in
        if not any(apath.startswith(r) for r in ROOTS):
            return 0

        new = ti.get("content") or ti.get("new_string") or ""
        if not new or not RESULT_RE.search(new):
            return 0                       # not writing a result; nothing to gate

        on_disk = ""
        if os.path.exists(apath):
            with open(apath, encoding="utf-8", errors="replace") as fh:
                on_disk = fh.read()

        whole = new if FENCE_RE.search(new) else (on_disk + "\n" + new)
        if not PREREG_RE.search(whole):
            return 0                       # not a pre-registration

        name = os.path.basename(apath)
        if not FENCE_RE.search(whole):
            reason = (
                f"BLOCKED — {name} reports a RESULT but has no ```commitments block.\n\n"
                "Its §3 robustness arms are prose, which is the state AB-03 was in when "
                "it committed to a `p_search {0.0, 0.25, 0.50}` sweep in a sentence and "
                "reported a verdict without ever running it. Nothing failed; the "
                "commitment was not a kind of object.\n\n"
                "To proceed, add to §3 a fenced ```commitments block — JSON, one entry "
                "per arm a result could be reported without:\n\n"
                '```commitments\n'
                '[{"id": "C1", "text": "<the §3 sentence VERBATIM>",\n'
                '  "artifact": "result_x_robustness.json",\n'
                '  "requires": ["p_search=0.0", "p_search=0.25", "p_search=0.5"]}]\n'
                '```\n\n'
                "If there genuinely are none, an empty list with a line above it saying "
                "so is the honest form, and it is auditable. Check with:\n"
                f"    python3 {HARNESS}/prereg.py {path}"
            )
        else:
            # Write the merged text somewhere prereg.py can parse it in place, so the
            # commitment paths still resolve relative to the real document's directory.
            sys.path.insert(0, HARNESS)
            import tempfile

            import prereg  # noqa: E402

            fd, tmp = tempfile.mkstemp(suffix=".md", dir=os.path.dirname(apath))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(whole)
                results = prereg.check(tmp)
            finally:
                os.unlink(tmp)

            bad = [r for r in results if not r.discharged]
            if not bad:
                return 0

            lines = "\n".join(
                f"    ⛔ {r.id}: {r.detail}\n       “{r.commitment.text}”" for r in bad[:4])
            reason = (
                f"BLOCKED — {name} reports a RESULT with "
                f"{len(bad)}/{len(results)} §3 commitments undischarged.\n\n"
                f"{lines}\n\n"
                "A pre-registration's value is that it binds you to the checks you would "
                "rather skip once you have seen the headline. Reporting the verdict first "
                "and the robustness arm later is the same as not pre-registering it.\n\n"
                "To proceed, do ONE of:\n"
                "  1. Run the arm, then write the result.\n"
                "  2. Amend §3 in place, dated, with the reason — the way AB-04 dropped "
                "E2 BEFORE any result existed, for a checkable arithmetic reason. An "
                "amendment made after seeing the headline is not the same object and "
                "must say so.\n"
                f"  3. Re-check: python3 {HARNESS}/prereg.py {path}"
            )

        try:                                   # firing ledger; never fatal
            from _gatelog import record as _rec
            _l = locals()
            _rec("prereg-commitment-gate", _l.get("reason", ""),
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
        return 0                            # fail-open, always


if __name__ == "__main__":
    sys.exit(main())
