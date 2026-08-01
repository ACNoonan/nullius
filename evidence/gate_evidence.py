#!/usr/bin/env python3
"""Recover every real PreToolUse gate denial from Claude Code transcripts.

Three contamination sources this handles explicitly:
  1. hook SOURCE files read into context contain the literal BLOCKED strings
  2. deliberate .hooktest runs are not research denials
  3. transcripts REPLAY on resume/compaction, so one firing appears N times
"""
import json, glob, os, re, sys, collections

import sys
_pats = sys.argv[1:] or ["*"]          # e.g. "*myproject*"
ROOTS = [d for p in _pats
         for d in glob.glob(os.path.expanduser(f"~/.claude/projects/{p}"))]

GATE_BY_SIG = [
    ("depth: full",                    "research-depth-gate"),
    ("commitments block",              "prereg-commitment-gate"),
    ("commitments undischarged",       "prereg-commitment-gate"),
    ("VOCAB.md",                       "vocab-gate"),
    ("bibliography entry contradicts", "citation-attribution-gate"),
    ("no marginal named",              "marginal-gate"),
    ("effective-sample-size",          "marginal-gate"),
]
BLOCK_RE = re.compile(r"BLOCKED\s+—\s+([^\\\"\n]{10,200})")

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
            for m in BLOCK_RE.finditer(blob):
                reason = m.group(1).strip()
                if "{name}" in reason:                      # uninstantiated template
                    rejected["template in hook source"] += 1; continue
                gate = classify(reason)
                if not gate:
                    rejected["unrecognised BLOCKED prose"] += 1; continue
                tuid = rec.get("message", {}).get("content", [{}])
                tuid = tuid[0].get("tool_use_id") if isinstance(tuid, list) and tuid else None
                target = tool_targets.get(tuid, "")
                if "/.claude/hooks/" in target:
                    rejected["hook source read"] += 1; continue
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

ev = sorted(events.values(), key=lambda e: e["ts"])
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
    f"Scanned **{files_scanned} transcripts** ({lines_scanned:,} records) across the",
    "the scanned projects.",
    "",
    f"**{len(ev)} unique denials.** Every count below is deduplicated; the raw",
    "text-match count is roughly 2.4x higher and is not usable.",
    "",
    "## What was excluded, and why",
    "",
    "| rejected | reason |",
    "|---:|---|",
]
for k, n in rejected.most_common():
    out.append(f"| {n} | {k} |")
out += ["",
    "Each of those five is a way a naive `grep BLOCKED` overcounts. The hook",
    "source files contain the denial strings verbatim, so any session that read a",
    "hook inflates the count; templates carry an uninstantiated `{name}`;",
    "transcripts replay on resume and compaction.",
    "",
    "## By gate", "", "| n | gate |", "|---:|---|"]
for g, n in _c.Counter(e["gate"] for e in ev).most_common():
    out.append(f"| {n} | `{g}` |")
out += ["", "## By day", "", "| day | firings |", "|---|---:|"]
for d, n in sorted(_c.Counter(e["ts"][:10] for e in ev).items()):
    out.append(f"| {d} | {n} |")
out += ["", "*Timestamps are UTC; the final day's rows are the prior evening local time.*",
        "", "## Every firing", "",
        "| when (UTC) | gate | target | violation |", "|---|---|---|---|"]
for e in ev:
    out.append(f"| {e['ts'].replace('T',' ')} | `{e['gate']}` | `{e['target']}` | {e['reason']} |")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "EVIDENCE.md"), "w").write("\n".join(out) + "\n")
print(f"\nwrote EVIDENCE.md ({len(out)} lines)")
