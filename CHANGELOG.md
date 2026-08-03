# Changelog

## [Unreleased]

### Added — a positive control can now say that it is one

The case location filtering cannot reach: a control replays real text through a
real gate at a real path, so its ledger row is identical to a genuine catch.
Everything about it is true except the intent, and intent is not in the file.

- `NULLIUS_CONTROL` marks every firing beneath it `control: true`. The gate still
  blocks — refusing is the point of a control — and only the row's status changes.
- `tools/selftest.py <gate> <path> [--expect deny|allow]` runs a gate against text
  on stdin and **sets the variable itself**, so a control cannot be run without
  being labelled. That is the whole design: a flag you must remember is a flag you
  forget, and forgetting counts a control as a real catch. Because the tool cannot
  omit the label, an unlabelled row stays trustworthy. Exits non-zero when the gate
  disagrees with the prediction, so a gate that stopped firing fails CI.
- `provenance.counts_as_evidence(row)` is now the single named decision, honouring
  the declaration first and falling back to location for rows written before the
  declaration existed.
- Tests 59 → 73, including the check that would have caught the original problem:
  the same firing, on the same real path, counted with the flag and without.

### Fixed — `extraction_integrity.py` had forked, and it is a gate's own instrument

Two research repos ran a 328-line copy; the canonical one here is 378. Reconciled
after measuring rather than reasoning: the canonical copy was swept against a real
341-PDF shelf and its classification compared to the committed index — **321 shared
papers, zero class changes, nothing dropped from `maths_unsafe`.** The fork was a
refactor. Its one behavioural difference was where the index is written
(`<root>/.nullius/` rather than `papers/`), and that is the hazard: a reader that
knows only the old path stops finding the index the moment the tool is upgraded,
silently, because an absent index is how the maths half is designed to go inert.

- The tool resolved `_config` through `abspath(__file__)`, which does not follow a
  symlink — so the supported install (link, never copy) would have silently
  degraded the governed-root default to the shelf directory. Uses `realpath` now.

### Fixed — third sync: the instruments that count the gates were not gated

Nothing below changes what a gate blocks. It changes what this project was
entitled to say about how often they had, which had drifted in the direction
that flatters the tool — the one direction nothing here was checking.

- **The test suite wrote its firings into the user's real evidence ledger.**
  `_gatelog.LEDGER` was a constant, so nothing could redirect it, and 177 of the
  220 rows in the author's ledger were rows `tests/test_gates.py` had written.
  The path now resolves per call — `$NULLIUS_LEDGER`, else the legacy location
  if it exists, else `$XDG_STATE_HOME/nullius/` — and the suite points itself at
  a temp file before the first gate runs. The legacy path is kept when present
  so an existing ledger is not orphaned.
- **`provenance.py` would have stamped those rows into a paper.** It read the
  ledger raw, so the derived provenance block — the one part of a paper whose
  whole warrant is that no number in it was typed — would have disclosed 220
  firings where 39 had happened. Synthetic rows are now excluded by target
  location and reported as an exclusion, never dropped silently. The one case
  it cannot see, a positive control replaying real text through a gate, is
  documented rather than filtered.
- **The evidence generator counted this project quoting itself.** It searched
  transcripts for the denial text, so a session that *edited* a gate — writing
  it, diffing two versions, running its test harness — read as a firing. Two
  filters were also keyed to single spellings (`/.claude/hooks/` only;
  `{name}` while `ownership_gate` templates `{REGISTER_NAME}`). Replaced with a
  structural test: a firing is an errored hook result whose text begins with the
  marker. Every category the new test drops was checked by hand; none was a
  firing.

### Changed — the published evidence figure comes down

- **127 unique denials → 96** on one identical scan of 371 transcripts: 31 rows
  were the gates quoting themselves. `grep BLOCKED` still returns 6.4x the real
  number. The committed table tracks a live corpus, so its total moves as
  sessions accrue; 127→96 is the paired comparison this entry is about.
- **`ownership_gate` has never fired on live work.** The README claimed six
  firings within a day of install; those were positive controls replaying the
  section the gate was built from. It catches that case on demand and has not
  yet caught a new one.
- **The depth gate's maths-fidelity half likewise has no live firing** — its two
  recorded hits were writes to a deliberate probe file.
- Tests: 48 checks → 59, covering the ledger's write path, the redirect, and the
  synthetic-firing classifier in both directions. The check that would have
  caught the original bug — *the real ledger is untouched* — was verified to go
  red when pointed at the real ledger.

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
