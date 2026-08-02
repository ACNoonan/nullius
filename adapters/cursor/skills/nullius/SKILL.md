---
name: nullius
description: >-
  Research-claim discipline for AI-assisted work. Use when writing up a result,
  citing a paper, claiming novelty, recording what was read, reporting an
  effective sample size, or preparing a document for publication. Enforces that
  a claim has an artifact behind it before it ships.
---

# nullius

Cursor cannot refuse a write, so this skill is advisory. **Install
`adapters/git/pre-commit` too** — that layer blocks the commit regardless of
what any model decided.

Applies in repositories holding a `.nullius.toml`.

## The gates, as rules

**Depth.** A source may not gate a decision until it has been read in full.
Record depth per source with exactly this vocabulary — `full`, `targeted`,
`fetch-summary`, `snippet`, `unsearched` — and for `targeted`, say which part
was read and what was not. A model's summary of a paper is never a premise.

**Fidelity.** An artifact existing is not an artifact being right. A PDF text
layer routinely deletes mathematics with no mangling to warn you — `C(γ*)` comes
out as `C ( )`, `δ_t` as `t`. Where the shelf index flags a paper maths-unsafe,
a `full` claim must say `maths: image`, `maths: unread`, or `maths: n/a`. Do not
re-run the extraction in another mode: every mode reads the same layer and
agrees with the error. The page image is the only authority.

**Instrument.** Before reporting a number, state a check that *could have come
out wrong* and what its failure would have looked like. A check that cannot
fail is not evidence.

**Commitments.** No RESULT while its pre-registered commitments are
undischarged.

**Vocabulary.** No identifier in an undeclared namespace. No internal lane IDs
or workflow words in published prose.

**Marginal.** No effective sample size without naming what is resampled.

**Ownership.** A concession is as gateable as a claim, and harder to catch — no
referee will tell you that you gave away more than you owed. Do not write "we
claim none of this" over a source your ownership register records as *not*
holding it; name the exclusion's scope in the same paragraph, or amend the
register.

**Novelty.** A novelty claim is an absence claim. Check prior art in more than
one phrasing — the same object carries different names in different fields, so
a term-scan zero is evidence about the word, not the object.

## Running the checks

```sh
python3 ~/.nullius/gates/provenance.py --paper PAPER_DIR --check
python3 ~/.nullius/gates/proseleak.py  --sections DIR --repo REPO --check
python3 ~/.nullius/gates/ownership_gate.py --audit SECTIONS_DIR
```

All three exit non-zero on failure and print file:line for every hit.

Build the maths-fidelity index the depth gate consults — without it, that half
of the gate is inert:

```sh
python3 ~/.nullius/tools/extraction_integrity.py sweep --shelf PAPERS_DIR
```
