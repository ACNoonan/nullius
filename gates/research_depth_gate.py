#!/usr/bin/env python3
"""PreToolUse gate: a `depth: full` claim must point at an artifact that exists.

WHY (2026-07-27)
    Our own note saying a paper was read in full is a CLAIM, not evidence. It has
    been wrong repeatedly, always in the direction that made our position look
    stronger:
      - EL-pilot gated on a published accuracy figure computed under a metric
        nobody had read (§4.4), and pinned exact-match scoring against it.
      - A `fetch-summary` of Kotte 2606.29054 supplied two false premises to a
        research agent, which then reasoned from them.
      - An MSCE intake marked `full` by a subagent got three things wrong, all
        of which made our critique look better than it was.
    So the register header may say `full` only where an extracted text or PDF is
    on disk and can be grepped.

WHAT THIS BLOCKS
    (1) A Write/Edit to a research document that declares depth `full` without any
    resolvable path to the extraction on the same line or the two following it.

    (2) A `depth: full` claim whose artifact IS on disk but whose text layer is
    known to delete mathematics, unless the claim says which channel the maths
    came from. Nothing else. The instrument-verification gate belongs in code —
    a text hook cannot check an instrument — and is out of scope here.

WHY (2) — ARTIFACT PRESENCE IS NOT ARTIFACT FIDELITY
    The original gate proved a file exists. It cannot tell whether that file says
    what the page says. Sweeping 312 shelf PDFs found 48 maths-unsafe, and the
    failure is silent: Patton (2013), born-digital LaTeX, renders `C(γ*)` as
    `C ( )` and `δ_t` as `t` — a different variable that also exists in the paper,
    so the corrupted line stays syntactically valid. Rychlik (1994) lost a
    denominator worth 901× at the operating point it was being read for. Six shelf
    `.pdf` files were not PDFs at all (Cloudflare/JSTOR block pages), one with an
    85 KB `.txt` beside it — so an artifact can exist, be non-empty, be the WRONG
    DOCUMENT, and pass check (1).

    This is a flag, not a wall, and deliberately so: a paper can be read in full
    and understood correctly from a lossy text layer, as long as no equation was
    taken from it. What the gate demands is that the claim SAY so, using one of:

        maths: image    equations read off rendered page images
                        (`tools/extraction_integrity.py page <stem> <page>`)
        maths: unread   prose only; no equation, constant or bound from this paper
                        has entered the work
        maths: n/a      the paper contains no mathematics

    The flag is checkable in the weak sense the rest of this hook is checkable —
    it separates a specific claim from a bare one, and cannot verify that anyone
    looked. The index it consults is written by `tools/extraction_integrity.py
    sweep`; with no index, this half is silently inert.

WHAT THIS DELIBERATELY DOES NOT DO
    It cannot check that the paper was actually read, only that the artifact the
    claim rests on exists. That is the honest limit of a text hook: it enforces
    presence, never quality. Quality is the skill's job (your project's source-intake checklist).

FAIL-OPEN
    Any internal error, unreadable input, or unexpected shape => allow. A hook
    that blocks work because the hook itself broke would be retired within a day,
    and then nothing is enforced. Silence on error is the correct trade.
"""
from __future__ import annotations

import json
import os
import re
import sys

# Only trees that opted in. See _config.py: a repo is governed iff it holds a
# `.nullius.toml` at its root. Empty tuple => this gate does nothing,
# which is the correct behaviour outside an opted-in repo.
try:
    from _config import roots_for
except Exception:                                # never let config break a gate
    def roots_for(_path):
        return ()

