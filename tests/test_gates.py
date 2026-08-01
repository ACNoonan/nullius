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
              "citation_attribution_gate", "marginal_gate"):
        for label, payload in (("empty", ""), ("not json", "<<<"),
                               ("wrong shape", '{"foo": 1}')):
            p = subprocess.run([PY, os.path.join(GATES, f"{g}.py")], input=payload,
                               capture_output=True, text=True, timeout=20)
            check(f"{g} allows on {label}",
                  '"deny"' not in p.stdout and p.returncode == 0)


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
    try:
        for t in (test_opt_in, test_no_false_positive, test_fail_open,
                  test_proseleak, test_git_adapter):
            t(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    for f in FAIL:
        print(f"  FAILED: {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
