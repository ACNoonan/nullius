#!/usr/bin/env python3
"""PreToolUse gate: an effective sample size must name the marginal it is under.

WHY (2026-07-30)
    An n_eff is not a property of a benchmark. It is a property of a benchmark
    UNDER A STATED MARGINAL, and the same data gives wildly different answers:
    SWE-bench Verified's 500 instances are 500 under a per-item reading and 96.5
    under a per-source one. A figure written without its marginal is not a weaker
    result, it is not a result.

    Three claims shipped into the paper without one, and every one was caught by
    Adam on read-back rather than by any gate:

      "the 500 instances ... carry the weight of about a hundred"   (per-source)
      "441 published outcomes are worth about 104 independent ones"  (per-source)
      "the five mandated runs are worth about 100 ... not 400"       (per-item)

    Each reads as intrinsic. None was. The paper had the correct position written
    down days earlier -- "the claim here is about what each marginal is worth on
    this data" -- and the new results were framed de novo instead of being routed
    through it. That is the behaviour this blocks: a fresh measurement inventing
    its own frame while the standing position sits unread in a long document.

WHAT THIS BLOCKS
    A Write/Edit whose new content contains an effective-sample-size or
    information-content CLAIM in a paragraph that names no marginal, in a .md
    under a research repo. Claim patterns are deliberately narrow: an n_eff
    assignment, a design effect with a number attached, or the English forms
    ("carry the weight of", "are worth about N independent", "worth N of M").

WHAT IT DELIBERATELY DOES NOT DO
    It does not fire on a bare mention of n_eff or DEFF -- definitions, formulae,
    method text and table headers must stay writable without ceremony. It does
    not check that the marginal named is the RIGHT one; no text hook can. And it
    says nothing about evaluative language ("should worry", "sound design"),
    which needs an estimand rather than a marginal and is not mechanisable --
    that half stays a human check in your project's standing-positions doc.

FAIL-OPEN
    Any internal error, unreadable input, non-markdown target => allow.
"""
from __future__ import annotations

import json
import re
import sys

# A CLAIM about information content, not a mere mention.
CLAIM = re.compile(
    r"(n_?\\?text\{?eff\}?\s*(?:=|is|of)\s*[\d.,]"          # n_eff = 96.5 / n_eff is 812
    r"|n_?\\?text\{?eff\}?\s*(?:=|is)\s*\*?\*?[\d.,]"
    r"|carry(?:ing)?\s+the\s+(?:weight|information)\s+of"    # "carry the weight of about a hundred"
    r"|(?:are|is)\s+worth\s+(?:about\s+)?[\d.,]+\s+independent"
    r"|worth\s+(?:about\s+)?[\d.,]+\s+of\s+[\d.,]+"
    r"|design\s+effect\s+(?:is|of)\s+[\d.]+)",
    re.I,
)

# Naming the marginal. Any of these in the same paragraph discharges the gate.
MARGINAL = re.compile(
    r"(per[-\s]run|per[-\s]item|per[-\s]source|per[-\s]task|per[-\s]question|per[-\s]prefix"
    r"|per[-\s]repositor|marginal|resampl|estimand)",
    re.I,
)

# Formula / definition context: allowed to state n_eff without a marginal.
DEFN = re.compile(
    r"(=\s*n\s*/|\\frac|defin|formula|estimator|Usage:|```|\| *n_?\\?text\{?eff"
    # Synthetic validation has no benchmark and therefore no marginal to name: a design
    # effect computed on a simulated copula is a property of the simulation, full stop.
    r"|copula|simulat|synthetic|Monte Carlo|negative control|permut)", re.I)


def paragraphs(text: str):
    buf = []
    for line in text.splitlines():
        if line.strip():
            buf.append(line)
        elif buf:
            yield "\n".join(buf)
            buf = []
    if buf:
        yield "\n".join(buf)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        ti = payload.get("tool_input") or {}
        path = ti.get("file_path") or ""
        if not path.endswith(".md"):
            return 0
        new = ti.get("content") or ti.get("new_string") or ""
        if not new.strip():
            return 0

        offenders = []
        for para in paragraphs(new):
            if not CLAIM.search(para):
                continue
            if MARGINAL.search(para) or DEFN.search(para):
                continue
            m = CLAIM.search(para)
            frag = para[max(0, m.start() - 60): m.end() + 60].replace("\n", " ")
            offenders.append(frag.strip())
        if not offenders:
            return 0

        shown = "\n".join(f"    …{o}…" for o in offenders[:3])
        reason = (
            "BLOCKED — an effective-sample-size claim with no marginal named.\n\n"
            f"In {path}:\n{shown}\n\n"
            "An n_eff is not a property of a benchmark. It is a property of a benchmark "
            "UNDER A MARGINAL, and the same data gives different answers: SWE-bench "
            "Verified's 500 instances are 500 under a per-item reading and 96.5 under a "
            "per-source one. Written without its marginal the figure is not a weaker "
            "result — it is not a result.\n\n"
            "Name which one is being resampled, in the same paragraph:\n"
            "  • per-run    — agent stochasticity; the item set is held fixed\n"
            "  • per-item   — a different draw of items from the same source pool\n"
            "  • per-source — a different draw of the sources (repos, authors) themselves\n\n"
            "If the sentence is a definition, a formula or a table header rather than a "
            "claim, it will pass once that is visible from the paragraph itself.\n\n"
            "Three such claims reached the paper before this gate existed, each caught on "
            "read-back. The standing position was already written down and the new results "
            "were framed without it — see your project's standing-positions doc."
        )
        try:                                   # firing ledger; never fatal
            from _gatelog import record as _rec
            _l = locals()
            _rec("marginal-gate", _l.get("reason", ""),
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
