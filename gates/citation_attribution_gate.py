#!/usr/bin/env python3
"""PreToolUse gate: a bibliography entry's author must match the artifact on disk.

WHY (2026-07-29)
    Two citation keys in one session named authors who do not exist on the papers
    they pointed at: `[zhang2026grpo]` for arXiv 2603.01162, which is Zhou et al.,
    and `[qu2026]` for 2605.21125, which is He et al. Both surnames were inferred
    from context rather than read off the paper. The AB-01 changelog rates this
    "cut immediately" severity — a wrong citation misattributes credit and sends a
    reader to the wrong work — and it is the single hardest error class to see in
    review, because a plausible surname reads as a fact.

WHY THE OBVIOUS RULE DOES NOT WORK (measured, not assumed)
    The tempting check is "does the claimed surname appear in the paper at all?"
    It fails on the exact error it exists to catch: **"Zhang" occurs 52 times in
    2603.01162** — common surnames are all over a bibliography. Scoped to the
    first HEAD_LINES lines, the title/author block, "Zhang" occurs 0 times and
    "Zhou" once. So the check must be block-scoped, and this docstring records the
    negative control because a gate whose rule was never tested against a real
    failure is decoration.

WHAT THIS BLOCKS
    A Write/Edit that introduces or changes a `### [key] Author, I. YEAR. Title.`
    bibliography entry where one of these is PROVABLY wrong:
      1. KEY/AUTHOR   the key's leading alphabetic run disagrees with the first
                      author's surname (pure string check, needs no artifact).
      2. AUTHOR/PAPER the entry names an artifact on disk, and the first author's
                      surname does not appear in that artifact's author block.
      3. TITLE/PAPER  fewer than TITLE_MIN_FRAC of the title's significant words
                      appear in that artifact's head — i.e. the key points at a
                      different paper than the entry describes.

WHAT THIS DELIBERATELY DOES NOT DO
    No artifact on disk => no author/title check, allowed. Paywalled and
    `[not read]` entries are legitimate and are the depth gate's business, not
    this one. It cannot verify a full author LIST, only the first author, and it
    cannot tell a genuine transliteration variant from an error — it reports what
    the author block actually contains and lets a human decide. It never checks
    whether the paper was read; presence is not comprehension.

FAIL-OPEN
    Any internal error, unreadable input or unexpected shape => allow. A hook that
    blocks work because the hook broke gets retired within a day, after which
    nothing is enforced.

STANDALONE AUDIT
    python3 citation-attribution-gate.py --audit path/to/references.md
    Checks every entry in the file and exits 1 if any fails. Use this to sweep a
    bibliography that predates the gate.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

# Opted-in trees only; resolved per-write in main(). See _config.py.
try:
    from _config import roots_for
except Exception:                                # never let config break a gate
    def roots_for(_path):
        return ()

ROOTS: tuple = ()          # set by main() once the target path is known

HEAD_LINES = 80          # title/author block; 2603.01162 needs ~17, arXiv stamps interleave
TITLE_MIN_FRAC = 0.60    # fraction of significant title words that must appear
MIN_TITLE_WORDS = 3      # below this, skip the title check as unreliable

# `### [key] Surname, I., Surname2, I. YEAR. Title.`
ENTRY_RE = re.compile(
    r"^###\s*\[(?P<key>[A-Za-z][A-Za-z0-9_]*)\]\s*(?P<rest>.+?)\s*$", re.M)
# artifact path in a **Depth:** line, in backticks
ARTIFACT_RE = re.compile(r"`([^`]*?(?:papers/text|papers/pdfs)/[^`]+?)`")
# corporate / non-personal authors: no "Surname, I." shape
PERSONAL_RE = re.compile(r"^(?P<surname>[A-Z][\w'’\-]+),\s*(?P<initials>[A-Z]\.)")


def deaccent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", deaccent(s).lower())


def find_artifact(block: str) -> str | None:
    """Resolve the first artifact path mentioned in an entry block."""
    m = ARTIFACT_RE.search(block)
    if not m:
        return None
    rel = m.group(1).strip()
    cands = [rel]
    for root in ROOTS:
        cands.append(os.path.join(root, rel))
        # entries are written relative to the repo root, but a paper dir may nest
        cands.append(os.path.join(root, "papers", os.path.basename(rel)))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def head_of(path: str) -> str | None:
    """First HEAD_LINES lines of the extracted text, or None if unusable."""
    if path.endswith(".pdf"):
        txt = re.sub(r"/pdfs/", "/text/", path)
        txt = re.sub(r"\.pdf$", ".txt", txt)
        if not os.path.isfile(txt):
            return None
        path = txt
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = [next(fh, "") for _ in range(HEAD_LINES)]
    except Exception:
        return None
    head = "".join(lines)
    return head if head.strip() else None


def capitalised_words(head: str) -> list[str]:
    """Plausible name tokens in the author block, for an actionable message."""
    seen, out = set(), []
    # Strip trailing affiliation digits: pdftotext renders "Zhou^1" as "Zhou1".
    for w in re.findall(r"\b([A-Z][a-z]{1,})\d*", head):
        if w.lower() in {"the", "and", "abstract", "introduction", "we", "this",
                         "under", "with", "for", "our", "its", "policy", "group"}:
            continue
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:18]


def check_entry(key: str, rest: str, block: str) -> list[str]:
    """Return a list of failure strings; empty means pass."""
    fails: list[str] = []

    pm = PERSONAL_RE.match(rest)
    if not pm:
        return fails                      # corporate/doc author: nothing to check
    surname = pm.group("surname")

    # -- check 1: key prefix vs first-author surname (no artifact needed) -------
    # ADVISORY ONLY, deliberately. Keying by method name is an established
    # convention in this bibliography — [traq2023], [conu2024], [lofreecp2024],
    # [hibayes2025], [pfwcp2026] are all TRAQ/ConU/LoFreeCP/HiBayES/PF-WCP, not
    # author names. Auditing 76 entries gave this rule 5 false positives and zero
    # unique catches: both real 2026-07-29 errors were independently caught by the
    # AUTHOR/PAPER check below. So it goes to stderr and never blocks.
    key_prefix = re.match(r"^[a-zA-Z]+", key).group(0)
    ns, nk = norm(surname), norm(key_prefix)
    if nk and ns and not (ns.startswith(nk) or nk.startswith(ns)):
        print(f"  note [{key}]: key begins '{key_prefix}' but first author is "
              f"'{surname}' — fine if the key is a method name, an error if it "
              f"was meant to be the author.", file=sys.stderr)

    art = find_artifact(block)
    if not art:
        return fails                      # no artifact => author/title unverifiable here
    head = head_of(art)
    if head is None:
        return fails                      # unreadable => fail open

    # -- check 2: surname must appear in the author block ----------------------
    # Two extraction realities, each found by a control that blocked a CORRECT entry:
    #  * Right edge is (?![A-Za-z]) not \b — pdftotext renders affiliation
    #    superscripts as digits, so the block reads "Hongyi Zhou1,∗" and
    #    r"\bZhou\b" fails because the digit is a word character.
    #  * Titlecase OR ALLCAPS — old journal scans set the byline in caps
    #    ("By Y. VARDI", Ann. Statist. 1985). Matching case-INsensitively instead
    #    would be wrong: it makes short surnames like "He" match the pronoun.
    sn = deaccent(surname)
    pat = rf"\b(?:{re.escape(sn)}|{re.escape(sn.upper())})(?![A-Za-z])"
    if not re.search(pat, deaccent(head)):
        names = ", ".join(capitalised_words(head)) or "(none parsed)"
        fails.append(
            f"AUTHOR/PAPER: '{surname}' does not appear in the first {HEAD_LINES} "
            f"lines of {os.path.basename(art)}. Names actually in that block: "
            f"{names}. NOTE: a surname elsewhere in the file is not evidence — "
            f"'Zhang' occurs 52x in 2603.01162's bibliography and 0x in its "
            f"author block, which is the error this gate exists to catch.")

    # -- check 3: title must match the artifact -------------------------------
    tm = re.search(r"\b(?:19|20|26)\d{2}[a-z]?\.\s*(?P<title>.+)$", rest)
    if tm:
        words = [w for w in re.findall(r"[A-Za-z]{4,}", tm.group("title"))]
        if len(words) >= MIN_TITLE_WORDS:
            hl = deaccent(head).lower()
            hit = sum(1 for w in words if deaccent(w).lower() in hl)
            frac = hit / len(words)
            if frac < TITLE_MIN_FRAC:
                fails.append(
                    f"TITLE/PAPER: only {hit}/{len(words)} ({frac:.0%}) of the "
                    f"title's significant words appear in "
                    f"{os.path.basename(art)}'s head — below the {TITLE_MIN_FRAC:.0%} "
                    f"floor. The key may point at a different paper than the entry "
                    f"describes.")
    return fails


def entries_in(text: str) -> list[tuple[str, str, str]]:
    """(key, rest, block) for each entry; block runs to the next entry or EOF."""
    ms = list(ENTRY_RE.finditer(text))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append((m.group("key"), m.group("rest"), text[m.start():end]))
    return out


def audit(path: str) -> int:
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except Exception as e:
        print(f"cannot read {path}: {e}")
        return 0
    ents = entries_in(text)
    bad = 0
    for key, rest, block in ents:
        fails = check_entry(key, rest, block)
        if fails:
            bad += 1
            print(f"\n[{key}]")
            for f in fails:
                print(f"  ✗ {f}")
    checked = sum(1 for k, r, b in ents if PERSONAL_RE.match(r))
    withart = sum(1 for k, r, b in ents if PERSONAL_RE.match(r) and find_artifact(b))
    print(f"\n{len(ents)} entries, {checked} with a personal first author, "
          f"{withart} with a resolvable artifact (author+title checked), "
          f"{bad} failing.")
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
    if os.path.basename(path) != "references.md":
        return 0

    # Only inspect what this call introduces.
    text = ti.get("content") or ti.get("new_string") or ""
    if not text.strip():
        return 0

    all_fails: list[str] = []
    for key, rest, block in entries_in(text):
        all_fails += check_entry(key, rest, block)

    if all_fails:
        reason = ("BLOCKED — a bibliography entry contradicts the paper on disk.\n\n"
                  + "\n\n".join(f"  • {f}" for f in all_fails)
                  + "\n\nA plausible surname reads as a fact, which is why this is "
                    "gated in code rather than left to review. Open the artifact's "
                    "first lines and copy the names from it.")
        try:                                   # firing ledger; never fatal
            from _gatelog import record as _rec
            _l = locals()
            _rec("citation-attribution-gate", _l.get("reason", ""),
                 _l.get("path") or _l.get("file_path") or _l.get("target") or "")
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