# Resolved once per write, in main(), from the target path. It is a MODULE global
# rather than a parameter threaded through six helpers because the helpers are
# also called by the test suite and the git adapter.
#
# It used to be neither: helpers called `roots_for(path)` where no `path` was in
# scope, which raised NameError inside main()'s try and FAILED OPEN — silently, on
# exactly the two shapes this gate exists for. A claim naming a bibliography key
# (`### [smith2020]`) or an arXiv id was never gated at all, because those are the
# branches that reach the shelf lookups; only the bare `depth: full` with no source
# named was still caught. Caught 2026-08-02 by probing a real bibliography entry
# through the hook, not by the suite, which only ever fed it the bare shape.
ROOTS: tuple = ()

# Documents where a depth register is meaningful. Scratch .py files are exempt.
DOC_RE = re.compile(r"\.(md|txt)$", re.I)

# The reading shelf is the artifact STORE. Its index necessarily talks about depth
# claims in the third person ("eighteen papers marked `depth: full`"), and gating
# the registry of artifacts on having artifacts is circular. Exempt.
EXEMPT_RE = re.compile(r"/papers/", re.I)

# `depth: full`, `**depth** | `full``, `- **Depth on X: `full`.**` and friends.
#
# The trailing delimiter is a LOOKAHEAD and `$` is an alternative: this once required
# a character AFTER `full`, so a line ending exactly at `**Depth:** full` — the most
# natural way to write it — was never gated at all. Found by a gate test, not in use.
DEPTH_RE = re.compile(r"depth[^\n]{0,80}?[`'\"*\s|:]full(?=[`'\"*\s.,)]|$)", re.I)

# The DECLARED label — the first vocabulary word after "Depth". Gating on the mere
# presence of "full" anywhere in the line flagged
#     "**Depth:** partial — Preface/TOC/Introduction read IN FULL via an excerpt; the body…"
# which declares `partial` and is exactly the honest self-limiting we want. Only a line
# that actually CLAIMS full depth is gated.
DECLARED_RE = re.compile(
    r"depth\W{0,12}(full|partial|fetch-summary|snippet|unsearched|abstract)\b", re.I)

# Anything that looks like it names a file or directory on disk. The trailing-slash
# alternative matters: an extraction is often cited as a folder (`sources/`), and
# requiring a file extension rejected those even when the folder was really there.
PATH_RE = re.compile(
    r"[~./\w-]*/[\w./-]+\.(?:pdf|txt|md|jsonl?|tex|html)"      # a file
    r"|`[~./\w-]*[\w-]/`"                                       # a backticked dir
    r"|(?<![\w/])[\w-]+/(?![\w.])",                             # a bare dir token
    re.I,
)

# Phrases that assert the read happened in a CHECKABLE way. Any of these alongside
# the claim is enough.
#
# The second group was added 2026-07-27 and is a deliberate LOOSENING, recorded as
# such. The first group assumes an arXiv-shaped world: a PDF, a text extraction, a
# line count. Paper 2's reference list is not that world — it cites Biometrika, JRSS-B,
# ReStud, JSTOR-only 1993 survey-statistics work. Those reads really happened (one
# paper was purchased; a JSTOR scan was OCR'd end to end) and produced attestations
# far more specific than a bare `depth: full`:
#
#     "complete scanned article read 2026-07-27, all 18 pages, quote verified in place"
#     "JSTOR page scans OCR'd and read end to end, 26pp"
#     "purchased and read 2026-07-27, all 20pp. Eq. (9) verified in place"
#
# Blocking those while passing "extracted with pdftotext" would enforce a FILE FORMAT,
# not a standard of evidence. Be honest about the cost: a page count can be fabricated
# as easily as a tool name, so this gate has never verified that anyone read anything —
# it separates a specific, checkable claim from a bare one, and that is all it ever did.
# The strongest form is still an extraction on disk under `papers/text/`, which is what
# the arXiv path gets you for free and the paywalled path does not.
EVIDENCE_RE = re.compile(
    r"pdftotext|arxiv\.org/pdf|grepped|cloned|extracted with|"
    r"\d{3,}\s*(?:lines|words)|full text file"
    r"|\ball\s+\d{1,4}\s*(?:pages|pp)\b|\b\d{1,4}\s*pp\b|pp\.\s*\d"
    r"|verified in place|read end to end|OCR",
    re.I,
)


