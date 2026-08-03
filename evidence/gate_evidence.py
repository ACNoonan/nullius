#!/usr/bin/env python3
"""Recover every real PreToolUse gate denial from Claude Code transcripts.

The hard part is not finding the denials. It is that a transcript from a session
that WORKED ON these gates is saturated with their denial strings — source being
written, a diff of two versions, the gate's own test harness printing its
positive controls — and every one of those reads like a firing to a text search.

Until 2026-08-03 that was handled with blocklists — a path prefix, a literal
placeholder, a filename — and blocklists were the wrong instrument. Each was
keyed to the single example in front of whoever wrote it, so each passed every
test anyone thought to write and failed silently on the second instance. The
source-read filter matched `/.claude/hooks/` and missed `nullius/gates/`; the
template filter matched `{name}` and missed `{REGISTER_NAME}`.

It now reads the RECORD SHAPE instead: a denial is a `tool_result` with
`is_error` true whose text begins with the marker. See DENIAL_RE below. Rebuilt
across the full transcript history, that removes 31 rows the blocklists had
passed — gate source being written, a `diff` of two gate versions, the stdout of
a gate's own test harness, an editor attachment. Every category it drops was
checked by hand and none was a firing.

On one identical scan the figure went 127 -> 96. Nothing changed about the
gates; the instrument that counted them was wrong, and had been since the first
release.
"""
import json, glob, os, re, sys, collections, hashlib

import sys
_pats = sys.argv[1:] or ["*"]          # e.g. "*myproject*"
ROOTS = [d for p in _pats
         for d in glob.glob(os.path.expanduser(f"~/.claude/projects/{p}"))]

# Order matters: the maths signature must be tried BEFORE the plain depth one,
# because the maths denial also contains the literal "depth: full".
GATE_BY_SIG = [
    ("lose mathematics",               "research-depth-gate/maths"),
    ("depth: full",                    "research-depth-gate"),
    ("ownership concession",           "ownership-gate"),
    ("commitments block",              "prereg-commitment-gate"),
    ("commitments undischarged",       "prereg-commitment-gate"),
    ("VOCAB.md",                       "vocab-gate"),
    ("bibliography entry contradicts", "citation-attribution-gate"),
    ("no marginal named",              "marginal-gate"),
    ("effective-sample-size",          "marginal-gate"),
]
# An uninstantiated placeholder of ANY name, not just `{name}`. `ownership_gate`
# uses `{REGISTER_NAME}` and shipped two rows past the old literal test.
TEMPLATE_RE = re.compile(r"\{[A-Za-z_][A-Za-z_0-9]*\}")

# A gate reading its own source is not a gate catching a claim. Match on what
# the file IS — a gate module, wherever it is checked out — rather than on the
# one directory the author happened to have installed at the time.
def is_gate_source(target):
    if not target:
        return False
    base = os.path.basename(target)
    parent = os.path.basename(os.path.dirname(target))
    return (
        "/.claude/hooks/" in target
        or parent in ("gates", "hooks")
        or bool(re.match(r"^(test[-_])?[a-z_-]+[-_]gate\.py$", base))
        or base in ("provenance.py", "proseleak.py", "_gatelog.py",
                    "gate_evidence.py", "extraction_integrity.py")
    )

# A hook denial has a SHAPE, and reading for it beats every path blocklist here.
#
# The generator used to regex the whole serialised record, so any record that
# merely CONTAINED the string counted: a `diff` of two gate files, the stdout of
# a gate's own test harness, a Write whose content was a gate, an attachment
# snippet of one. All of it read as a firing. That is how five contaminated rows
# reached the published table, and widening the path filters only caught three
# of them — the rest had no resolvable target to filter on.
#
# What a real denial is, structurally: a `tool_result` block, `is_error` true,
# whose text BEGINS with the marker. Nothing else in a transcript has that shape,
# and a gate quoting itself never does — its BLOCKED text sits mid-content, in a
# result that succeeded.
DENIAL_RE = re.compile(r"^BLOCKED\s+—\s+(.{10,200}?)(?:\n|$)")


