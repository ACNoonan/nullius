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

**Instrument.** Before reporting a number, state a check that *could have come
out wrong* and what its failure would have looked like. A check that cannot
fail is not evidence.

**Commitments.** No RESULT while its pre-registered commitments are
undischarged.

**Vocabulary.** No identifier in an undeclared namespace. No internal lane IDs
or workflow words in published prose.

**Marginal.** No effective sample size without naming what is resampled.

**Novelty.** A novelty claim is an absence claim. Check prior art in more than
one phrasing — the same object carries different names in different fields, so
a term-scan zero is evidence about the word, not the object.

## Running the checks

```sh
python3 ~/.nullius/gates/provenance.py --paper PAPER_DIR --check
python3 ~/.nullius/gates/proseleak.py  --sections DIR --repo REPO --check
```

Both exit non-zero on failure and print file:line for every hit.
