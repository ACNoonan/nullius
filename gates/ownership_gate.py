#!/usr/bin/env python3
"""PreToolUse gate: an ownership concession must not contradict the declared register.

WHY
    A project can have five live gates and a numeric ledger and still have nothing
    checking an OWNERSHIP assertion. Each of the others asks a different question:
    was the read done (research-depth), does the key point at the right paper
    (citation-attribution), is the identifier declared (vocab), did the arms run
    (prereg-commitment), does the effective sample size name its marginal
    (marginal). "This is ours" / "this is theirs" / "we claim none of this" was
    enforced by diligence alone.

    2026-08-01, in a paper about design effects: one section edit wrote "We claim
    none of this structure and it should not be read as new" and conceded a
    composition to [kish1965] eq. 5.6.8 — while the same paper's prior-art table
    says Kish coined the design effect "for means and proportions, NEVER for his
    own §12.9", which is exactly where the relevant indicator lives. Two sentences
    in one document, in direct contradiction. Nothing fired. It was caught by
    hand, late, after it had already driven a project-level recommendation.

    Third instance of the class: [crespi2011] stated the paper's central claim and
    sat uncited for a day after that was known; [gulliford2005] was declined on
    second-hand grounds without anyone reading him. **An over-concession is as
    damaging as an over-claim and strictly harder to catch, because no referee
    will do it for you** — a referee's incentive runs the other way.

WHY THE OBVIOUS RULE DOES NOT WORK (measured, not assumed)
    The tempting check is "flag any concession that names a registered owner". It
    fires on legitimate concessions, which are the majority. One coverage-law
    section reads "Every component of that picture is published, and we claim none
    of them" and is entirely correct — none of the keys in that paragraph carries
    an exclusion. Scoping to the EXCLUDES field is what separates the two, and
    this docstring records the negative control because a gate whose rule was
    never tested against a real non-failure gets switched off within a week, after
    which nothing is enforced.

THE REGISTER
    An `OWNERSHIP.md` anywhere in the governed tree. Rows are headed `### [P3] …`
    and an exclusion is a line of the form:

        **EXCLUDES:** [kish1965] — his own §12.9. Kish coined the design effect
        for means and proportions and never applied it there.

    The text between the dash and the first sentence-ending period is the SCOPE
    MARKER: the bounded thing this owner does *not* hold.

WHAT THIS BLOCKS
    A Write/Edit that introduces ownership-CONCESSION language ("we claim none",
    "is not new", "should not be read as new", "is not ours", "we do not claim")
    in a paragraph that names a citation key carrying an EXCLUDES row, WITHOUT
    naming that exclusion's scope marker in the same paragraph. The marker is what
    shows the writer knew the exception.

WHAT THIS DELIBERATELY DOES NOT DO
    It does not check the CLAIM direction ("this is ours"). Detecting an over-claim
    needs to know which ingredient a sentence is about, and every formulation tried
    produced false positives on assembly language, which is how a synthesis paper
    legitimately talks. The concession direction is the demonstrated failure and is
    what is gated; the claim direction stays a review item. It also cannot tell a
    good concession from a bad one where no exclusion is declared — if the register
    is wrong or silent, this gate is silent too. Keeping `OWNERSHIP.md` current is
    the human's job.

FAIL-OPEN
    Any internal error, unreadable input, missing register or unexpected shape =>
    allow. A hook that blocks work because the hook broke gets retired.

STANDALONE AUDIT
    python3 ownership_gate.py --audit path/to/sections_or_file
    Sweeps existing prose for the same contradiction and exits 1 if any is found.
    Use this on material that predates the gate.
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

REGISTER_NAME = "OWNERSHIP.md"

# `**EXCLUDES:** [key] — MARKER. explanation…`  (em dash or hyphen, marker up to first period)
EXCLUDES_RE = re.compile(
    # marker runs to the first sentence-ending period — one FOLLOWED BY whitespace,
    # so that "§12.9" and "eq. 5.6.8" survive intact rather than truncating to "§12".
    r"\*\*EXCLUDES:\*\*\s*\[(?P<key>[A-Za-z][A-Za-z0-9_]*)\]\s*[—\-–]\s*(?P<marker>.+?)\.(?=\s)",
    re.M)
ROW_RE = re.compile(r"^###\s*\[(?P<id>P\d+)\]\s*(?P<title>.+?)\s*$", re.M)
CITE_RE = re.compile(r"\[([a-z][a-z0-9_]*)\]")

CONCESSIONS = (
    "we claim none",
    "claim none of",
    "should not be read as new",
    "is not new",
    "are not new",
    "is not ours",
    "are not ours",
    "we do not claim",
    "we claim no novelty",
    "no novelty is claimed",
)

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".mypy_cache"}


def find_register() -> str | None:
    for root in ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            if REGISTER_NAME in filenames:
                return os.path.join(dirpath, REGISTER_NAME)
    return None


def load_exclusions(path: str) -> dict[str, list[tuple[str, str]]]:
    """{citation_key: [(row_id, scope_marker), …]}"""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except Exception:
        return {}
    rows = [(m.group("id"), m.start()) for m in ROW_RE.finditer(text)]
    out: dict[str, list[tuple[str, str]]] = {}
    for m in EXCLUDES_RE.finditer(text):
        rid = "?"
        for r_id, r_start in rows:
            if r_start < m.start():
                rid = r_id
            else:
                break
        out.setdefault(m.group("key"), []).append((rid, m.group("marker").strip()))
    return out


def marker_present(para: str, marker: str) -> bool:
    """Did the writer name the exception? Accept the marker or its distinctive token."""
    p = para.lower()
    mk = marker.lower().strip()
    if mk and mk in p:
        return True
    # a marker like "§12.9" or "unimodality" — accept its longest alphanumeric run too
    toks = [t for t in re.split(r"[^0-9a-z§.]+", mk) if len(t) >= 4]
    return any(t in p for t in toks)


def paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def check_text(text: str, excl: dict[str, list[tuple[str, str]]]) -> list[str]:
    fails: list[str] = []
    for para in paragraphs(text):
        low = para.lower()
        hit = next((c for c in CONCESSIONS if c in low), None)
        if not hit:
            continue
        for key in set(CITE_RE.findall(para)):
            for rid, marker in excl.get(key, []):
                if marker_present(para, marker):
                    continue
                snippet = re.sub(r"\s+", " ", para.strip())[:150]
                fails.append(
                    f"CONCESSION/EXCLUSION: a paragraph conceding ownership "
                    f"(\"{hit}\") names [{key}], but {REGISTER_NAME} row {rid} "
                    f"records that [{key}] does NOT hold this — exclusion scope: "
                    f"\"{marker}\". The paragraph never names that scope, so it "
                    f"concedes more than the register allows.\n"
                    f"      paragraph: …{snippet}…")
    return fails


def audit(target: str) -> int:
    global ROOTS
    ROOTS = roots_for(os.path.join(os.path.abspath(target), "x"))
    if not ROOTS:
        print("not inside a repository holding .nullius.toml; nothing to check")
        return 0
    reg = find_register()
    if not reg:
        print(f"no {REGISTER_NAME} found; nothing to check")
        return 0
    excl = load_exclusions(reg)
    print(f"register: {reg}  ({sum(len(v) for v in excl.values())} exclusion(s) "
          f"over {len(excl)} key(s))")
    files = []
    if os.path.isdir(target):
        for dp, dn, fn in os.walk(target):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            files += [os.path.join(dp, f) for f in fn if f.endswith(".md")]
    else:
        files = [target]
    bad = 0
    for f in sorted(files):
        if os.path.basename(f) == REGISTER_NAME:
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
        except Exception:
            continue
        for msg in check_text(txt, excl):
            bad += 1
            print(f"\n[{os.path.relpath(f)}]\n  ✗ {msg}")
    print(f"\n{len(files)} file(s) scanned, {bad} contradiction(s).")
    return 1 if bad else 0


def main() -> int:
    if "--audit" in sys.argv:
        i = sys.argv.index("--audit")
        return audit(sys.argv[i + 1])

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    ti = payload.get("tool_input") or {}
    path = ti.get("file_path") or ""
    global ROOTS
    ROOTS = roots_for(path)
    if not ROOTS:
        return 0                                 # repo did not opt in
    if not path or not any(os.path.abspath(path).startswith(r) for r in ROOTS):
        return 0
    if not path.endswith(".md") or os.path.basename(path) == REGISTER_NAME:
        return 0

    text = ti.get("content") or ti.get("new_string") or ""
    if not text.strip():
        return 0

    reg = find_register()
    if not reg:
        return 0
    excl = load_exclusions(reg)
    if not excl:
        return 0

    fails = check_text(text, excl)
    if fails:
        reason = (f"BLOCKED — an ownership concession contradicts {REGISTER_NAME}.\n\n"
                  + "\n\n".join(f"  • {f}" for f in fails)
                  + "\n\nAn over-concession is as damaging as an over-claim and no "
                    "referee will catch it for you. Either name the exclusion's "
                    "scope in the same paragraph — showing the concession is "
                    "bounded — or amend the register if it is now wrong.")
        try:
            from _gatelog import record as _rec
            _rec("ownership-gate", reason, path)
        except Exception:
            pass
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)          # fail open, always
