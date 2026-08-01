#!/usr/bin/env python3
"""Build gate: internal vocabulary must not reach published prose.

THE INVERSE OF vocab-gate.py
    The write-time hook enforces that an identifier is DECLARED. This enforces
    that a declared *internal* identifier never ships. Same registry, opposite
    direction — and the second direction is the one a reader sees.

WHY IT SELF-MAINTAINS
    Namespaces in VOCAB.md carry a `scope`: program | local | external |
    cross-repo. `external` is the real world — GPT, UTF, PRM, WNUT — and
    belongs in a paper. Everything else is ours and does not. The gate reads
    that field rather than carrying a hardcoded blocklist, so declaring a new
    lane automatically extends it.

WHAT COUNTS AS PROSE
    Fenced code blocks and inline code spans are reported SEPARATELY, not
    merged into the prose count. a helper function named in a
    reproduction appendix is something a reader can go find; the same
    token in a sentence is a workflow leak. Conflating them produces a gate
    that cries wolf and gets deleted, which is the failure mode these gates
    are least allowed to have.

USAGE
    proseleak.py --sections DIR [--repo DIR] [--allow TOKEN]... [--check]
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import os
import re
import sys

# Internal process vocabulary — not identifiers, so not in VOCAB.md, but they
# are unmistakably workflow words. Each earned its place by appearing in a
# draft. Deliberately short: a long list here is a linter nobody trusts.
# Measured on AB-01's 15 sections at first run: 6 flagged, 2 real — 33%
# precision. Three entries were removed as a result, and the reason is the same
# for all three: THE WORD HAS A LEGITIMATE SCIENTIFIC SENSE.
#   `pre-reg`     — "the pre-registered directional prediction" is mainstream
#                   open-science vocabulary, not our workflow.
#   `the harness` — "the harness adds no spread of its own" is the SIMULATION
#                   harness. Nothing to do with the tooling.
#   `depth register` — will become public vocabulary if the standard ships, so
#                   gating on it would fight the thing we are trying to publish.
# What is left has no other reading in a paper: a codename, or a word that only
# means something to someone who has seen the repo.
PROCESS_WORDS = [
    "the lane", "this lane", "our shelf", "the shelf",
    "fetch-summary", "unsearched", "depth: full",
]

# Your project's internal codenames — tool names, service names, anything that
# means something only to someone who has seen your repo. Left empty on purpose:
# these are the highest-signal leaks and nobody else's list will match yours.
#   PROJECT_CODENAMES = ["yourtool", "yourservice"]
PROJECT_CODENAMES: list[str] = []
PROCESS_WORDS += PROJECT_CODENAMES

FENCE_RE = re.compile(r"^\s*```")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
INTERNAL_SCOPES = {"program", "local", "cross-repo"}


def load_vocab(repo):
    """Import the repo's own vocab.py and read its registry. Returns
    (internal_prefixes, external_prefixes, lane_slugs)."""
    vp = os.path.join(repo, "vocab.py")
    if not os.path.isfile(vp):
        return set(), set(), set()
    spec = importlib.util.spec_from_file_location("_vocab", vp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    namespaces, _defined, lanes = mod.load_registry(repo)
    internal, external = set(), set()
    for prefix, ns in namespaces.items():
        (internal if ns.scope in INTERNAL_SCOPES else external).add(prefix)
    return internal, external, set(lanes)


def scan_file(path, id_re, lane_re, allow):
    """Return (prose_hits, code_hits); each is [(lineno, token, line)]."""
    prose, code = [], []
    in_fence = False
    for n, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        bucket = code if in_fence else prose
        # Inline code is code even on a prose line.
        stripped = INLINE_CODE_RE.sub(" ", line)
        inline_only = INLINE_CODE_RE.findall(line)

        for target, text in ((bucket, line if in_fence else stripped),
                             (code, " ".join(inline_only) if not in_fence else "")):
            if not text:
                continue
            for rx in (r for r in (id_re, lane_re) if r):
                for m in rx.finditer(text):
                    tok = m.group(0)
                    if tok.lower() in allow:
                        continue
                    target.append((n, tok, line.rstrip()))
            low = text.lower()
            for w in PROCESS_WORDS:
                if w in allow:
                    continue
                start = 0
                while (i := low.find(w, start)) != -1:
                    target.append((n, w, line.rstrip()))
                    start = i + len(w)
    return prose, code


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", required=True, help="dir of published .md")
    ap.add_argument("--repo", default="", help="repo root holding VOCAB.md/vocab.py")
    ap.add_argument("--allow", action="append", default=[],
                    help="token to permit (repeatable)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    repo = a.repo or os.path.abspath(os.path.join(a.sections, *[".."] * 6))
    internal, external, lanes = load_vocab(repo)
    allow = {t.lower() for t in a.allow}

    id_re = lane_re = None
    if internal:
        id_re = re.compile(r"(?<![\w/-])(?:%s)-\d{1,3}[a-z]?(?![\w-])"
                           % "|".join(sorted(internal, key=len, reverse=True)))
    if lanes:
        lane_re = re.compile(r"(?<![\w/-])(?:%s)/[TGDQR]-\d{1,3}[a-z]?(?![\w-])"
                             % "|".join(re.escape(s) for s in sorted(lanes, key=len, reverse=True)))

    print(f"registry: {len(internal)} internal namespaces, "
          f"{len(external)} external (allowed), {len(lanes)} lanes")
    if external:
        print(f"  external, permitted in prose: {' '.join(sorted(external))}")

    files = sorted(glob.glob(os.path.join(a.sections, "*.md")))
    tot_prose = tot_code = 0
    for f in files:
        prose, code = scan_file(f, id_re, lane_re, allow)
        tot_prose += len(prose)
        tot_code += len(code)
        if not prose and not code:
            continue
        print(f"\n{os.path.relpath(f, a.sections)}")
        for n, tok, line in prose:
            print(f"  PROSE  :{n}  {tok!r}")
            print(f"           {line.strip()[:96]}")
        for n, tok, line in code:
            print(f"  code   :{n}  {tok!r}  (in code span/block — review, not blocked)")

    print(f"\n{'=' * 66}")
    print(f"scanned {len(files)} files — {tot_prose} prose leaks, {tot_code} in code")
    print("BUILD GATE: " + ("FAIL" if tot_prose else "PASS"))
    print("=" * 66)
    return 1 if (a.check and tot_prose) else 0


if __name__ == "__main__":
    sys.exit(main())
