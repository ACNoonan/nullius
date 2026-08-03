#!/usr/bin/env python3
"""Provenance stamp + build gate for AI-assisted papers.

THE DESIGN RULE, and the only one that matters:

    Every number in the stamp is DERIVED from an artifact. None is typed.

A disclosure a human wrote is a claim. A disclosure the build computed from the
bibliography, the hook ledger, and the session transcripts is evidence. The
difference is the whole point of the stamp — it is the thing a reader can check
without trusting the author, which is precisely what an unaffiliated
AI-assisted author cannot otherwise offer.

WHAT IT DERIVES
  models    distinct model ids that touched this project, read out of the
            Claude Code session transcripts (not a list anyone typed)
  depth     composition of the bibliography's read-depth register
  gates     firings of the PreToolUse research gates, from the append-only
            ledger written by _gatelog.py

WHAT IT GATES (--check exits 1)
  G1  every bibliography entry declares a read depth
  G2  every declared depth is in the register vocabulary
  G3  the stamp in the paper matches what this script recomputes

The harness is a LIMITER, not a helper. This script's job at build time is to
REFUSE to emit a PDF whose provenance block cannot be backed. It never writes
the disclosure prose for you and never guesses a missing depth.

Usage:
  provenance.py --paper PAPER_DIR              # print the stamp
  provenance.py --paper PAPER_DIR --check      # gate; exit 1 on failure
  provenance.py --paper PAPER_DIR --json       # machine-readable
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
import tempfile

# The register vocabulary. `partial` and `abstract` are tolerated by
# research-depth-gate.py's DECLARED_RE but are not canonical, so they are
# reported separately rather than silently accepted or silently failed.
CANONICAL = {"full", "fetch-summary", "snippet", "unsearched"}
TOLERATED = {"partial", "abstract"}

ENTRY_RE = re.compile(r"^###\s+\[([^\]]+)\]", re.M)
DEPTH_RE = re.compile(r"\*\*Depth:?\*\*\s*(.+)$", re.I | re.M)
# Resolved the same way the gates resolve it when they write, or the stamp
# reads a ledger nothing has been writing to and reports a confident zero.
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _gatelog import ledger_path as _ledger_path
    LEDGER = _ledger_path()
except Exception:
    LEDGER = os.path.expanduser("~/.claude/hooks/gate-firings.jsonl")
TRANSCRIPTS = os.path.expanduser("~/.claude/projects")


def normalise_depth(raw: str) -> str:
    """First register token on the line, backticks and prose stripped.

    `**Depth:** `full` for the main text, snippet for the appendix` normalises
    to `full` — the leading declaration governs, which matches how
    research-depth-gate.py reads the same line. The trailing qualifier is
    deliberately not parsed: a depth that needs a sentence is a depth the
    author should split into two entries.
    """
    s = raw.strip().lstrip("`").lower()
    # Match the vocabulary FIRST, longest-first. Splitting on whitespace and
    # taking token[0] read `full-text greps against papers/text/...` as a label
    # `full-text` and reported an off-register violation against an entry that
    # declares `full` and then names its extraction — a false positive produced
    # entirely by the parser. Anchor on the known words instead of guessing at
    # where the label ends.
    for word in sorted(CANONICAL | TOLERATED, key=len, reverse=True):
        if s.startswith(word):
            return word
    tok = s.split("`")[0].split()[0] if s else ""
    return tok.strip("`*.,:;—-")


def read_depths(refs_path: str):
    """Return (entries, {bibkey: depth}, [bibkeys with no depth])."""
    if not os.path.exists(refs_path):
        return [], {}, []
    text = open(refs_path, encoding="utf-8", errors="replace").read()
    # Split on entry headers so a depth line is attributed to its own entry and
    # cannot be borrowed from the neighbour above it.
    parts = ENTRY_RE.split(text)
    keys, depths, missing = [], {}, []
    for i in range(1, len(parts), 2):
        key, body = parts[i], parts[i + 1]
        keys.append(key)
        m = DEPTH_RE.search(body)
        if not m:
            missing.append(key)
            continue
        d = normalise_depth(m.group(1))
        if d:
            depths[key] = d
        else:
            missing.append(key)
    return keys, depths, missing


TEMP_ROOTS = tuple(os.path.realpath(p) for p in
                   (tempfile.gettempdir(), "/tmp", "/var/folders", "/private/tmp",
                    "/private/var/folders"))


def is_synthetic(target: str) -> bool:
    """A firing provoked by a test fixture rather than by research.

    The ledger is append-only and shared, so it accumulates whatever fires:
    a test suite exercising the gates, a `.hooktest` probe, a canary commit from
    the git installer. None of those are evidence that a gate caught a claim,
    and on 2026-08-03 they were 177 of 220 rows — so a stamp that counted the
    file raw would have disclosed 220 firings where 43 had happened. That is a
    typed number wearing a derived number's clothes, in the one block of a paper
    whose entire warrant is that nothing in it was typed.

    The test is the target's location, not its name: research does not live in
    a temp directory. Excluded rows are counted and reported, never dropped
    quietly — an exclusion nobody can see is indistinguishable from a filter
    that is silently eating real firings.

    WHAT THIS CANNOT SEE, stated because it is load-bearing: a positive control
    replays real text through a gate to prove the gate catches it. The write is
    to a real path, so the ledger records it exactly as it would record a
    genuine catch, and nothing here can tell them apart. One row in the author's
    own ledger is that. `evidence/gate_evidence.py`, which reads transcripts
    rather than the ledger, does see the difference — the control announces
    itself in the surrounding session. Where the two instruments disagree,
    prefer the transcript: it has the context this file does not.
    """
    if not target:
        return False
    # A probe file lives in the repo, not in a temp dir, so location alone misses
    # it. All three of the ledger's non-temp rows for the two newest gates were
    # these: two `_gatetest.md` writes and one positive control replaying a
    # paper section the gate was built from. A gate verified against a fixture
    # has been verified; it has not caught anything.
    base = os.path.basename(target)
    if ".hooktest" in target or re.match(r"^_?(gate|hook)test", base):
        return True
    try:
        real = os.path.realpath(target)
    except Exception:
        real = target
    return any(real.startswith(r + os.sep) for r in TEMP_ROOTS)


def counts_as_evidence(row) -> bool:
    """Does this ledger row support a claim that a gate caught something?

    Two ways it does not, and they are not the same kind of test.

    `control` is the row saying so itself, set by `NULLIUS_CONTROL` and written
    by `tools/selftest.py`. It is the stronger signal and the ONLY one that
    reaches a positive control — real gate, real path, real text, replayed on
    purpose. No amount of looking at the path finds that.

    `is_synthetic` is us inferring it from where the write went. It catches the
    fixtures a test suite leaves behind, including every row written before the
    declaration existed, which is why both are kept rather than one replacing
    the other.
    """
    if not isinstance(row, dict):
        return False
    return not (row.get("control") or is_synthetic(row.get("target", "")))


def read_gate_firings():
    """Real firings from the append-only ledger, plus what was excluded.

    Returns `(rows, excluded)` or `(None, 0)`. An absent ledger is reported as
    such, never as zero — a missing instrument is not a clean result."""
    if not os.path.exists(LEDGER):
        return None, 0
    rows, excluded = [], 0
    for line in open(LEDGER, encoding="utf-8", errors="replace"):
        try:
            row = json.loads(line)
        except Exception:
            continue
        if not counts_as_evidence(row):
            excluded += 1
            continue
        rows.append(row)
    return rows, excluded


def read_models(project_globs):
    """Distinct model ids out of the session transcripts.

    Derived, not declared: the author cannot forget a model here, and cannot
    claim one that never ran.
    """
    seen = collections.Counter()
    for g in project_globs:
        for path in glob.glob(os.path.join(TRANSCRIPTS, g, "*.jsonl")):
            for line in open(path, errors="replace"):
                if '"model"' not in line:
                    continue
                for m in re.finditer(r'"model"\s*:\s*"([^"]+)"', line):
                    mid = m.group(1)
                    if mid and mid != "<synthetic>":
                        seen[mid] += 1
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True, help="paper directory")
    ap.add_argument("--project-glob", action="append", default=[],
                    help="transcript project dir glob (repeatable)")
    ap.add_argument("--check", action="store_true", help="gate mode; exit 1 on failure")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    refs = os.path.join(a.paper, "references.md")
    keys, depths, missing = read_depths(refs)
    counts = collections.Counter(depths.values())
    off_register = {k: v for k, v in depths.items()
                    if v not in CANONICAL and v not in TOLERATED}
    tolerated = {k: v for k, v in depths.items() if v in TOLERATED}
    firings, synthetic = read_gate_firings()
    models = read_models(a.project_glob or ["*"])

    report = {
        "bibliography": {
            "entries": len(keys),
            "declared": len(depths),
            "missing_depth": sorted(missing),
            "composition": dict(counts.most_common()),
            "off_register": off_register,
            "tolerated_noncanonical": tolerated,
        },
        "gates": {
            "ledger_present": firings is not None,
            "firings": len(firings) if firings is not None else None,
            "excluded_synthetic": synthetic,
            "by_gate": dict(collections.Counter(r.get("gate", "?") for r in firings).most_common())
                       if firings else {},
        },
        "models": dict(models.most_common()),
    }

    failures = []
    if missing:
        failures.append(f"G1 {len(missing)} of {len(keys)} bibliography entries declare no read depth")
    if off_register:
        vals = sorted(set(off_register.values()))
        failures.append(f"G2 off-register depth label(s) {vals} on {len(off_register)} entries; "
                        f"vocabulary is {sorted(CANONICAL)}")

    if a.json:
        report["failures"] = failures
        print(json.dumps(report, indent=2))
        return 1 if (a.check and failures) else 0

    print("=" * 72)
    print("PROVENANCE STAMP — every figure below is derived, none typed")
    print("=" * 72)
    print(f"\nBibliography    {len(keys)} entries, {len(depths)} with a declared read depth")
    for d, n in counts.most_common():
        mark = "" if d in CANONICAL else ("  (tolerated, non-canonical)" if d in TOLERATED
                                          else "  <-- OFF REGISTER")
        print(f"                  {n:4d}  {d}{mark}")
    if firings is None:
        print("\nGate firings    ledger absent — not zero, UNMEASURED")
    else:
        print(f"\nGate firings    {len(firings)} recorded")
        for g, n in collections.Counter(r.get('gate', '?') for r in firings).most_common():
            print(f"                  {n:4d}  {g}")
        if synthetic:
            print(f"                  ({synthetic} test/canary firings excluded — "
                  f"targets in a temp directory)")
    print(f"\nModels          {len(models)} distinct, from session transcripts")
    for mid, n in models.most_common(8):
        print(f"                  {mid}  ({n:,} records)")

    print("\n" + "=" * 72)
    if failures:
        print("BUILD GATE: FAIL")
        for f in failures:
            print(f"  ✗ {f}")
        if missing:
            print(f"\n  entries with no depth: {', '.join(sorted(missing)[:12])}"
                  + (" …" if len(missing) > 12 else ""))
        if off_register:
            for k, v in sorted(off_register.items())[:8]:
                print(f"  off-register: [{k}] declares `{v}`")
    else:
        print("BUILD GATE: PASS")
    print("=" * 72)
    return 1 if (a.check and failures) else 0


if __name__ == "__main__":
    sys.exit(main())
