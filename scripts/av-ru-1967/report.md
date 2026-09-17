# av-ru.1967 pipeline — batch-2 review status (2026-09-17)

Status against `av-ru-1967-review-batch-2-2026-09-17.md` (repo root), as of
commit `6a62f91` on `av-ru-1967-parsing`.

## Done

- **P0. Исправить дедупликацию до confidence-гейта** — two-pass collect-then-rank
  dedup in `build_dataset.py` (commit `2efb9c0`).
- **P0. Пересмотреть смысл `confidence: high`** — added `detect_parse_issues()`
  content gate (raw structural markers, av/ru leaks, russian-word-as-headword)
  on top of segmentation's boundary confidence; only entries clean on both
  are published (commit `9f4425b`).
- **P0. Не терять provenance в review queue** (partial) — `needs_review.jsonl`
  rows now carry `column`, `top`, `reasons`, `prev_word`, `next_word`,
  `continues_next_page`, `word_raw`, `raw_text`, `entry` (commit `05a40dd`).
  Still missing: bbox/x-coords, source token-range, HTML cards.
- **P0. Классификация order-регрессий** — `check_order.py`'s `classify()`
  buckets every regression into `stress-glyph-unresolved` /
  `hyphen-reduplication` / `false-headword` / `unclassified` (commit `66a9e66`).
- **P1. Исправить декларацию полного pipeline** — `quality_scan.py` is now a
  hard 0-tolerance gate; `check_order.py` and `resolve_references.py` are
  baseline gates (`baseline.py` / `baselines.json`) that fail the build on
  regression; `compare_with_av_ru.py` is wired in as an explicit, clearly
  optional diagnostic. `build_all.sh`/`README.md` updated accordingly
  (commit `48d85cb`).
- **P1. Довести forms до семантически корректной структуры** —
  `parse_forms_raw()` rewritten to drop case/mood/declension-class grammar
  markers and separator punctuation instead of leaking them into `forms[]`;
  new `malformed-form-value` content gate catches mid-word OCR corruption
  that survived the marker cleanup. All three acceptance criteria (0 grammar
  markers / 0 separator punctuation / 0 unexplained digits in `forms[]`)
  verified on the published file (commit `6a62f91`).
- **Triage of the 13 unclassified high/high order regressions** — reviewed
  each individually; none has a safe, generalizable automated fix (source
  dictionary layout choices, one-off OCR errors, or already-known diagnostic
  limitations). No code change made; documented in
  `/memories/repo/av-ru-1967-parsing.md` (Step 38).

## Current metrics (published `data/av-ru.1967.jsonl`)

- 9858 entries, 0 schema violations, 0 `quality_scan` findings.
- `needs_review.jsonl`: 3632 rows (gitignored).
- `check_order.py`: 900 total regressions (131 high/high), broken down as
  391 stress-glyph-unresolved / 61 hyphen-reduplication / 9 false-headword /
  439 unclassified (13 high/high) — tracked as the current baseline ceiling
  in `baselines.json`.
- `resolve_references.py`: 1204 unresolved `see_also`/`from` targets —
  tracked the same way.

## Not started (out of scope for this round — larger undertakings)

1. **Per-page coverage ledger** for all 597 pages (candidates,
   accepted/review/rejected counts, first/last headword, carry-in/out, max
   span length) — needs a new data structure/output format.
2. **HTML review cards** with scan image + proposed JSON for medium/low and
   boundary cases — needs pdfplumber image export + templating.
3. **Persistent (non-gitignored) decision ledger** that survives re-runs and
   reports conflicts if a span changed — needs an architectural decision on
   where it lives (everything under `tmp/` is currently gitignored/ephemeral).

## Explicitly deferred by the review itself (do not start)

`gender_forms` population, full stress restoration, `sources.json`
registration, license decision, site publication integration.
