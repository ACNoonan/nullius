# Changelog

## [Unreleased]

### Added — second sync from the private harness

- `ownership_gate`: refuses an ownership CONCESSION over a source the register
  records as not holding it. The first gate that runs in the opposite direction
  to all the others — an over-concession is as damaging as an over-claim and no
  referee's incentive runs that way.
- Maths-fidelity half of `research_depth_gate`: a `depth: full` claim resting on
  an artifact whose text layer is known to eat mathematics must state where the
  maths came from (`maths: image` / `unread` / `n/a`). Artifact presence is not
  artifact fidelity.
- `tools/extraction_integrity.py`, the instrument that produces the index that
  half consults. Triages a shelf of PDFs, routes to page images, and never
  repairs an extraction. Shelf layout is configurable (`--shelf`, `--out`,
  `$NULLIUS_SHELF`); with no index built, the gate half is silently inert.
- `citation_attribution_gate` now scopes its author-block window by NON-BLANK
  lines, and reports UNRESOLVED — rather than asserting a misattribution — when
  both the author and title checks fail together, which is the signature of a
  window that never reached the article rather than of a wrong name.
- Tests: 26 checks -> 48, covering the two new gates, the claim shapes a real
  bibliography uses, and the citation gate's blocking behaviour (which had none).
- Evidence refreshed against 169 transcripts: 127 unique denials over seven days.

### Fixed

- **`research_depth_gate` failed open on its two commonest inputs.** The
  opt-in refactor left `roots_for(path)` in helpers where no `path` was in scope;
  the NameError was swallowed by the gate's own fail-open handler, so a claim
  naming a citation key or an arXiv id was never gated. Only the bare
  `depth: full` with no source named still fired. The suite passed throughout,
  because it only ever fed the gate that one shape.
- `citation_attribution_gate --audit` never resolved `ROOTS`, so it could not
  find any artifact and reported "0 failing" over a bibliography it had not
  checked — a green result indistinguishable from a real pass.
- `DEPTH_RE` required a character after `full`, so a line ending exactly at
  `**Depth:** full` — the most natural way to write the claim — was exempt.
- The evidence generator emitted real target filenames while the committed
  artifact claimed they were redacted. Redaction now happens in the generator,
  and its "2.4x" and "five" are derived rather than typed.
- The CI mutation job patched a line that no longer existed, so it silently
  tested nothing. It now runs a mutant per gate and errors if one fails to apply.

### Added — initial set
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
