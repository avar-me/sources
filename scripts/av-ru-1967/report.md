# av-ru.1967 pipeline — review status (2026-09-17)

Status against `av-ru-1967-review-batch-2-2026-09-17.md` and
`av-ru-1967-review-batch-3-2026-09-17.md` (repo root), as of commit
`cbbcfa6` on `av-ru-1967-parsing`. Following batch-3's own instruction: a
requirement is only marked `Done` if fully closed; `Partial` means real,
verified progress but the item's own acceptance criteria aren't all met yet.

## Batch-2 — Done

- **P0. Исправить дедупликацию до confidence-гейта** — two-pass collect-then-rank
  dedup in `build_dataset.py` (commit `2efb9c0`).
- **P0. Пересмотреть смысл `confidence: high`** — `detect_parse_issues()`
  content gate on top of segmentation's boundary confidence (commit `9f4425b`).
- **P0. Не терять provenance в review queue** (partial then, superseded by
  batch-3 item 1's `check_accepted.py` + provenance file work below).
- **P0. Классификация order-регрессий** — `check_order.py`'s `classify()`
  (commit `66a9e66`), later split into `suggested_category`/
  `confirmed_category` by batch-3 item 10.
- **P1. Исправить декларацию полного pipeline** — hard/baseline gates
  wired into `build_all.sh` (commit `48d85cb`).
- **P1. Довести forms до семантически корректной структуры** — grammar
  markers/punctuation/digits removed from `forms[]` (commit `6a62f91`).
- Triage of the (then-)13 unclassified high/high order regressions —
  migrated into the batch-3 persistent decision ledger (see below).

## Batch-3 P0 — status

1. **Реализовать независимые gates для accepted/review/draft** —
   **Partial**. New `check_accepted.py` checks ONLY the published file in
   its own order (independent of `check_order.py`/`resolve_references.py`,
   which still check the full draft): order regressions (408, matches the
   reviewer's own independent count), suspicious-headword language
   (dictionary hint + content-signal, not a blacklist), oversized spans,
   provenance completeness (hard 0), `see_also` link targets by origin/
   destination. Still dictionary-based rather than the full layout/font
   structural classifier the review ultimately wants (see item 6).
2. **Построить per-page coverage ledger** — **Done**. New
   `build_page_ledger.py` covers all 597 pages, committed as
   `data/av-ru.1967.page_ledger.jsonl`. Page 551 (the only zero-draft-
   article page) investigated and resolved: confirmed via rendered PDF
   scans to be a legitimate continuation of the p.550 "цебё" mega-entry,
   not a bug. `unexplained token/article drops` (105) is a measured
   baseline, not yet a proven-zero hard gate (can't yet distinguish real
   drops from expected candidate-to-article reduction).
3. **Исправить carry и крупные spans** — **Partial**. p.550-551 resolved
   (see above). All 25 draft-level spans > 1000 chars triaged: 7 accepted
   and confirmed legitimate (common verbs with many senses), 5 correctly
   queued as medium/low confidence, 12 correctly demoted via parse_issues
   with a concrete reason. No individual span was hand-corrected — the
   existing gates already route each one correctly; a human still needs to
   process the 12 demoted ones via the review queue.
4. **Создать persistent decision ledger** — **Done**. New, committed
   `data/av-ru.1967.decisions.jsonl` (21 rows) + `decision_ledger.py`
   (hash-based conflict detection). Actually CONSUMED by `check_order.py`
   (not just written) — a stale decision (source facts changed) is a hard
   build failure, never silently reused (verified via a negative test).
5. **Сделать реальный baseline ratchet** — **Done**. `baseline.py`'s
   `check_metric()` now requires an exact match to the committed value;
   missing baseline = fail, improvement without updating the file = fail.
6. **Исправить false-headword detection без бесконечного blacklist** —
   **Partial**. Combined a Russian-lexicon hint (`data/ru-av.jsonl`, not a
   hardcoded list) with a content signal (`_is_bare_or_fragment` — bare
   stubs/truncated fragments only) to avoid flagging legitimate
   directly-borrowed Avar loanwords (амбар, авантюра). Cut false positives
   132 → 27 (manually verified 0 remaining false positives). A genuine
   layout-based signal ("is this word the first word on its printed
   line", via the new `geometry_lookup.py`) was tested at scale and
   **rejected**: 19% of all accepted entries aren't line-initial for
   entirely legitimate reasons (multiple short headwords sharing one
   line), far more than the ~27 real false headwords — confirmed the
   real fix needs the segment `index` threaded through
   `parse_articles.py` (not done this round). Still not the full
   layout/font/indent structural classifier the review asks for.

## Batch-3 P1 — status

7. **Сохранить полную provenance duplicate groups** — **Partial**.
   `data/av-ru.1967.provenance.jsonl` records `selection_rule`,
   `duplicate_group_spans_differ`, a real `bbox` (via `geometry_lookup.py`,
   9854/9858 populated) for both the winner and every duplicate-group
   member, plus each member's page/column/top/confidence/reasons/
   `raw_text_preview`. Missing: full raw text (only a 100-char preview)
   for non-winning members.
8. **Построить HTML review queue** — **Partial**. New
   `build_review_html.py` (not wired into `build_all.sh`, ~20min cold
   render of 570 page images, cached after). Generates a priority-ordered
   (boundary-high-demoted → carry → oversized-span → touches-regression →
   medium → low) local site with a per-item CROP of the item's own
   printed line (via `geometry_lookup.py`'s bbox, cheaply cropped with PIL
   from the cached full page — 3623/3632 crops generated) plus the full
   page image, raw OCR, proposed entry, reasons, decision-ledger status,
   and a progress counter. None of the 3632 items have actually been
   triaged through it yet — that's a separate, much larger manual-review
   effort.
9. **Разделить links для accepted и полного draft** — **Done**.
   `check_accepted.py` categorizes `see_also` targets by BOTH origin
   (accepted/review) and destination (accepted/review/missing/
   ocr-invalid) — 8 measured/gated buckets total.
10. **Сделать классификацию regressions доказуемой** — **Done**. Every
    `check_order.py` regression now has `suggested_category` (heuristic)
    separate from `confirmed_category` (only from a hash-valid ledger
    decision) — 13/900 currently confirmed.

## Batch-4 (av-ru-1967-review-batch-4-2026-09-17.md) — status

Machine-readable manifest (verified by `check_ci_policy.py`'s
`check_report_freshness()` on every CI run — `evaluated_commit` must be
HEAD or HEAD's immediate parent, and every hash below is recomputed from
the files on disk and required to match exactly; a report whose manifest
doesn't match the files it claims to describe fails CI, however
plausible its commit reference looks):

```json
{
  "evaluated_commit": "647f511c48c3c76d789ee7669b47ff930e2aa414",
  "artifact_hashes": {
    "data/av-ru.1967.jsonl": "d0ecbc6bbb3fac1f4c55c411aae7c5144c97d5da6fcc5077239e3ebed61a4813",
    "data/av-ru.1967.provenance.jsonl": "cb96a123353eb9c54ca4ab8fd55f840d72555a0b1308708e8fc8a736698fba09",
    "data/av-ru.1967.page_ledger.jsonl": "fc6aa9ca9dbcf84a3bac4e0a9d51448de3cb24002b19f98c328f19b4a604cfd2",
    "data/av-ru.1967.bracket_anomalies.jsonl": "1db3db6eb590d1ea5af0d9576c425d6b4558237bacc987dee3f659bfc164fd65",
    "data/av-ru.1967.missing_links_classification.jsonl": "204b069b81d94b4e030e5862ea847e59c5a598bffb704b7ef551b59af0d5251c"
  },
  "baselines_hash": "59e9eb8d4e48c93bd6bacaae5cec15ff84d6857cae1e9b59fe2f3d7d3e547f10"
}
```

1. **Per-candidate outcome ledger** — **Done**. `parse_articles.py`/
   `build_dataset.py` emit `candidate_outcomes.jsonl`/`draft_outcomes.jsonl`
   with exactly one outcome per candidate/draft article; 0 unaccounted.
2. **Decision ledger semantics** — **Done**. `needs_manual_fix` +
   `accepted_after_human_review` added; 6 misused `allowlisted` rows
   reclassified.
3. **Reproducible decision evidence** — **Done**. `pdf_sha256`, bbox,
   raw-text-snippet hashing.
4. **Fix the 6 named known accepted errors** — **Done**. New
   `data/av-ru.1967.corrections.jsonl` + `apply_corrections.py`.
5. **Close all 27 suspicious-headword findings** — **Done, fully** (all
   27 fixed with real corrections, including "во" — completed in
   batch-5, see below). `check_accepted.suspicious_headwords`: 27 → 0.
6. **Classify accounting gaps + 96 bracket anomalies** — **Done**. The 26
   accounting gap and 105 candidate drops were already closed by item 1;
   the 96 unclosed-bracket signals are now classified
   (`classify_bracket_anomalies.py`) — 95/96 were already safely
   quarantined in the review queue, the 1 accepted case (`шал` homonym 1)
   had real content loss, fixed.
7. **Multi-page provenance** — **Partial**. `source_pages` now
   structurally links p.551 to `цебё`'s own carry instead of a hardcoded
   exception; per-page bbox/token-range arrays for every source page not
   implemented.
8. **100% bbox coverage** — **Done**. 0/9836 accepted + 0/3632 review
   entries missing bbox (root cause: `geometry_lookup.find_line()` only
   matched a LINE's own aggregate top, missing bold words positioned
   mid-line with their own slightly different top).
9. **Real review-queue triage** — **Not started** this round beyond what
   items 5/6 covered incidentally.
10. **Accepted → missing links priority batch** — **Done**, and beyond
    the "first 100" minimum: found the dominant systematic class (a
    stress-mark notation difference, not OCR noise) and fixed it as a
    MATCHING normalization (not a content mutation) in both
    `check_accepted.py` and `resolve_references.py`.
    `check_accepted.links_missing`: 495 → 228.
    `check_accepted.review_links_missing`: 400 → 278.
    `resolve_references.unresolved`: 1204 → 464.
11. **Monotonic baseline CI policy** — **Done**, then reworked again for
    batch-5 (see below) after 3 real gaps were found in the first version.

See `/memories/repo/av-ru-1967-parsing.md` (Steps 52-60+) for the full
per-item investigation detail, bugs found/fixed, and validation record —
this section is a summary, not a replacement for that log.

## Batch-5 (av-ru-1967-review-batch-5-2026-09-18.md) — status

All 3 P0s: **Done**.

- **P0 "Исправить невоспроизводимый page ledger"**: root cause confirmed
  exactly as reported — `build_page_ledger.py` read
  `tmp/av-ru.1967/order_check.jsonl` (`check_order.py`'s own output) but
  ran BEFORE it in `build_all.sh`'s old step order. Fixed by reordering
  and wiping the whole `tmp/av-ru.1967/` at the start of every build
  (not just `geometry/`). New `check_reproducibility.sh` (2 clean runs +
  `git diff --exit-code`), also wired into CI.
- **P0 "Переделать monotonic baseline CI policy"**: all 3 named gaps
  fixed — a base ref lacking `baselines.json` (e.g. `main`) now falls
  back to the branch's own history instead of skipping; a metric's
  removal is only valid with a matching `baseline_migrations.json`
  entry (new file; documents the old `page_ledger.unexplained_drops`'s
  removal); the approval trailer is now per-metric and value-specific.
  New `test_check_ci_policy.py` (16 unit tests, stdlib `unittest`).
- **P0 "Сделать freshness отчёта проверяемой"**: ancestor-only checking
  never expires, so replaced with a machine-readable manifest (see
  above) requiring `evaluated_commit` be HEAD or HEAD's immediate
  parent EXACTLY, with every committed artifact's hash independently
  recomputed and matched.

P1s:

- **"Не называть automated corrections hand-verified"** — **Done**.
  `data/av-ru.1967.corrections.jsonl`'s `decision` renamed
  `"corrected"` → `"pending_human_signoff"` (honest: proposed and
  applied by an automated agent, not yet reviewed by a person; now 34
  rows). Every row now carries `risk_class` (`glyph-only-rename` /
  `punctuation-markup-repair` / `headword-removal-merge` /
  `sense-example-reconstruction`) and `before_entries` (the exact
  pre-correction entry/entries, reconstructed from a clean
  pre-corrections build) alongside the existing `expected_entry`, so a
  human reviewer has a real before/after diff to check, not just a
  page number. `human_signoff` is `null` until an actual person
  reviews a row (not yet done — 0/34 human-reviewed).
- **"Исправить семантику bracket decision"** — **Done**. The bulk
  `bracket-anomalies:batch-4-item-6` decision changed from `allowlisted`
  (wrongly implying "data confirmed correct") to the new
  `classified_pending_review` decision value (added to
  `decision_ledger.py`'s `DECISION_VALUES`, deliberately excluded from
  `RESOLVED_DECISIONS`). The classification artifact itself moved from a
  gitignored `tmp/` file to committed `data/av-ru.1967.bracket_anomalies.jsonl`
  (96 rows), each with a stable `item_id` and a `review_decision` field
  (`null` until individually reviewed) so future triage can reference a
  durable id, not just a count.
- **"Закрыть оставшиеся suspicious headwords до нуля"** — **Done**.
  `check_accepted.suspicious_headwords`: 2 → **0**. `сундук` fixed at
  the CHECKER level (`_is_bare_or_fragment()` no longer treats a
  legitimate see-only cross-reference as bare — verified only 1 accepted
  entry in the whole dataset had this exact shape, so the fix can't mask
  any other case). `во` actually fixed via a new correction:
  `вйхьизе`'s own garbled entry (missing sense 1, swapped av/ru example
  fields) reconstructed directly from raw_text, `во` removed.
- **"Начать настоящий review sprint"** — **Partial**. Individually
  reviewed all 96 bracket-anomaly review cards (1 of batch-5's 5 named
  priority groups) — every row now has a `review_decision` in
  `data/av-ru.1967.bracket_anomalies.jsonl`. This surfaced a real,
  previously-unnoticed bug class: 5 of the 96 (`новатор`/`профорг`/
  `скульптор`/`стажёр`/`инспектор`) are genuine missed-mid-paragraph-
  headword splits (a Russian-loanword genitive-declension bracket cut
  short at "1-го скл." with the actual genitive value mis-detected as
  its own bold headword), NOT cosmetic OCR noise like the rest — fixed
  via 5 new corrections, all 5 promoted into accepted. 80/96 confirmed
  as legitimate complete entries with only a single-glyph OCR defect
  (still correctly in review, not promoted this round). 6 flagged as
  genuinely too garbled for confident text-only reconstruction.
  **Bigger finding from this investigation, refined further**: 528
  review items across 80 pages are stuck at `confidence: "medium"`
  purely because of `reasons: ["label-lookahead"]` (the bold-detection-
  unreliable fallback heuristic) with ZERO other `parse_issues`. A
  37-item stratified sample (not just the earlier single-page spot-
  check) found this bucket is NOT uniformly safe: 1 bare false headword
  (`прямоугольник`) and 3 more confirmed missed-gloss-continuation
  splits (`ййгъи`/`распятие`, `мамлакат`/`страна`, `рёлъизари`/
  `осмеяние`) — resolving to 4 confirmed split pairs out of 37 sampled
  (~11%, the same order of magnitude as Step 48's rejected 19%-false-
  positive heuristic, validating the original caution against blanket
  promotion). **Not fixed this round**: all 4 pages involved (97, 243,
  332, 417) have zero accepted entries at all (confirmed via
  `page_ledger.jsonl`), so there is no nearby accepted anchor to insert
  these corrections after without creating new, badly-out-of-order
  `check_accepted.order_regressions` — fixing this properly requires
  solving the underlying dead-zone/anchor problem first (e.g. promoting
  a batch of the surrounding correct majority together, or an explicit
  approved regression trade-off), not a quick correction.
- **"228 accepted-origin link classification"** — **Done** (classified,
  not all individually fixed — matches the bracket-anomaly precedent).
  New `classify_missing_links.py`, committed as
  `data/av-ru.1967.missing_links_classification.jsonl` (228 rows, stable
  `item_id`, `review_decision` preserved across regeneration, wired into
  `build_all.sh` as non-gating, covered by `check_reproducibility.sh`).
  Buckets: 17 `valid-class-agreement-variant` (confirmed not a bug by
  construction — normal Avar noun-class prefix cross-reference); 74
  `ocr-target-fixable` (fuzzy match ≥88 against accepted/review vocab —
  a CANDIDATE only, not verified); 104
  `possible-ocr-target-needs-verification` (fuzzy match 75-88); 33
  `no-plausible-match-found`. None of the fuzzy candidates were
  auto-applied as corrections (similarity alone isn't proof of the
  correct target). Caught and fixed a real reproducibility bug while
  building this: `rapidfuzz.process.extractOne` breaks ties between
  equally-scored candidates by input order, and Python's set iteration
  order for strings depends on per-process hash randomization — fixed
  by sorting the candidate word list deterministically before matching.
- Remaining P1s (100+ order-regression triage, multi-page
  `source_spans` evidence) — not yet started this round; see
  `/memories/repo/av-ru-1967-parsing.md` for current progress on each.
- **"100+ order-regression triage"** — **Started**. Found that 420/426
  draft-level `unclassified` order regressions have a low/medium-
  confidence `next` word (already quarantined in the review queue, not
  published) — heterogeneous root causes on manual sampling (false
  headwords, OCR noise, genuine pronoun-paradigm layout scrambles), so
  NOT given a blanket suggested_category (would be cosmetic, not a real
  diagnosis). Focused instead on the more consequential accepted-level
  `check_accepted.order_regressions` (383 → **382**): found and fixed 1
  real bug via direct geometry inspection — `у` was a false headword
  (a Russian sentence-initial capital letter mis-detected as bold),
  actually the orphaned Russian half of an example sentence belonging to
  the accepted entry `аби` (homonym 2, sense "сказание, предание") whose
  Avar half was already correctly captured with an empty `ru`. Merged
  back in, `у` removed (`correction:у-orphaned-example-merged-into-аби`).
  Remaining ~380 order regressions still need the same one-by-one
  geometry-inspection triage — not a batch fix, genuinely slow going.

## History: batch-2/3 metrics snapshot (superseded, kept for record only)

**This section describes an OLD state (commit `7a3038b`) and is NOT the
current status** — it predates all of batch-4/5's fixes above. Kept only
so the historical arc of the project is visible; the manifest above (and
`scripts/av-ru-1967/baselines.json`/`/memories/repo/av-ru-1967-parsing.md`)
are the only current-state sources of truth. Do not read the numbers
below as describing the present.

- `data/av-ru.1967.jsonl`: 9858 entries, sha256
  `c44b4d54cd04d82bd8c8cf87a354d709832b85cd64a9ed99d8f0e991bc4eaa84`,
  byte-reproducible across repeated `build_all.sh` runs. 0 schema
  violations, 0 `quality_scan` findings.
- `data/av-ru.1967.provenance.jsonl`: 9858 rows (1:1 with accepted),
  9854/9858 with a real `bbox`.
- `data/av-ru.1967.page_ledger.jsonl`: 597 rows (23-619), 0 unexplained
  zero-candidate pages, 105 unexplained drops (baseline, not yet 0).
- `data/av-ru.1967.decisions.jsonl`: 21 rows (13 order-regression triages,
  1 carry-page, 7 oversized-span confirmations).
- `check_accepted.py`: 408 order regressions, 27 suspicious headwords, 7
  oversized spans, 495/399 accepted/review-origin missing links, 0
  ocr-invalid targets, 0 missing provenance.
- `check_order.py` (draft-level): 900 total regressions (131 high/high),
  391 stress-glyph-unresolved / 61 hyphen-reduplication / 9 false-headword
  / 426 unclassified (0 high/high — the 13 previously-unclassified
  high/high pairs are now ledger-confirmed).
- `resolve_references.py` (draft-level): 1204 unresolved.
- All baseline metrics are an exact-match ratchet (`baseline.py`) —
  missing or drifted (better or worse) fails the build.

## Not started / explicitly out of scope for this round

- Full raw text (only a preview) for non-winning duplicate-group members.
- The full layout/font-based structural false-headword classifier —
  investigated (line-initial-word signal), empirically rejected (19%
  false-positive rate), real fix needs segment `index` threading through
  `parse_articles.py` (identified, not implemented).
- Actually triaging the 3632-item review queue, the 12 demoted long spans,
  or the ~900/408 order regressions down to zero — all currently measured
  and gated against regressions, not yet driven to the review's ultimate
  "0 необъяснённых" criteria.
- Explicitly deferred by both reviews: `gender_forms` population, full
  stress restoration, `sources.json` registration, license decision, site
  publication integration.
