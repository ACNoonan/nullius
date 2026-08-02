# Gate firings — recovered from Claude Code transcripts

Scanned **169 transcripts** (155,658 records) across
the scanned projects.

**127 unique denials.** Every count below is deduplicated; the raw
text-match count is 2.9x higher and is not usable.

## What was excluded, and why

| rejected | reason |
|---:|---|
| 164 | replayed duplicate |
| 30 | unrecognised BLOCKED prose |
| 24 | template in hook source |
| 23 | hook source read |
| 4 | deliberate hooktest |

Each of those 5 is a way a naive `grep BLOCKED` overcounts. The hook
source files contain the denial strings verbatim, so any session that read a
hook inflates the count; templates carry an uninstantiated `{name}`;
transcripts replay on resume and compaction.

## By gate

| n | gate |
|---:|---|
| 59 | `vocab-gate` |
| 35 | `research-depth-gate` |
| 12 | `prereg-commitment-gate` |
| 7 | `citation-attribution-gate` |
| 6 | `marginal-gate` |
| 6 | `ownership-gate` |
| 2 | `research-depth-gate/maths` |

## By day

| day | firings |
|---|---:|
| 2026-07-27 | 4 |
| 2026-07-28 | 8 |
| 2026-07-29 | 22 |
| 2026-07-30 | 36 |
| 2026-07-31 | 9 |
| 2026-08-01 | 32 |
| 2026-08-02 | 16 |

*Timestamps are UTC; the final day's rows are the prior evening local time.*

## Every firing

*Target filenames are redacted — they name unpublished work. The token is a
stable hash, so the same file is recognisable across rows. Dates, gates and
violation types are verbatim.*

