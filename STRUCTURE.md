# Structure — nullius

**Kind: infrastructure.** S2–S5 do not apply — this repo owns no experiments and no findings.
S1 and S6 are met.

*Added 2026-08-07 per [the standard](../command-center/standard/infrastructure.md).*

## The one rule

> ***Nullius in verba.*** **A note saying you read something is a claim, not evidence.**

Eight programs that read what is about to be written and **block the write** when the claim has
nothing behind it. Not a prompt pack, and not instructions asking a model to be careful — gates
that take nobody's word for it, including yours.

## Map

```
gates/           the eight gate programs. `_config.py` `_gatelog.py` `_payload.py` are shared
                 internals — the leading underscore means "not a gate, don't wire it"
adapters/        per-host wiring: claude-code/ (settings.json), codex/, cursor/, git/
tools/           extraction_integrity.py — symlinked into calibrated-uncertainty/papers
                 selftest.py
evidence/        EVIDENCE.md + gate_evidence.py — what each gate has actually caught
docs/            prose
tests/           per-gate tests
```

## ⚠ The live gates and this package have forked. All six of them.

`~/.claude/hooks/` holds **real files, not symlinks** into `gates/`. Every shared gate differs:

| gate | this package | live in `~/.claude/hooks/` |
|---|---|---|
| `citation_attribution_gate` | 2026-08-03, 352 ln | 2026-08-01, 336 ln |
| `ownership_gate` | 2026-08-03, 274 ln | 2026-08-01, 249 ln |
| `research_depth_gate` | 2026-08-03, 444 ln | 2026-08-03, 425 ln |
| `prereg_commitment_gate` | 2026-07-31, 183 ln | 2026-07-30, 175 ln |
| `marginal_gate` | 2026-07-31, 146 ln | 2026-07-30, 146 ln |
| `vocab_gate` | 2026-07-31, 159 ln | 2026-07-30, 159 ln |

**This looks deliberate, not accidental.** The package is consistently newer and longer, and the
differences are *generalization*: where the live gate says `"see RECONCILIATION-PROTOCOL.md
section 9"`, the packaged one says `"see your project's standing-positions doc"`. That is a public
release being lifted out of a private original — a reasonable thing to have done.

**But there is no sync mechanism, and two consequences follow.** A fix made in one never reaches
the other. And **the gates that actually run are not the gates that ship** — so the package's
behaviour is not what daily use tests, and daily use is not what the public gets.

**Deliberately not reconciled here.** This repo's own doctrine is that a fork may hold work that
exists nowhere else, so it is reported for a human, never clobbered. The direction of the fix —
generalize the live ones, or accept a vendor-and-adapt relationship and write down which is
canonical — is a design decision, not a filesystem operation.

*Two gates exist only on one side, which is a separate question from the drift:*
`proseleak` and `provenance` are packaged but not wired; `canonical-symlink-gate` runs globally
but is not in this package at all.

## Waivers

None.
