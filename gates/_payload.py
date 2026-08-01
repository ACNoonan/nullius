"""Emit the PreToolUse payload shape for a file already on disk.

Lets the git adapter reuse the write-time gates verbatim instead of
reimplementing every rule for the commit path. One implementation of each rule,
two places it runs.

    python3 _payload.py FILE | python3 research_depth_gate.py
"""
import json
import sys

if len(sys.argv) < 2:
    sys.exit(0)

try:
    content = open(sys.argv[1], encoding="utf-8", errors="replace").read()
except Exception:
    content = ""

json.dump({"tool_name": "Write",
           "tool_input": {"file_path": sys.argv[1], "content": content}},
          sys.stdout)