| when (UTC) | gate | target | violation |
|---|---|---|---|
| 2026-07-27 19:37:47 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-27 19:43:15 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-27 23:05:11 | `research-depth-gate` | `«58b5».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-27 23:55:30 | `research-depth-gate` | `«2b78».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 00:30:40 | `research-depth-gate` | `«ecec».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 16:43:46 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 16:44:42 | `prereg-commitment-gate` | `?` | T-01.md reports a RESULT with 1/1 §3 commitments undischarged. |
| 2026-07-28 16:44:51 | `prereg-commitment-gate` | `?` | T-02.md reports a RESULT but has no ```commitments block. |
| 2026-07-28 20:14:37 | `research-depth-gate` | `«0440».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 21:36:02 | `research-depth-gate` | `«07a0».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-28 23:45:35 | `prereg-commitment-gate` | `«6a50».md` | TF-style9.md reports a RESULT but has no ```commitments block. |
| 2026-07-28 23:48:57 | `prereg-commitment-gate` | `«6a50».md` | TF-style9.md reports a RESULT with 1/3 §3 commitments undischarged. |
| 2026-07-29 04:47:19 | `research-depth-gate` | `«fa3d».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 05:17:00 | `prereg-commitment-gate` | `«53c6».md` | MR-06.md reports a RESULT but has no ```commitments block. |
| 2026-07-29 05:17:41 | `prereg-commitment-gate` | `«53c6».md` | MR-06.md reports a RESULT with 3/3 §3 commitments undischarged. |
| 2026-07-29 14:27:27 | `prereg-commitment-gate` | `?` | SA-03.md reports a RESULT with 7/7 §3 commitments undischarged. |
| 2026-07-29 15:38:06 | `research-depth-gate` | `«d27e».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 16:08:38 | `research-depth-gate` | `«446c».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 16:09:38 | `prereg-commitment-gate` | `«9c0c».md` | TF-style11.md reports a RESULT with 3/3 §3 commitments undischarged. |
| 2026-07-29 16:18:47 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 16:26:54 | `vocab-gate` | `?` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 18:45:39 | `vocab-gate` | `«3d5f».py` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 19:26:01 | `research-depth-gate` | `«0440».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 19:46:47 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-29 21:06:49 | `prereg-commitment-gate` | `«53c6».md` | MR-06.md reports a RESULT with 3/3 §3 commitments undischarged. |
| 2026-07-29 21:08:49 | `vocab-gate` | `«268f».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:12:45 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:13:51 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:44:02 | `vocab-gate` | `«3dd3».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:47:29 | `vocab-gate` | `«ecec».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 22:50:01 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-29 23:01:10 | `citation-attribution-gate` | `?` | a bibliography entry contradicts the paper on disk. |
| 2026-07-29 23:02:18 | `citation-attribution-gate` | `?` | a bibliography entry contradicts the paper on disk. |
| 2026-07-29 23:04:44 | `vocab-gate` | `«048b».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 00:20:45 | `vocab-gate` | `«4aa7».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 00:20:53 | `vocab-gate` | `«c21b».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 00:59:20 | `research-depth-gate` | `«b2d1».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 01:54:09 | `vocab-gate` | `«60c2».py` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 01:56:54 | `vocab-gate` | `«254c».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 03:03:42 | `vocab-gate` | `«5142».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:01:23 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:02:43 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:08:10 | `vocab-gate` | `«0c35».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:09:34 | `research-depth-gate` | `«0c35».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 04:19:41 | `vocab-gate` | `«4aa7».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 04:42:36 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 05:33:38 | `research-depth-gate` | `«07a0».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 05:34:13 | `citation-attribution-gate` | `«07a0».md` | a bibliography entry contradicts the paper on disk. |
| 2026-07-30 05:46:04 | `research-depth-gate` | `«b2d1».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 06:36:38 | `vocab-gate` | `«4aa7».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 13:06:10 | `vocab-gate` | `«4aa7».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 13:38:15 | `vocab-gate` | `«0ff1».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 13:52:24 | `vocab-gate` | `«4aa7».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 13:58:44 | `vocab-gate` | `«51a8».py` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 14:52:24 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 14:53:15 | `research-depth-gate` | `«7bfa».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 14:53:16 | `research-depth-gate` | `«d27e».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-30 15:00:59 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 15:10:14 | `citation-attribution-gate` | `«07a0».md` | a bibliography entry contradicts the paper on disk. |
| 2026-07-30 15:18:59 | `marginal-gate` | `?` | an effective-sample-size claim with no marginal named. |
| 2026-07-30 15:19:57 | `marginal-gate` | `?` | an effective-sample-size claim with no marginal named. |
| 2026-07-30 15:26:41 | `vocab-gate` | `«172b».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 15:36:41 | `vocab-gate` | `«b6c3».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 15:38:26 | `vocab-gate` | `«1436».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 15:59:53 | `marginal-gate` | `«685a».md` | an effective-sample-size claim with no marginal named. |
| 2026-07-30 16:11:12 | `vocab-gate` | `«0ff1».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 16:17:52 | `marginal-gate` | `«d067».md` | an effective-sample-size claim with no marginal named. |
| 2026-07-30 16:21:40 | `vocab-gate` | `«0ff1».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-30 23:35:10 | `prereg-commitment-gate` | `«4aa7».md` | RESULTS.md reports a RESULT but has no ```commitments block. |
| 2026-07-30 23:38:12 | `vocab-gate` | `«4aa7».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-31 01:34:53 | `marginal-gate` | `«56cd».md` | an effective-sample-size claim with no marginal named. |
| 2026-07-31 01:48:07 | `vocab-gate` | `«cf99».txt` | an identifier with no entry in VOCAB.md. |
| 2026-07-31 02:55:47 | `vocab-gate` | `«9fb5».md` | an identifier with no entry in VOCAB.md. |
| 2026-07-31 03:28:23 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-31 03:28:27 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-31 03:28:31 | `vocab-gate` | `?` | an identifier with no entry in VOCAB.md. |
| 2026-07-31 03:33:12 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-07-31 17:02:48 | `research-depth-gate` | `«ec1f».md` | a `depth: full` claim with no artifact behind it. |
| 2026-07-31 22:18:55 | `vocab-gate` | `«9d98».py` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 02:32:18 | `prereg-commitment-gate` | `«602a».md` | SA-07.md reports a RESULT with 5/5 §3 commitments undischarged. |
| 2026-08-01 14:09:15 | `vocab-gate` | `«a628».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 14:12:47 | `vocab-gate` | `«0ff1».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 14:13:45 | `vocab-gate` | `«2b78».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 14:22:43 | `vocab-gate` | `«0ff1».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 14:24:01 | `vocab-gate` | `«0ff1».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 14:32:59 | `vocab-gate` | `«b050».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 14:44:47 | `vocab-gate` | `«9b24».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 15:47:18 | `vocab-gate` | `«9043».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 16:10:56 | `vocab-gate` | `«1232».py` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 16:51:02 | `vocab-gate` | `«bbe7».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 16:56:37 | `prereg-commitment-gate` | `«1d68».md` | READ-g06-diagonals.md reports a RESULT but has no ```commitments block. |
| 2026-08-01 17:21:13 | `marginal-gate` | `«56cd».md` | an effective-sample-size claim with no marginal named. |
| 2026-08-01 17:27:11 | `research-depth-gate` | `«6ee8».md` | a `depth: full` claim with no artifact behind it. |
| 2026-08-01 18:01:56 | `vocab-gate` | `«2931».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 18:09:33 | `vocab-gate` | `«5c95».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 18:29:21 | `research-depth-gate` | `«6ee8».md` | a `depth: full` claim with no artifact behind it. |
| 2026-08-01 18:32:21 | `research-depth-gate` | `«2931».md` | a `depth: full` claim with no artifact behind it. |
| 2026-08-01 18:37:44 | `vocab-gate` | `«6c4c».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 19:04:43 | `vocab-gate` | `«d27e».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 19:10:36 | `vocab-gate` | `«a628».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 19:18:56 | `vocab-gate` | `«a628».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 19:38:15 | `vocab-gate` | `«8af1».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 19:43:34 | `vocab-gate` | `«8af1».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 19:49:20 | `vocab-gate` | `«4aa7».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 19:56:43 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-08-01 19:57:56 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-08-01 19:58:13 | `vocab-gate` | `«35bf».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 19:59:44 | `vocab-gate` | `«2b78».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-01 20:20:42 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-08-01 20:24:48 | `citation-attribution-gate` | `?` | a bibliography entry contradicts the paper on disk. |
| 2026-08-01 20:26:49 | `ownership-gate` | `?` | an ownership concession contradicts OWNERSHIP.md. |
| 2026-08-02 02:46:42 | `ownership-gate` | `?` | an ownership concession contradicts OWNERSHIP.md. |
| 2026-08-02 14:29:35 | `vocab-gate` | `«1c5e».py` | an identifier with no entry in VOCAB.md. |
| 2026-08-02 16:42:51 | `vocab-gate` | `«4b91».md` | an identifier with no entry in VOCAB.md. |
| 2026-08-02 18:07:46 | `research-depth-gate` | `?` | a `depth: full` claim resting on an artifact whose text layer |
| 2026-08-02 18:08:03 | `ownership-gate` | `?` | an ownership concession contradicts OWNERSHIP.md. |
| 2026-08-02 18:09:29 | `research-depth-gate` | `«3253».py` | a `depth: full` claim with no artifact behind it. |
| 2026-08-02 18:11:26 | `research-depth-gate` | `?` | a `depth: full` claim resting on an artifact whose text layer |
| 2026-08-02 18:11:26 | `research-depth-gate` | `«3253».py` | a `depth: full` claim resting on an artifact whose text layer |
| 2026-08-02 18:11:36 | `research-depth-gate` | `?` | a `depth: full` claim with no artifact behind it. |
| 2026-08-02 18:11:48 | `research-depth-gate/maths` | `?` | a `depth: full` claim resting on an artifact whose text layer is known to lose mathematics. |
| 2026-08-02 18:12:26 | `citation-attribution-gate` | `«537e».py` | a bibliography entry contradicts the paper on disk. |
| 2026-08-02 18:12:31 | `citation-attribution-gate` | `«537e».py` | a bibliography entry contradicts the paper on disk. |
| 2026-08-02 18:13:16 | `ownership-gate` | `?` | an ownership concession contradicts {REGISTER_NAME}. |
| 2026-08-02 18:13:16 | `ownership-gate` | `«f73c».py` | an ownership concession contradicts {REGISTER_NAME}. |
| 2026-08-02 18:13:26 | `ownership-gate` | `?` | an ownership concession contradicts OWNERSHIP.md. |
| 2026-08-02 18:15:13 | `research-depth-gate/maths` | `?` | a `depth: full` claim resting on an artifact whose text layer is known to lose mathematics. |