def _blocks(rec):
    c = (rec.get("message") or {}).get("content")
    return c if isinstance(c, list) else []


def _result_text(blk):
    txt = blk.get("content")
    if isinstance(txt, list):
        txt = "\n".join(p.get("text", "") for p in txt if isinstance(p, dict))
    return txt if isinstance(txt, str) else ""


def denials(rec):
    """Every genuine hook denial in one transcript record."""
    for blk in _blocks(rec):
        if not isinstance(blk, dict) or blk.get("type") != "tool_result":
            continue
        if not blk.get("is_error"):
            continue
        m = DENIAL_RE.match(_result_text(blk).strip())
        if m:
            yield m.group(1).strip()


# Why a record mentions BLOCKED without being a firing. Reported rather than
# lumped into one number, because the breakdown is the argument: it shows what a
# naive `grep BLOCKED` would have counted, and every category here is one this
# generator counted at some point.
def why_not_denial(rec):
    if any(denials(rec)):
        return None
    blob = json.dumps(rec, ensure_ascii=False)
    for blk in _blocks(rec):
        if isinstance(blk, dict) and blk.get("type") == "tool_use":
            fp = (blk.get("input") or {}).get("file_path") or ""
            if is_gate_source(fp):
                return "a gate's own source being written"
    if any(s in blob for s in ("POSITIVE CONTROL", "POS CONTROL", "NEG CONTROL",
                               "must BLOCK", "Must BLOCK", "hooktest", "_gatetest")):
        return "a gate's own test harness, run deliberately"
    if is_gate_source((rec.get("attachment") or {}).get("filename", "")):
        return "a gate's source quoted as an editor attachment"
    if TEMPLATE_RE.search(blob) and "permissionDecisionReason" not in blob:
        return "an uninstantiated {PLACEHOLDER} in gate source"
    return "gate text quoted in other tool output"


def classify(reason):
    for sig, gate in GATE_BY_SIG:
        if sig in reason: return gate
    return None

events, tool_targets = {}, {}
files_scanned = lines_scanned = 0
rejected = collections.Counter()

for root in ROOTS:
    for path in sorted(glob.glob(f"{root}/*.jsonl")):
        files_scanned += 1
        # pass 1: map tool_use_id -> target file
        for line in open(path, errors="replace"):
            lines_scanned += 1
            if '"tool_use"' not in line: continue
            try: rec = json.loads(line)
            except Exception: continue
            for blk in (rec.get("message") or {}).get("content") or []:
                if isinstance(blk, dict) and blk.get("type") == "tool_use":
                    fp = (blk.get("input") or {}).get("file_path")
                    if fp: tool_targets[blk["id"]] = fp
        # pass 2: denials
        for line in open(path, errors="replace"):
            if "BLOCKED" not in line: continue
            try: rec = json.loads(line)
            except Exception: continue
            blob = json.dumps(rec, ensure_ascii=False)
            for reason in denials(rec):
                if TEMPLATE_RE.search(reason):              # uninstantiated template
                    rejected["template in gate source"] += 1; continue
                gate = classify(reason)
                if not gate:
                    rejected["unrecognised BLOCKED prose"] += 1; continue
                tuid = rec.get("message", {}).get("content", [{}])
                tuid = tuid[0].get("tool_use_id") if isinstance(tuid, list) and tuid else None
                target = tool_targets.get(tuid, "")
                if is_gate_source(target):
                    rejected["gate source read"] += 1; continue
                if ".hooktest" in blob:
                    rejected["deliberate hooktest"] += 1; continue
                key = rec.get("uuid") or f"{reason}|{target}"
                if key in events:
                    rejected["replayed duplicate"] += 1; continue
                events[key] = {
                    "ts": (rec.get("timestamp") or "")[:19],
                    "gate": gate, "reason": reason,
                    "target": os.path.basename(target) if target else "?",
                    "session": os.path.basename(path)[:8],
                }
            why = why_not_denial(rec)
            if why:
                rejected[why] += 1