# arXiv-shaped identifiers, so a claim naming a paper can be checked against the
# shelf directly instead of demanding that the prose also spell out a path.
ARXIV_RE = re.compile(r"\b(\d{4}\.\d{4,5})(?:v\d+)?\b")

_SHELF: set[str] | None = None


def shelf_ids() -> set[str]:
    """arXiv ids of every PDF/text on the reading shelves. Built once, cached."""
    global _SHELF
    if _SHELF is None:
        ids: set[str] = set()
        for root in ROOTS:
            for sub in ("papers", "papers/pdfs", "sources"):
                d = os.path.join(root, sub)
                if not os.path.isdir(d):
                    continue
                try:
                    for name in os.listdir(d):
                        ids.update(m.group(1) for m in ARXIV_RE.finditer(name))
                except OSError:
                    pass
        _SHELF = ids
    return _SHELF


# --- maths-fidelity side -----------------------------------------------------
# Written by `tools/extraction_integrity.py sweep`. Absent or unreadable => this
# half of the gate is silently inert, which is the correct trade: a fidelity check
# that blocks work because its index was never built would be disabled in a day.
#
# Searched in this order under the governing root, first hit wins. `.nullius/` is
# the default the sweeper writes to; the other two are for projects that keep the
# shelf and its index together.
INDEX_PATHS = (
    os.path.join(".nullius", "extraction_integrity.json"),
    os.path.join("papers", "extraction_integrity.json"),
    "extraction_integrity.json",
)

_UNSAFE: dict[str, str] | None = None

MATHS_FLAG_RE = re.compile(r"maths?\W{0,4}(image|unread|n/?a)\b", re.I)


def unsafe_index() -> dict[str, str]:
    """{identifier: class} for every maths-unsafe artifact, keyed several ways.

    Keyed by arXiv id, by PDF stem and by text-extraction stem, because a claim may
    name any of the three and the gate should not care which.
    """
    global _UNSAFE
    if _UNSAFE is None:
        idx: dict[str, str] = {}
        for root in ROOTS:
            for rel in INDEX_PATHS:
                try:
                    with open(os.path.join(root, rel)) as fh:
                        rows = json.load(fh)
                except Exception:
                    continue
                if not isinstance(rows, list):
                    continue
                for r in rows:
                    if not isinstance(r, dict) or not r.get("maths_unsafe"):
                        continue
                    cls = r.get("cls", "maths-unsafe")
                    pdf = r.get("pdf", "")
                    stem = pdf[:-4] if pdf.endswith(".pdf") else pdf
                    for key in (stem, re.sub(r"^arxiv-", "", stem), r.get("text") or ""):
                        if key:
                            idx[key.lower().removesuffix(".txt")] = cls
                    for m in ARXIV_RE.finditer(pdf):
                        idx[m.group(1)] = cls
                break                      # first index found under this root wins
        _UNSAFE = idx
    return _UNSAFE


def unsafe_in(window: str) -> tuple[str, str] | None:
    """The first maths-unsafe artifact this claim names, if any."""
    idx = unsafe_index()
    if not idx:
        return None
    for m in ARXIV_RE.finditer(window):
        if m.group(1) in idx:
            return m.group(1), idx[m.group(1)]
    # Path- and bibkey-shaped mentions: match on the basename stem.
    for m in re.finditer(r"[\w.-]+(?=\.(?:pdf|txt)\b)|\[([a-z][a-z-]+\d{4}[a-z]?)\]", window):
        tok = (m.group(1) or m.group(0)).lower()
        if tok in idx:
            return tok, idx[tok]
    return None


def resolves(path: str, doc_dir: str) -> bool:
    """True if the referenced path exists, absolute or relative to the document."""
    p = os.path.expanduser(path)
    if os.path.exists(p):
        return True
    return os.path.exists(os.path.join(doc_dir, p.lstrip("./")))


