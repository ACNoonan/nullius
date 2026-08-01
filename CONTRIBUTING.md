# Contributing

## The one rule that is specific to this project

**A gate must be demonstrated to fail before it is merged.**

A check that cannot come out wrong is not evidence, and a gate that quietly
stopped firing looks exactly like a gate that has nothing to complain about.
So every pull request that adds or changes a gate must include, in
`tests/test_gates.py`, a matched pair:

- an input that **must be blocked**, and
- a near-identical input that **must be allowed**

A test that only asserts blocking passes just as well against a gate that
blocks everything. A test that only asserts allowing passes against a gate
that does nothing. Neither alone tells you the gate discriminates.

CI enforces this from the other side: a `mutation` job breaks a gate on purpose
and **fails if the suite still passes**. If you add a gate whose behaviour no
test observes, that job is where you find out.

## The two invariants

**Fail open.** Every gate must allow the write on any internal error,
unreadable input, or unexpected shape. Wrap your entry point; return 0 on
anything unexpected. A gate that blocks work because the gate broke gets
uninstalled within a week, and then nothing is enforced at all. There are
fail-open tests for all five gates — add one for yours.

**Opt in.** Gates apply only inside a tree holding `.nullius.toml`. Never
widen that. Somebody has this installed globally and does not want their
unrelated repos linted.

## Precision matters more than recall

A gate that cries wolf is deleted, and then it has a recall of zero. When
`proseleak` was first run against a real paper it flagged six things, of which
two were real — 33%. Three words came out of its list because they had
legitimate scientific senses (`pre-registered` is normal open-science
vocabulary; "the harness" was a *simulation* harness). That tuning is recorded
in the source next to the list, with the measured number that motivated it.

If you add a pattern, say in a comment what it fired on and what it should not.

## Before you open a PR

```sh
python3 tests/test_gates.py          # 26 checks, all must pass
shellcheck -s sh adapters/git/*      # if you touched the shell
```

Run the mutation check by hand if you changed gate logic: break your gate,
confirm the suite goes red, restore it.

## Adding a depth label

The read-depth register is deliberately small: `full`, `targeted`,
`fetch-summary`, `snippet`, `unsearched`. Adding a value is a change to the
standard, not a config tweak — open an issue describing the read it describes
and why no existing label covers it. `targeted` earned its place by being
independently invented four times in one bibliography.

## Scope

This is a limiter. Proposals that make it *help* you write — generate prose,
suggest citations, draft sections — are out of scope by design, not by
oversight.
