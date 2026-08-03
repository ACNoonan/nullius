# nullius

[![ci](https://github.com/ACNoonan/nullius/actions/workflows/ci.yml/badge.svg)](https://github.com/ACNoonan/nullius/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![no dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](#install)

*Nullius in verba* — "take nobody's word for it." The Royal Society's motto since
1660, and the oldest statement of the thing this tool enforces.

**Checks that refuse to let an AI-assisted research claim ship until an artifact
backs it.**

The motto was written against argument from authority. It applies without
amendment to a model: a summary of a paper is not the paper, and a note saying
you read something is a claim, not evidence. The gates below take nobody's
word for it — not the model's, and not yours.

Not a prompt pack. Not a set of instructions asking a model to be careful. Eight
programs that read what is about to be written and **block the write** when the
claim has nothing behind it.

---

## Why this exists

One scalar function has been rediscovered independently in at least eight
fields since 1950 — survey sampling, psychometrics, quantitative genetics,
cluster-trial biostatistics, econometrics, diagnostic radiology, copula theory,
risk management — under eight different names, by researchers who do not cite
one another. Each field solved its own case correctly and stopped.

**Nobody was dumb. What failed was routing.** A correct result in one field had
no route into the next, and the overlaps sat unnoticed for seventy years
because reading across a boundary is expensive and nobody is paid to do it.

That is the part that just changed. A model is a cross-field retrieval and
translation instrument, and it makes the connective work tractable for one
person in a week. It also makes **confident, well-formed, wrong work** tractable
in an afternoon — which is why mathematicians are right to be suspicious of what
is currently arriving in their inboxes. They have no way to tell a disciplined
outsider from a generator.

This is an attempt at that signal.

### A harness is a limiter

When models were weak, a harness was scaffolding — context and instructions to
get a competent answer out. Models are not weak now, so the bottleneck moved,
and what a harness is *for* moved with it:

> Its job is to stop a capable model from being confidently wrong at speed.

Every gate here blocks. Not one helps you write. That is the design, not an
omission.

The failure they target is not hallucination. It is the **plausible premise
nobody checked** — a novelty claim that was never searched, a number quoted from
a summary instead of a paper, a result reported against commitments still
undischarged. These survive review because they read correctly. They fail
against an artifact on disk, which is the only thing these gates consult.

## What each one refuses

| gate | refuses |
|---|---|
| `research_depth_gate` | a `depth: full` claim on a source with no extraction on disk — **or** one whose extraction is known to have eaten the mathematics, unless the claim says where the maths came from |
| `citation_attribution_gate` | a bibliography entry whose authors contradict the artifact it cites |
| `prereg_commitment_gate` | a RESULT written while its pre-registered commitments sit undischarged |
| `vocab_gate` | an identifier minted into a namespace nobody declared |
| `marginal_gate` | an effective-sample-size claim with no marginal named |
| `ownership_gate` | a concession — "we claim none of this" — over a source the ownership register says does *not* hold it |
| `provenance` *(build)* | a paper whose bibliography has undeclared or off-register read depths |
| `proseleak` *(build)* | internal lane IDs and workflow vocabulary reaching published prose |

`ownership_gate` is the one that runs in the *other* direction. Every gate above
it guards against claiming too much; that one guards against giving too much
away. An over-concession is strictly harder to catch, because no referee's
incentive runs that way — it took a hand audit, late, after a false concession to
a 1965 textbook had already driven a project-level decision.

### The instrument behind the depth gate

`tools/extraction_integrity.py sweep` classifies a shelf of PDFs and writes the
index the depth gate consults. It exists because **artifact presence is not
artifact fidelity**: a sweep of 312 papers found 48 whose text layer silently
loses mathematics, and six `.pdf` files that were Cloudflare block pages rather
than papers — one with an 85 KB `.txt` beside it. Born-digital LaTeX is affected,
not just scans: `C(γ*)` extracts as `C ( )` and `δ_t` as `t`, a different variable
that also exists in the paper, so the corrupted line stays syntactically valid.

There is no text pipeline that recovers displayed mathematics — `-layout`, `-raw`
and per-page all read the same layer and agree with the error. The tool triages
and routes to the page image; it never repairs an extraction. With no index
built, that half of the depth gate is silently inert.

## The two rules everything here obeys

**1. Fail open.** Every gate allows the write on any internal error, unreadable
input, or unexpected shape. A gate that blocks work because the gate broke gets
deleted within a week, and then nothing is enforced at all. Being wrong in the
permissive direction is survivable; being wrong in the blocking direction is
fatal to the tool.

**2. Opt in per repository.** A tree is governed only if it holds a
`.nullius.toml` at its root. Installed globally, these do nothing to any
repo that did not ask. Consent lives in the checkout, so a collaborator who
clones gets the same behaviour.

## Install

```sh
git clone https://github.com/<you>/nullius ~/.nullius
touch /path/to/your/repo/.nullius.toml     # opt the repo in
sh ~/.nullius/adapters/git/install.sh --repo /path/to/your/repo
```

**Use the installer, not `ln -s`.** If `core.hooksPath` is set — husky,
lefthook, the pre-commit framework and most dotfiles repos all set it — git
never reads `.git/hooks/`, so the symlink everyone reaches for does nothing.
It fails silently *and permissively*: every commit passes and the repo looks
gated. The installer resolves the real hook directory, chains any existing
pre-commit rather than clobbering it, and finishes with a canary commit that
**must be refused** — if the canary is allowed, the install reports FAILED
instead of pretending to have worked.

Then wire whichever agent you use — see `adapters/`.

| platform | enforcement | how |
|---|---|---|
| Claude Code | **blocks the write** | `PreToolUse` hooks; `adapters/claude-code/` |
| git (any agent, any editor) | **blocks the commit** | `adapters/git/pre-commit` |
| Cursor | advisory | skill + rule; `adapters/cursor/` |
| Codex | advisory | `AGENTS.md` fragment; `adapters/codex/` |

**Be clear-eyed about that table.** Only Claude Code can currently intercept and
refuse a write before it lands. Cursor rules and Codex `AGENTS.md` are
instructions to a model that may or may not follow them — useful, not
enforcement. **The portable enforcement layer is the git hook**, which does not
care which agent or human produced the diff. If you install one thing, install
that.

### Environment

| variable | what it sets | default |
|---|---|---|
| `NULLIUS_LEDGER` | where firings are appended | `$XDG_STATE_HOME/nullius/gate-firings.jsonl`, or `~/.claude/hooks/gate-firings.jsonl` if that file already exists |
| `NULLIUS_CONTROL` | marks every firing beneath it as a deliberate control | unset |
| `NULLIUS_SHELF` | the PDF shelf `extraction_integrity.py` sweeps | `papers/` under the governed root |

The ledger is the artifact you will later cite, and **a firing you provoked on
purpose is written exactly like one a gate caught.** That is not hypothetical:
177 of 220 rows in the author's own ledger were this project's test suite, and
`provenance.py` would have stamped all 220 into a paper. The suite now redirects
itself and the stamp reports what it excluded.

Location filtering handles fixtures, but it cannot reach the case that matters
most — a **positive control**, which replays real text through a real gate at a
real path to prove the gate refuses it. Everything about that row is genuine
except the intent, and intent is not in the file. So the control declares
itself:

```sh
tools/selftest.py ownership_gate paper/sections/08.md < the-offending-text.md
```

That sets `NULLIUS_CONTROL` for you, so the row is labelled and the stamp skips
it. **Use the tool rather than the variable.** A flag you have to remember is a
flag you forget, and forgetting counts a control as a real catch — the same
inflating direction as every other error this release fixed. Because the tool
cannot be used without labelling, an *unlabelled* row stays worth trusting.
`selftest.py` exits non-zero when a gate disagrees with what you predicted, so a
gate that has quietly stopped firing fails CI instead of looking like a clean
repo.

## Evidence

`evidence/EVIDENCE.md` records every firing recovered from eight days of real
research sessions — **97 unique denials across 371 transcripts**, with a
rejection table showing what a naive count would have overstated and why.

That figure went **down** in this release, and the reason is worth stating
plainly, because it is the failure this project exists to catch.

Earlier tables were built by searching transcripts for the denial text. But a
session that *works on these gates* fills its transcript with their denial
strings — the diff, the file being written, the test harness printing its
positive controls — and a text search cannot tell that from a gate refusing
someone's claim. The generator now identifies a firing by its structure (an
errored hook result whose text begins with the marker) rather than by matching
text. Scored against the old filters on one identical scan, that took the count
from **127 to 96** — 31 rows had been this project quoting itself. `grep BLOCKED`
over the same transcripts still returns 6.4x the real number. (The committed
table tracks a live corpus, so its total moves as sessions accrue; 127→96 is the
paired comparison.)

Two corrections fall out of that, both against our own earlier claims:

- **`ownership_gate` has never fired on live work.** The over-concession it was
  built for was caught by hand, and the gate was then validated by replaying
  that section as a positive control. A previous README read those replays as
  six firings. It catches the case; it has not yet caught a new one.
- **The depth gate's maths-fidelity half likewise has no live firing** — its two
  recorded hits were writes to a deliberate probe file.

The gates' claim to work is not that they exist, and not that a log is long. It
is that they fired, on specific files, on specific dates, against a working
researcher who wanted to write something else — and that the count of those
firings is itself produced by an instrument that was checked.

## License

MIT.