# A bibliography entry is headed by its citation key: `### [tudball2022] Tudball...`.
# Journal-only papers have no arXiv id, so the shelf is keyed by that bibkey instead:
# an extraction saved as `papers/text/<bibkey>.txt` backs the claim.
BIBKEY_RE = re.compile(r"\[([a-z][a-z-]+\d{4}[a-z]?)\]")


def bibkey_extracted(window: str) -> bool:
    """True if a citation key in the window has an extraction saved under papers/text/."""
    for m in BIBKEY_RE.finditer(window):
        for root in ROOTS:
            for ext in (".txt", ".pdf", ".md"):
                if os.path.exists(os.path.join(root, "papers", "text", m.group(1) + ext)):
                    return True
    return False


def papers_on_shelf(window: str) -> bool:
    """True if the claim names arXiv ids and EVERY one of them is on the shelf.

    Every, not any: `depth: full` over four papers is four claims, and three
    artifacts out of four is exactly the partial read this gate exists to catch.
    """
    ids = {m.group(1) for m in ARXIV_RE.finditer(window)}
    return bool(ids) and ids <= shelf_ids()


# The depth vocabulary itself. A line listing two or more of these is DEFINING the
# register ("Depth ∈ {full, fetch-summary, snippet, unsearched}"), not claiming a
# depth, and must not be gated — that was a false positive on the ESCO scout note.
VOCAB = ("full", "fetch-summary", "snippet", "unsearched")


# A line that DISCLAIMS a full read ("Zero papers read in full", "not read in
# full", "no full read yet") is honest reporting and is the behaviour we want, not
# a claim to gate. Matching it was a false positive on the swarm-moe intake note.
NEGATED_RE = re.compile(
    r"(?:zero|none|no|not|never|without|un-?read|yet to be|pending)\b[^.\n]{0,40}full"
    r"|full[^.\n]{0,30}\b(?:not|never|pending|outstanding|missing)\b"
    # "Depth note: this is a *grep of the full text*" states a LOWER depth in prose
    # rather than by vocabulary word. Self-limitation is the behaviour we want; gating
    # it teaches people to stop writing the caveat.
    r"|\bgrep(?:ped)?\s+(?:of|over|across)\s+the\s+full",
    re.I,
)


def is_vocabulary_definition(line: str) -> bool:
    low = line.lower()
    return sum(term in low for term in VOCAB) >= 2 or "∈" in line


