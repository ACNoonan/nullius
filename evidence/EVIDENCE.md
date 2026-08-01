# Gate firings — recovered from Claude Code transcripts

Scanned **159 transcripts** (163,758 records) across the
two private research projects.

**77 unique denials.** Every count below is deduplicated; the raw
text-match count is roughly 2.4x higher and is not usable.

## What was excluded, and why

| rejected | reason |
|---:|---|
| 105 | replayed duplicate |
| 24 | template in hook source |
| 22 | unrecognised BLOCKED prose |
| 16 | hook source read |
| 4 | deliberate hooktest |

Each of those five is a way a naive `grep BLOCKED` overcounts. The hook
source files contain the denial strings verbatim, so any session that read a
hook inflates the count; templates carry an uninstantiated `{name}`;
transcripts replay on resume and compaction.

## By gate

| n | gate |
|---:|---|
| 35 | `vocab-gate` |
| 23 | `research-depth-gate` |
| 10 | `prereg-commitment-gate` |
| 5 | `marginal-gate` |
| 4 | `citation-attribution-gate` |

## By day

| day | firings |
|---|---:|
| 2026-07-27 | 4 |
| 2026-07-28 | 8 |
| 2026-07-29 | 22 |
| 2026-07-30 | 36 |
| 2026-07-31 | 7 |

*Timestamps are UTC; the final day's rows are the prior evening local time.*

## Every firing

*Target filenames are redacted: they name unpublished work. Dates, gates and violation types are verbatim.*


| when (UTC) | gate | target | violation |
|---|---|---|---|
| 2026-07-27 19:37:47 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-27 19:43:15 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-27 23:05:11 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-27 23:55:30 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 00:30:40 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 16:43:46 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 16:44:42 | `prereg-commitment-gate` | `?` | T-01.md reports a RESULT with 1/1 §3 commitments undischarged. |
| 2026-07-28 16:44:51 | `prereg-commitment-gate` | `?` | T-02.md reports a RESULT but has no ```commitments block. |
| 2026-07-28 20:14:37 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 21:36:02 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 23:45:35 | `prereg-commitment-gate` | `<lane>.md` | <lane>.md reports a RESULT but has no ```commitments block. |
| 2026-07-28 23:48:57 | `prereg-commitment-gate` | `<lane>.md` | <lane>.md reports a RESULT with 1/3 §3 commitments undischarged. |
| 2026-07-29 04:47:19 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 05:17:00 | `prereg-commitment-gate` | `<lane>.md` | <lane>.md reports a RESULT but has no ```commitments block. |
| 2026-07-29 05:17:41 | `prereg-commitment-gate` | `<lane>.md` | <lane>.md reports a RESULT with 3/3 §3 commitments undischarged. |
| 2026-07-29 14:27:27 | `prereg-commitment-gate` | `?` | <lane>.md reports a RESULT with 7/7 §3 commitments undischarged. |
| 2026-07-29 15:38:06 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 16:08:38 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 16:09:38 | `prereg-commitment-gate` | `<lane>.md` | <lane>.md reports a RESULT with 3/3 §3 commitments undischarged. |
| 2026-07-29 16:18:47 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 16:26:54 | `vocab-gate` | `?` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 18:45:39 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 19:26:01 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 19:46:47 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 21:06:49 | `prereg-commitment-gate` | `<lane>.md` | <lane>.md reports a RESULT with 3/3 §3 commitments undischarged. |
| 2026-07-29 21:08:49 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:12:45 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:13:51 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:44:02 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:47:29 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:50:01 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 23:01:10 | `citation-attribution-gate` | `?` | a bibliography entry contradicts the paper on disk. |
| 2026-07-29 23:02:18 | `citation-attribution-gate` | `?` | a bibliography entry contradicts the paper on disk. |
| 2026-07-29 23:04:44 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 00:20:45 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 00:20:53 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 00:59:20 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 01:54:09 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 01:56:54 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 03:03:42 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:01:23 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:02:43 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:08:10 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:09:34 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 04:19:41 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:42:36 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 05:33:38 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 05:34:13 | `citation-attribution-gate` | `<redacted>` | a bibliography entry contradicts the paper on disk. |
| 2026-07-30 05:46:04 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 06:36:38 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 13:06:10 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 13:38:15 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 13:52:24 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 13:58:44 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 14:52:24 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 14:53:15 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 14:53:16 | `research-depth-gate` | `<redacted>` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 15:00:59 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 15:10:14 | `citation-attribution-gate` | `<redacted>` | a bibliography entry contradicts the paper on disk. |
| 2026-07-30 15:18:59 | `marginal-gate` | `?` | an effective-sample-size claim with no marginal named. |
| 2026-07-30 15:19:57 | `marginal-gate` | `?` | an effective-sample-size claim with no marginal named. |
| 2026-07-30 15:26:41 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 15:36:41 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 15:38:26 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 15:59:53 | `marginal-gate` | `<redacted>` | an effective-sample-size claim with no marginal named. |
| 2026-07-30 16:11:12 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 16:17:52 | `marginal-gate` | `<redacted>` | an effective-sample-size claim with no marginal named. |
| 2026-07-30 16:21:40 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 23:35:10 | `prereg-commitment-gate` | `<redacted>` | RESULTS.md reports a RESULT but has no ```commitments block. |
| 2026-07-30 23:38:12 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-31 01:34:53 | `marginal-gate` | `<redacted>` | an effective-sample-size claim with no marginal named. |
| 2026-07-31 01:48:07 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-31 02:55:47 | `vocab-gate` | `<redacted>` | an identifier with no entry in VOCAB.md. |
| 2026-07-31 03:28:23 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-31 03:28:27 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-31 03:28:31 | `vocab-gate` | `?` | an identifier with no entry in VOCAB.md. |
| 2026-07-31 03:33:12 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