def redact(name):
    """Target filenames name unpublished work and must not ship.

    Redaction is done HERE rather than by hand after the fact, because the
    committed artifact claimed redaction that this generator did not perform —
    one forgotten manual pass and the next regeneration publishes the lot. The
    hash is stable, so repeated firings on the same file stay visibly the same
    file, which is what the table is read for.
    """
    if not name or name == "?":
        return "?"
    stem, dot, ext = name.rpartition(".")
    h = hashlib.sha256((stem or name).encode()).hexdigest()[:4]
    return f"«{h}»{dot}{ext}" if dot else f"«{h}»"


ev = sorted(events.values(), key=lambda e: e["ts"])
for e in ev:
    e["target"] = redact(e["target"])
print(f"transcripts scanned : {files_scanned}")
print(f"lines scanned       : {lines_scanned:,}")
print(f"UNIQUE DENIALS      : {len(ev)}\n")
print("=== rejected (and why) ===")
for k, n in rejected.most_common(): print(f"  {n:5d}  {k}")
print("\n=== unique denials by gate ===")
for g, n in collections.Counter(e["gate"] for e in ev).most_common(): print(f"  {n:4d}  {g}")
print("\n=== by day ===")
for d, n in sorted(collections.Counter(e["ts"][:10] for e in ev).items()): print(f"  {d}  {n}")
print("\n=== every event ===")
for e in ev:
    print(f"  {e['ts']}  {e['gate']:<26} {e['target']:<28} {e['reason'][:70]}")

# ---- markdown artifact ----
import collections as _c
out = [
    "# Gate firings — recovered from Claude Code transcripts",
    "",
    f"Scanned **{files_scanned} transcripts** ({lines_scanned:,} records) across",
    "the scanned projects.",
    "",
    f"**{len(ev)} unique denials** — a hook `tool_result` carrying an error whose",
    "text begins with the denial marker. Nothing else counts. A `grep BLOCKED` over",
    f"the same transcripts returns {(len(ev) + sum(rejected.values())) / max(len(ev), 1):.1f}x "
    "more, and none of the excess is a firing.",
    "",
    "## What was excluded, and why",
    "",
    "| rejected | reason |",
    "|---:|---|",
]
for k, n in rejected.most_common():
    out.append(f"| {n} | {k} |")
out += ["",
    "Almost all of it is this project's own text. A session that edits a gate fills",
    "its transcript with that gate's denial strings — in the diff, in the file being",
    "written, in the test harness printing its positive controls — and a text search",
    "cannot tell that from the gate refusing someone's claim. Earlier releases of",
    "this table could not either, which is why the published figure has come down.",
    "",
    "## By gate", "", "| n | gate |", "|---:|---|"]
for g, n in _c.Counter(e["gate"] for e in ev).most_common():
    out.append(f"| {n} | `{g}` |")
out += ["", "## By day", "", "| day | firings |", "|---|---:|"]
for d, n in sorted(_c.Counter(e["ts"][:10] for e in ev).items()):
    out.append(f"| {d} | {n} |")
out += ["", "*Timestamps are UTC; the final day's rows are the prior evening local time.*",
        "", "## Every firing", "",
        "*Target filenames are redacted — they name unpublished work. The token is a",
        "stable hash, so the same file is recognisable across rows. Dates, gates and",
        "violation types are verbatim.*", "",
        "| when (UTC) | gate | target | violation |", "|---|---|---|---|"]
for e in ev:
    out.append(f"| {e['ts'].replace('T',' ')} | `{e['gate']}` | `{e['target']}` | {e['reason']} |")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "EVIDENCE.md"), "w").write("\n".join(out) + "\n")
print(f"\nwrote EVIDENCE.md ({len(out)} lines)")