def offending_claims(text: str, doc_dir: str) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Depth-full claims with no artifact, and those resting on a lossy artifact.

    Returns (missing_artifact, unflagged_maths). Both empty = allow. A claim can only
    appear in one: if the artifact is absent that is the first thing to fix, and
    asking for a maths flag on a file that is not there would be noise.
    """
    lines = text.splitlines()
    bad: list[str] = []
    lossy: list[tuple[str, str, str]] = []
    for i, line in enumerate(lines):
        declared = DECLARED_RE.search(line)
        if declared and declared.group(1).lower() != "full":
            continue                      # the line declares a LOWER depth; nothing to gate
        if (not DEPTH_RE.search(line)
                or is_vocabulary_definition(line)
                or NEGATED_RE.search(line)):
            continue
        # Look BACKWARD as well as forward. A bibliography entry states its key
        # and URL/DOI first and the depth last:
        #     ### [tudball2022] Tudball, M.J., ...
        #     **URL / DOI:** ...
        #     **Contribution:** ...
        #     **Why we cite:** ...
        #     **Depth:** full — ...
        # so a forward-only window called a well-formed reference list
        # non-compliant. Six back covers that shape with one wrapped line to
        # spare — measured against the real file, not guessed; at four it was
        # off by one and rejected an entry whose extraction was on disk. Two
        # forward covers a wrapped register row.
        window = "\n".join(lines[max(0, i - 6):i + 3])
        backed = (EVIDENCE_RE.search(window)
                  or papers_on_shelf(window) or bibkey_extracted(window)
                  or any(resolves(m.group(0), doc_dir) for m in PATH_RE.finditer(window)))
        if not backed:
            bad.append(line.strip()[:160])
            continue
        hit = unsafe_in(window)
        if hit and not MATHS_FLAG_RE.search(window):
            lossy.append((line.strip()[:140], hit[0], hit[1]))
    return bad, lossy


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0                                    # fail-open

    try:
        tool = payload.get("tool_name", "")
        if tool not in ("Write", "Edit"):
            return 0

        ti = payload.get("tool_input", {}) or {}
        path = ti.get("file_path", "")
        if not path or not DOC_RE.search(path) or EXEMPT_RE.search(path):
            return 0
        global ROOTS
        ROOTS = roots_for(path)
        if not any(os.path.abspath(path).startswith(r) for r in ROOTS):
            return 0

        text = ti.get("content") or ti.get("new_string") or ""
        if not text:
            return 0

        bad, lossy = offending_claims(text, os.path.dirname(os.path.abspath(path)))
        if not bad and not lossy:
            return 0

        if not bad:
            claims = "\n".join(f"    {c}\n      └─ {who} is {cls}" for c, who, cls in lossy[:3])
            reason = (
                "BLOCKED — a `depth: full` claim resting on an artifact whose text layer "
                "is known to lose mathematics.\n\n"
                f"In {os.path.basename(path)}:\n{claims}\n\n"
                "The file is on disk; that is not in question. What is in question is "
                "whether it says what the page says. A born-digital LaTeX paper can "
                "extract `C(γ*)` as `C ( )` and `δ_t` as `t` — still syntactically "
                "valid, silently wrong — and a `.pdf` that is really a block page is "
                "an artifact that is not the paper at all.\n\n"
                "To proceed, add ONE of these to the claim:\n"
                "  maths: image    — equations read off rendered page images\n"
                "                    (tools/extraction_integrity.py page <stem> <page>)\n"
                "  maths: unread   — prose only; no equation, constant or bound from this\n"
                "                    paper has entered the work\n"
                "  maths: n/a      — the paper contains no mathematics\n\n"
                "Full details for this paper: tools/extraction_integrity.py check <stem>\n"
                "Do NOT re-run pdftotext in another mode. Every mode reads the same layer "
                "and agrees with the error."
            )
            try:
                from _gatelog import record as _rec
                _rec("research-depth-gate/maths", reason, path)
            except Exception:
                pass
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}))
            return 0

        claims = "\n".join(f"    {c}" for c in bad[:3])
        reason = (
            "BLOCKED — a `depth: full` claim with no artifact behind it.\n\n"
            f"In {os.path.basename(path)}:\n{claims}\n\n"
            "Our own note saying a paper was read in full is a claim, not evidence, "
            "and it has been wrong before in the direction that flattered us.\n\n"
            "To proceed, do ONE of:\n"
            "  1. Name the extraction on the same line or the next two — a path that "
            "exists (e.g. `papers/2306.05836.txt`), or how it was produced "
            "(`pdftotext`, `arxiv.org/pdf/...`, `grepped the full text`, `1,718 lines`).\n"
            "  2. Downgrade the claim to `fetch-summary`, `snippet` or `unsearched` — "
            "which is the honest label if the artifact is not on disk.\n"
            "  3. Do the read first. A Sonnet search subagent can fetch and extract it; "
            "see your project's source-intake checklist for the six-item deliverable."
        )
        try:                                   # firing ledger; never fatal
            from _gatelog import record as _rec
            _l = locals()
            _rec("research-depth-gate", _l.get("reason", ""),
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
        return 0                                    # fail-open, always


if __name__ == "__main__":
    sys.exit(main())
