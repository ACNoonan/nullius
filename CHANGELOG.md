# Changelog

## [Unreleased]

### Added
- Five write-time gates: read depth, citation attribution, pre-registration
  commitments, vocabulary, and effective-sample-size marginal.
- Build-time `provenance.py` (derived provenance stamp; bibliography depth
  audit) and `proseleak.py` (internal vocabulary in published prose).
- `_gatelog.py`, an append-only firing ledger.
- Adapters for Claude Code (blocking), git (blocking, portable), Cursor and
  Codex (advisory).
- `adapters/git/install.sh`, which resolves `core.hooksPath` and verifies the
  install with a canary commit that must be refused.
- `tests/test_gates.py` — 26 checks, each asserting both directions.
- `evidence/EVIDENCE.md` — 76 gate firings recovered from 159 real sessions.

### Fixed before first release
- `git diff --cached` lists nothing on a root commit, so the first commit in a
  repo was never checked.
- `git rev-parse --git-dir` returns a relative path, which made the installer's
  canary point at the wrong hooks directory and report a good install as failed.
- `proseleak` flagged `pre-registered` and "the harness" (a simulation harness)
  as internal vocabulary — 33% precision on first run against a real paper.
