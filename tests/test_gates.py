#!/usr/bin/env python3
"""Test suite for nullius. Standard library only — no pytest, no install step.

    python3 tests/test_gates.py

WHY THIS FILE MATTERS MORE THAN USUAL
    A verification tool with no tests refutes itself. Worse, the specific
    failure these gates are most likely to have is the SILENT one: a gate that
    stopped firing still looks installed, and a repo full of unchecked claims
    looks exactly like a repo full of checked ones.

    So every test below asserts BOTH directions. A gate that only ever allows
    passes a permissive test suite perfectly. Each case here pairs the thing
    that must be blocked with the thing that must not be, because a check that
    cannot come out wrong is not evidence.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES = os.path.join(ROOT, "gates")
PY = sys.executable or "python3"

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not cond else ""))


def run_gate(gate, path, content):
    """Feed a gate the PreToolUse payload shape. Returns True if it DENIED."""
    payload = json.dumps({"tool_name": "Write",
                          "tool_input": {"file_path": path, "content": content}})
    p = subprocess.run([PY, os.path.join(GATES, f"{gate}.py")],
                       input=payload, capture_output=True, text=True, timeout=20)
    return '"deny"' in p.stdout


UNBACKED = "# Read log\n\n| Moulton 1986 | depth: full |\n"
BACKED = ("# Read log\n\n| Moulton 1986 | depth: full — extracted with "
          "pdftotext, 412 lines |\n")


def test_opt_in(tmp):
    """A tree without the marker is not governed. A tree with it is."""
    print("\nopt-in scoping")
    off, on = os.path.join(tmp, "off"), os.path.join(tmp, "on")
    os.makedirs(off); os.makedirs(on)
    open(os.path.join(on, ".nullius.toml"), "w").close()
    check("no marker -> allows",
          not run_gate("research_depth_gate", os.path.join(off, "n.md"), UNBACKED))
    check("marker -> denies",
          run_gate("research_depth_gate", os.path.join(on, "n.md"), UNBACKED))


def test_no_false_positive(tmp):
    """The gate must distinguish a backed claim from an unbacked one, or it is
    just a keyword blocklist."""
    print("\ndiscrimination")
    on = os.path.join(tmp, "on2"); os.makedirs(on)
    open(os.path.join(on, ".nullius.toml"), "w").close()
    check("unbacked depth:full -> denies",
          run_gate("research_depth_gate", os.path.join(on, "n.md"), UNBACKED))
    check("depth:full WITH artifact -> allows",
          not run_gate("research_depth_gate", os.path.join(on, "n.md"), BACKED))


def test_fail_open(tmp):
    """Every gate allows on garbage input. A gate that blocks because the gate
    broke gets uninstalled, and then nothing is enforced at all."""
    print("\nfail-open")
    for g in ("research_depth_gate", "prereg_commitment_gate", "vocab_gate",
              "citation_attribution_gate", "marginal_gate", "ownership_gate"):
        for label, payload in (("empty", ""), ("not json", "<<<"),
                               ("wrong shape", '{"foo": 1}')):
            p = subprocess.run([PY, os.path.join(GATES, f"{g}.py")], input=payload,
                               capture_output=True, text=True, timeout=20)
            check(f"{g} allows on {label}",
                  '"deny"' not in p.stdout and p.returncode == 0)


def test_depth_claim_shapes(tmp):
    """The shapes a real bibliography actually uses.

    These exist because the suite once tested only the bare `depth: full` with no
    source named — and that was the ONE shape still working. A claim naming a
    citation key or an arXiv id reached a shelf lookup that raised NameError
    inside the gate's own try/except, so it FAILED OPEN, silently, on exactly the
    input the gate exists for. Every assertion below went from allow to deny on
    the fix, which is what makes them evidence rather than decoration.
    """
    print("\ndepth claim shapes")
    on = os.path.join(tmp, "shapes"); os.makedirs(on)
    open(os.path.join(on, ".nullius.toml"), "w").close()
    n = os.path.join(on, "n.md")
    check("bibkey-shaped claim, unbacked -> denies",
          run_gate("research_depth_gate", n,
                   "### [smith2020] Smith\n**Depth:** full — read it all.\n"))
    check("arXiv-shaped claim, unbacked -> denies",
          run_gate("research_depth_gate", n,
                   "paper 2306.05836\n**Depth:** full — read it all.\n"))
    # The line ends immediately after `full`; the pattern once required a
    # character after it, so the most natural way to write the claim was exempt.
    check("claim at end of line -> denies",
          run_gate("research_depth_gate", n, "**Depth:** full\n"))
    # Self-limiting prose states a LOWER depth without using a vocabulary word.
    # Gating it teaches people to stop writing the caveat.
    check("'a grep of the full text' is not a full-depth claim -> allows",
          not run_gate("research_depth_gate", n,
                       "Depth: this is a grep of the full text only.\n"))


def test_maths_fidelity(tmp):
    """A `depth: full` claim on an artifact whose text layer eats mathematics.

    The negative control is the point: the CLEAN row must NOT fire, or the gate
    is just blocking every backed claim and the index is doing no work.
    """
    print("\nmaths fidelity")
    on = os.path.join(tmp, "maths"); os.makedirs(on)
    open(os.path.join(on, ".nullius.toml"), "w").close()
    os.makedirs(os.path.join(on, ".nullius"), exist_ok=True)
    with open(os.path.join(on, ".nullius", "extraction_integrity.json"), "w") as fh:
        json.dump([{"pdf": "2306.05836.pdf", "cls": "GLYPH-LOSS", "maths_unsafe": True,
                    "text": "2306.05836.txt"},
                   {"pdf": "1209.2673.pdf", "cls": "CLEAN", "maths_unsafe": False,
                    "text": "1209.2673.txt"}], fh)
    n = os.path.join(on, "n.md")
    backed = "**Depth:** full — extracted with pdftotext, 900 lines"
    check("unsafe artifact, no maths flag -> denies",
          run_gate("research_depth_gate", n, f"paper 2306.05836\n{backed}\n"))
    check("unsafe artifact, `maths: unread` -> allows",
          not run_gate("research_depth_gate", n,
                       f"paper 2306.05836\n{backed}. maths: unread\n"))
    check("unsafe artifact, `maths: image` -> allows",
          not run_gate("research_depth_gate", n,
                       f"paper 2306.05836\n{backed}. maths: image (p20 rendered)\n"))
    check("CLEAN artifact needs no flag -> allows",
          not run_gate("research_depth_gate", n, f"paper 1209.2673\n{backed}\n"))
    # No index at all => this half must be inert, not blocking.
    off = os.path.join(tmp, "noindex"); os.makedirs(off)
    open(os.path.join(off, ".nullius.toml"), "w").close()
    check("no index built -> maths half is inert",
          not run_gate("research_depth_gate", os.path.join(off, "n.md"),
                       f"paper 2306.05836\n{backed}\n"))


def test_ownership(tmp):
    """A concession bounded by the register is fine; one that overruns it is not.

    The third check is the negative control the gate was designed around: a
    concession naming a key with NO exclusion row is the majority case and must
    pass, or the rule collapses into "never concede anything".
    """
    print("\nownership")
    on = os.path.join(tmp, "own"); os.makedirs(on)
    open(os.path.join(on, ".nullius.toml"), "w").close()
    open(os.path.join(on, "OWNERSHIP.md"), "w").write(
        "### [P2] The design effect\n\n"
        "**EXCLUDES:** [kish1965] — his own §12.9. He coined the design effect for "
        "means and proportions and never applied it there.\n")
    n = os.path.join(on, "sec.md")
    check("concession over an excluded owner -> denies",
          run_gate("ownership_gate", n,
                   "We claim none of this structure and it should not be read as "
                   "new; it is [kish1965] eq. 5.6.8.\n"))
    check("concession naming the exclusion scope -> allows",
          not run_gate("ownership_gate", n,
                       "We claim none of this structure, except at §12.9 where "
                       "[kish1965] never went.\n"))
    check("concession over an UNexcluded key -> allows",
          not run_gate("ownership_gate", n,
                       "Every component of that picture is published, and we claim "
                       "none of them [crespi2011].\n"))
    check("no concession language -> allows",
          not run_gate("ownership_gate", n,
                       "This composition is ours, and [kish1965] eq. 5.6.8 is an "
                       "ingredient.\n"))
    check("the register itself is never gated -> allows",
          not run_gate("ownership_gate", os.path.join(on, "OWNERSHIP.md"),
                       "We claim none of this; it is [kish1965].\n"))


def test_firing_ledger(tmp):
    """The ledger must record real firings and must not record ours.

    This suite used to append every firing it provoked to the user's real
    ledger, because `_gatelog.LEDGER` was a constant and nothing could redirect
    it. 177 of 220 rows on 2026-08-03 were rows this file wrote. Nothing caught
    it: the ledger had no test at all, and a poisoned ledger reads exactly like
    a busy one.

    So the second check here is the one that matters. Asserting that a row got
    written proves the logger works; only asserting that it went NOWHERE ELSE
    proves the redirect does, and that is the direction that failed.
    """
    print("\nfiring ledger")
    sys.path.insert(0, GATES)
    try:
        import _gatelog
    finally:
        sys.path.pop(0)

    on = os.path.join(tmp, "ledger"); os.makedirs(on)
    open(os.path.join(on, ".nullius.toml"), "w").close()
    n = os.path.join(on, "n.md")

    # What the ledger would be if this suite had not redirected it — i.e. the
    # user's own file. Snapshot its size, provoke a denial, require no change.
    redirected = os.environ.pop("NULLIUS_LEDGER")
    real = _gatelog.ledger_path()
    os.environ["NULLIUS_LEDGER"] = redirected
    before = os.path.getsize(real) if os.path.exists(real) else None

    check("redirect is in force", _gatelog.ledger_path() == redirected)
    check("a denial appends a row", run_gate("research_depth_gate", n, UNBACKED)
          and os.path.exists(redirected))

    rows = [json.loads(l) for l in open(redirected, encoding="utf-8") if l.strip()]
    check("the row names the gate and the target",
          any(r.get("gate") == "research-depth-gate" and r.get("target", "").endswith("n.md")
              for r in rows))
    check("the row carries no file content",
          all("depth: full — extracted" not in json.dumps(r) for r in rows))

    after = os.path.getsize(real) if os.path.exists(real) else None
    check("the real ledger is untouched", after == before,
          f"{real} went {before} -> {after}")

    n_before = len(rows)
    run_gate("research_depth_gate", n, BACKED)
    rows = [l for l in open(redirected, encoding="utf-8") if l.strip()]
    check("an allowed write appends nothing", len(rows) == n_before)

    # The stamp must not count the rows this suite just wrote. Both directions:
    # a temp target is synthetic, a target under a real tree is not — a filter
    # that excluded everything would pass a one-sided test perfectly.
    sys.path.insert(0, GATES)
    try:
        import provenance
    finally:
        sys.path.pop(0)
    check("a temp-dir firing is synthetic", provenance.is_synthetic(n))
    check("a .hooktest firing is synthetic",
          provenance.is_synthetic("/home/r/paper/.hooktest.md"))
    check("an in-repo gate probe is synthetic",
          provenance.is_synthetic("/home/r/experiments/_gatetest.md"))
    check("a real research path is not synthetic",
          not provenance.is_synthetic(os.path.join(ROOT, "paper", "references.md")))
    check("an empty target is not synthetic", not provenance.is_synthetic(""))


def test_citation_attribution(tmp):
    """The gate's whole point: the entry says one name, the artifact says another.

    There was no test for this gate's blocking behaviour at all — a mutation run
    proved it, by breaking the gate and watching the suite stay green. The last
    two checks cover the window logic: an author block sitting behind 900 lines of
    journal masthead must not read as a misattribution.
    """
    print("\ncitation attribution")
    on = os.path.join(tmp, "cite"); os.makedirs(on)
    open(os.path.join(on, ".nullius.toml"), "w").close()
    text = os.path.join(on, "papers", "text"); os.makedirs(text)
    refs = os.path.join(on, "references.md")

    def entry(surname, title, artifact):
        return (f"### [{surname.lower()}2020] {surname}, A. 2020. {title}.\n\n"
                f"**Depth:** full — `papers/text/{artifact}`\n")

    open(os.path.join(text, "right.txt"), "w").write(
        "Nested Cluster Randomised Designs\n\nAlice Moulton, Bob Kish\n\n"
        "Abstract. We consider nested designs.\n")
    check("entry matching the artifact -> allows",
          not run_gate("citation_attribution_gate", refs,
                       entry("Moulton", "Nested Cluster Randomised Designs", "right.txt")))
    # Title present, author absent: the window DID reach the article, so the
    # surname really is wrong. This is the signature the gate exists for.
    check("wrong author on the right paper -> denies",
          run_gate("citation_attribution_gate", refs,
                   entry("Teerenstra", "Nested Cluster Randomised Designs", "right.txt")))

    # An issue-level artifact: 200 non-blank lines of masthead before the byline.
    open(os.path.join(text, "issue.txt"), "w").write(
        "".join(f"Stata Journal front matter line {i}\n" for i in range(200))
        + "Nested Cluster Randomised Designs\n\nAlice Moulton\n")
    check("author behind front matter -> UNRESOLVED, does not block",
          not run_gate("citation_attribution_gate", refs,
                       entry("Moulton", "Nested Cluster Randomised Designs", "issue.txt")))

    # Same entry, but the artifact is padded with BLANK lines: the byline sits at
    # raw line 900 and non-blank line 3. Both the hook and the audit ALLOW it
    # either way — the hook cannot distinguish "verified" from "unresolvable",
    # since both permit the write. So assert on the audit, which reports the two
    # separately. Counting raw lines made this correct entry unverifiable.
    open(os.path.join(text, "padded.txt"), "w").write(
        "A journal\n" + "\n" * 900 + "Nested Cluster Randomised Designs\n\nAlice Moulton\n")
    open(refs, "w").write(entry("Moulton", "Nested Cluster Randomised Designs", "padded.txt"))
    p = subprocess.run([PY, os.path.join(GATES, "citation_attribution_gate.py"),
                        "--audit", refs], capture_output=True, text=True, timeout=20)
    # Assert the artifact RESOLVED, not merely that nothing failed: an audit that
    # resolves no artifacts reports "0 failing" over a bibliography it never
    # checked, and that green is indistinguishable from a real pass.
    check("blank padding does not defeat the window -> verified, not unresolved",
          "1 with a resolvable artifact" in p.stdout
          and "0 failing, 0 unresolved" in p.stdout, p.stdout[-300:])

    open(refs, "w").write(entry("Moulton", "Nested Cluster Randomised Designs", "issue.txt"))
    p = subprocess.run([PY, os.path.join(GATES, "citation_attribution_gate.py"),
                        "--audit", refs], capture_output=True, text=True, timeout=20)
    check("front matter -> reported as unresolved, and does not fail the audit",
          "0 failing, 1 unresolved" in p.stdout and p.returncode == 0, p.stdout[-300:])


def test_proseleak(tmp):
    """Internal vocabulary in prose is blocked; the same token inside a code
    span is reported but not blocked."""
    print("\nproseleak")
    sec = os.path.join(tmp, "sections"); os.makedirs(sec)
    repo = os.path.join(tmp, "repo"); os.makedirs(repo)
    open(os.path.join(repo, "VOCAB.md"), "w").write(
        "| `AB-NN` | test | program | | our lane |\n")
    shutil.copy(os.path.join(GATES, "..", "gates", "_config.py"),
                os.path.join(tmp, "_ignored.py"))
    open(os.path.join(repo, "vocab.py"), "w").write(
        "from collections import defaultdict\n"
        "REPO='.'\n"
        "class N:\n"
        "    def __init__(s,p,k,sc,o,m,src):\n"
        "        s.prefix,s.kind,s.scope,s.owner,s.meaning,s.source=p,k,sc,o,m,src\n"
        "def load_registry(repo=REPO):\n"
        "    return {'AB': N('AB','test','program','','','')}, defaultdict(dict), {}\n")
    open(os.path.join(sec, "01.md"), "w").write(
        "# S\n\nWe measured AB-01 here.\n\n```\nAB-01 inside a fence\n```\n")
    p = subprocess.run([PY, os.path.join(GATES, "proseleak.py"),
                        "--sections", sec, "--repo", repo, "--check"],
                       capture_output=True, text=True, timeout=30)
    check("prose leak detected", "1 prose leaks" in p.stdout, p.stdout[-200:])
    check("code-fence occurrence not counted as prose", "1 in code" in p.stdout,
          p.stdout[-200:])
    check("--check exits non-zero on leak", p.returncode == 1)


def test_git_adapter(tmp):
    """The portable layer: refuses the commit, and only in an opted-in repo."""
    print("\ngit adapter")
    if not shutil.which("git"):
        check("git present", False, "git not on PATH"); return
    repo = os.path.join(tmp, "gitrepo"); os.makedirs(repo)
    env = dict(os.environ, NULLIUS_DIR=ROOT, NULLIUS_PYTHON=PY)
    def git(*a, **kw):
        return subprocess.run(["git", "-C", repo, *a], capture_output=True,
                              text=True, env=env, timeout=30, **kw)
    git("init", "-q")
    git("config", "user.email", "t@t"); git("config", "user.name", "t")
    hooks = os.path.join(repo, ".git", "hooks")
    os.makedirs(hooks, exist_ok=True)
    git("config", "core.hooksPath", hooks)
    dst = os.path.join(hooks, "pre-commit")
    with open(dst, "w") as fh:
        fh.write(f'#!/bin/sh\nNULLIUS_DIR="{ROOT}" exec '
                 f'"{ROOT}/adapters/git/pre-commit" "$@"\n')
    os.chmod(dst, 0o755)

    open(os.path.join(repo, "n.md"), "w").write(UNBACKED)
    git("add", "-A")
    check("not opted in -> commit succeeds", git("commit", "-qm", "a").returncode == 0)

    open(os.path.join(repo, ".nullius.toml"), "w").close()
    open(os.path.join(repo, "n.md"), "w").write(UNBACKED.replace("Moulton", "Kish"))
    git("add", "-A")
    check("opted in, unbacked -> commit REFUSED", git("commit", "-qm", "b").returncode != 0)

    open(os.path.join(repo, "n.md"), "w").write(BACKED)
    git("add", "-A")
    check("opted in, backed -> commit succeeds", git("commit", "-qm", "c").returncode == 0)

    open(os.path.join(repo, "n.md"), "w").write(UNBACKED)
    git("add", "-A")
    check("--no-verify bypass works",
          git("commit", "-qm", "d", "--no-verify").returncode == 0)


def main():
    tmp = tempfile.mkdtemp(prefix="nullius-test-")
    # Every gate this suite provokes logs a firing. Send those somewhere
    # disposable BEFORE the first one runs — subprocesses inherit this — or the
    # suite writes its fixtures into the user's real evidence ledger, which is
    # what it did until 2026-08-03. Set here rather than in a fixture so there
    # is no ordering by which a test runs unredirected.
    os.environ["NULLIUS_LEDGER"] = os.path.join(tmp, "gate-firings.jsonl")
    try:
        for t in (test_opt_in, test_no_false_positive, test_depth_claim_shapes,
                  test_maths_fidelity, test_ownership, test_firing_ledger,
                  test_citation_attribution, test_fail_open, test_proseleak,
                  test_git_adapter):
            t(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    for f in FAIL:
        print(f"  FAILED: {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
