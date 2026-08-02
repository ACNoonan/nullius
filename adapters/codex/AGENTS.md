# nullius — Codex adapter

Paste into your project `AGENTS.md`, or `~/.codex/AGENTS.md` for every project.

**Read this first.** Codex has no facility to intercept and refuse a write, so
everything below is an *instruction*, not enforcement. It will be followed most
of the time and silently skipped some of the time, which is exactly the failure
mode the gates exist to catch. **Install `adapters/git/pre-commit` as well.**
That one refuses the commit regardless of what any model decided to do.

---

## Research discipline (nullius)

These apply in any repository holding a `.nullius.toml`.

**A source's content may not enter the work until it has been read in full.**
"Entering the work" includes gating on one of its numbers, adopting its metric
or data split, using its dataset, and pruning or ranking a branch on what it
claims. A model's summary of a paper is never a premise.

**Record depth per source**, using exactly this vocabulary:

- `full` — the whole text was read; an extraction exists on disk
- `targeted` — part was read, and the entry states which part and what was *not*
- `fetch-summary` — a summary was retrieved; the text was not read
- `snippet` — a fragment only
- `unsearched` — not looked at

A summarizer's *"the paper doesn't mention X"* is not evidence of absence. Say
"grepped the full text", or say you didn't.

**An artifact existing is not an artifact being right.** A PDF text layer
routinely deletes mathematics with nothing to warn you: `C(γ*)` extracts as
`C ( )`, `δ_t` as `t` — a *different variable that also exists in the paper*, so
the corrupted line stays syntactically valid. A `.pdf` that is really a
Cloudflare block page is an artifact that is not the paper at all. Where a paper
is flagged maths-unsafe, a `full` claim must state the channel the mathematics
came from — `maths: image`, `maths: unread`, or `maths: n/a`. Never re-run the
extraction in another mode as a control: every mode reads the same layer and
agrees with the error. The page image is the only authority.

**Verify the instrument before trusting the number.** Before reporting a result,
state at least one check that *could have come out wrong*, and what a failure
would have looked like. A check that cannot fail is not evidence, and reporting
its pass as confirmation is the error.

**Do not report a RESULT while its pre-registered commitments are undischarged.**
Either discharge them or say in writing which are outstanding.

**Do not mint an identifier in a namespace nobody declared.** If a project keeps
a `VOCAB.md`, add the row before using the name.

**An effective sample size is meaningless without its marginal.** Never write one
without naming what is being resampled.

**Do not concede more than you owe.** An over-concession is as damaging as an
over-claim and strictly harder to catch, because no referee's incentive runs that
way. If a project keeps an ownership register, do not write "we claim none of
this" over a source the register records as *not* holding it — name the
exclusion's scope in the same paragraph, or amend the register.

**Never let internal vocabulary reach published prose** — lane IDs, workflow
words, tool codenames. Run `gates/proseleak.py` before shipping any document.

## Before you claim novelty

A novelty claim is an absence claim wearing a suit. Check prior art before
relying on "this is new", "nobody has measured X", "the SOTA is Y". Never a
single query — the same object routinely carries different names in different
fields, so a term-scan zero is evidence about the word, not the object.
