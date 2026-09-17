# av-ru.1967 parsing scripts

Tools for turning `books/saidov_m_avarskorusskii_slovar.pdf` into
`data/av-ru.1967.jsonl`. See `../../av-ru-1967-parsing-handoff.md` for the
full plan and `../../av-ru-1967-review-2026-09-17.md` for an external
review of the current state — read that review before touching
segmentation/parsing logic, it documents known gaps and a recommended fix
order. This directory only holds the code; `tmp/av-ru.1967/` (gitignored)
holds all intermediate artifacts.

## Environment

```bash
python3 -m venv .venv-av-ru-1967   # from repo root; gitignored
source .venv-av-ru-1967/bin/activate
pip install -r scripts/av-ru-1967/requirements.txt
```

Pinned versions (see `requirements.txt`): Python 3.14.3, pdfplumber 0.11.10,
rapidfuzz 3.14.6, jsonschema 4.26.0.

## Full pipeline (single command)

```bash
scripts/av-ru-1967/build_all.sh
```

Regenerates `data/av-ru.1967.jsonl` from the PDF end-to-end and runs every
diagnostic script, failing fast (`set -e`) on the first non-zero exit.
`validate_schema.py` and `quality_scan.py` are unconditional hard gates (0
tolerance: any schema violation, duplicate line, stray soft hyphen, empty
`av`/`ru` example, `see_also` self-loop, or av/ru-contamination finding
fails the build). `check_accepted.py`, `check_order.py` and
`resolve_references.py` are **baseline gates**
(`scripts/av-ru-1967/baselines.json`, via the shared `baseline.py` helper):
the build fails if their metrics regress past the last committed baseline,
but the baseline itself is allowed to be > 0 while the remaining
article-boundary/reference bugs are worked through (see the review docs'
"P0" sections). `check_accepted.py` checks ONLY the published file (its own
order/headword-language/span-size/provenance/link-target shape);
`check_order.py` and `resolve_references.py` check the full draft (every
candidate the segmenter found, published or not) — av-ru-1967-review-batch-
3-2026-09-17.md's "P0. Реализовать независимые gates для
accepted/review/draft" asked for exactly this draft-vs-accepted split,
since a clean draft-level number doesn't prove the *published* file's own
order/headwords are sound (batch-3 measured 900 draft-level order
regressions vs 408 accepted-only). When a fix genuinely lowers one of these
counts, lower the corresponding value in `baselines.json` in the same
commit so the gate keeps ratcheting toward zero instead of silently
tolerating the old, worse number forever. `compare_with_av_ru.py` is a
genuinely optional spot-check and never fails the build.

Verified byte-for-byte reproducible: running the script twice in a row
produces an identical `sha256sum` for `data/av-ru.1967.jsonl` both times.
Run it and read its own output for the current counts rather than trusting
numbers written in this file — this file is not regenerated automatically
and will drift.

## Pipeline stages (run individually if iterating on one stage)

1. **`extract_geometry.py`** — per-page word geometry (column, bbox, font,
   size, bold/italic) via pdfplumber, no article segmentation yet.
   ```bash
   python3 scripts/av-ru-1967/extract_geometry.py --start 23 --end 619
   ```
   Writes one JSON file per physical PDF page to `tmp/av-ru.1967/geometry/`.
   Physical page numbers match `pdf.pages[n-1]` — verified against the
   handoff doc's page-range table (e.g. page 620 starts the geographic
   names list, page 705 starts the grammar essay).

2. **`segment_entries.py`** — finds headword-candidate positions in the
   per-page word stream and assigns a confidence level (`high`/`medium`/
   `low`) and `reasons` for each.
   ```bash
   python3 scripts/av-ru-1967/segment_entries.py --start 23 --end 619
   ```
   Writes `tmp/av-ru.1967/segments.jsonl`.

3. **`parse_articles.py`** — converts headword spans into draft article
   dicts with senses/examples/labels; stitches an article across a page
   boundary when the previous page's last span didn't end on a real
   terminator.
   ```bash
   python3 scripts/av-ru-1967/parse_articles.py --start 23 --end 619
   ```
   Writes `tmp/av-ru.1967/draft_articles.jsonl`.

4. **`build_dataset.py`** — converts the draft articles into schema-shaped
   entries, applying the known-word-gated OCR rescues (stress-glyph
   б/6/й/ё, `||`-as-ц/Ц). An article is only published to
   `data/av-ru.1967.jsonl` if BOTH hold: segmentation `confidence: high`
   (the boundary itself is trusted) AND `detect_parse_issues()` finds
   nothing wrong with the parsed content (no leftover raw structural
   marker — `*`, `[`, `]`, `^`, `_`, `{`, `}`, `\` — and none of
   quality_scan.py's own av/ru-leak or russian-word-as-headword checks
   fire). Anything else goes to `tmp/av-ru.1967/needs_review.jsonl`
   (gitignored review queue) tagged with `confidence` and `parse_issues`.
   Also writes `data/av-ru.1967.provenance.jsonl` — one committed row per
   accepted entry, 1:1 with `data/av-ru.1967.jsonl` in the same order
   (page/column/top/confidence/reasons/raw_text_length, `selection_rule`
   — `"unique"` or `"highest-confidence-first-seen"` — plus
   `duplicate_group_spans_differ` and every OTHER duplicate-group
   candidate that was merged into it: page/column/top/confidence/reasons/
   `raw_text_preview`) — av-ru-1967-review-batch-3-2026-09-17.md, "P0
   (accepted entries without source provenance: 0)" and "P1 (duplicate-
   group provenance)".
   ```bash
   python3 scripts/av-ru-1967/build_dataset.py --out data/av-ru.1967.jsonl
   ```

5. **`validate_schema.py`** — hard gate: schema validity, duplicate lines,
   soft hyphens, empty av/ru examples, see_also self-loops.
   ```bash
   python3 scripts/av-ru-1967/validate_schema.py --input data/av-ru.1967.jsonl
   ```

## Diagnostic scripts and gates

- **`check_accepted.py`** (baseline gate, accepted-only) — the only script
  that checks the PUBLISHED file's own file order/content, independent of
  the heuristics that built it. Checks: alphabetical order regressions in
  `data/av-ru.1967.jsonl`'s own order (no stress-glyph rescue — accepted is
  supposed to be final already); suspicious-language headwords (a
  Russian-lexicon match against `data/ru-av.jsonl` is only a HINT — it
  fires as a finding only combined with `_is_bare_or_fragment()`, i.e. the
  entry ALSO has no substantive gloss content, since a genuine
  directly-borrowed Avar loanword like "амбар"/"авантюра" always has a
  real gloss/example and shouldn't be flagged just for looking Russian;
  still not the full layout/font-based structural classifier batch-3
  ultimately wants); oversized spans (`raw_text_length` from the provenance file);
  `see_also` link targets split into accepted/review/missing; provenance
  completeness (hard 0 — every accepted entry must have a provenance row by
  construction). Link targets are categorized by BOTH origin (accepted vs
  review entries) and destination (accepted/review/missing/ocr-invalid — a
  target string that's pure OCR noise, e.g. a leftover raw marker
  character or no letters at all, is distinguished from a "missing" but
  plausible word). Metrics tracked in `baselines.json`:
  `check_accepted.order_regressions`, `check_accepted.suspicious_headwords`,
  `check_accepted.oversized_spans`, `check_accepted.links_missing`,
  `check_accepted.review_links_missing`,
  `check_accepted.accepted_links_ocr_invalid`,
  `check_accepted.review_links_ocr_invalid`.
- **`build_page_ledger.py`** — per-page coverage ledger across all 597
  physical pages (23-619), cross-referencing geometry/segments/draft
  articles/accepted/review counts, first/last headword, carry-in/out,
  max span length, unclosed brackets, and order regressions touching that
  page. Writes the committed `data/av-ru.1967.page_ledger.jsonl` (597 rows).
  Hard gate: every page must be present, and every zero-draft-article page
  must have an explanation in `EXPLAINED_ZERO_CANDIDATE_PAGES` (currently
  just page 551 — confirmed via rendered page scans to be entirely a
  continuation of the p.550 "цебё" postposition mega-entry, not a bug).
  `unexplained token/article drops` (segment candidates that never became
  a draft article) is tracked as a baseline
  (`page_ledger.unexplained_drops`), not yet a hard 0, because the current
  count-difference can't distinguish a real drop from expected
  candidate-to-article reduction (homonym/bracket consumption, stitching).
- **`check_order.py`** (baseline gate, draft-only) — flags any two consecutive articles
  whose Avar sort keys go backwards (the whole book is one continuous A-Z
  listing across pages 23-619). Rescues stress-glyph/`||` OCR artifacts the
  same way `build_dataset.py` does before comparing, so remaining
  regressions are real segmentation bugs, not stress-mark noise. Each
  regression gets a `suggested_category` (an unproven heuristic guess —
  `stress-glyph-unresolved`, `hyphen-reduplication`, `false-headword`, or
  `unclassified`) and, if a matching row exists in the committed
  `data/av-ru.1967.decisions.jsonl` ledger, a `confirmed_category` (a human
  decision with recorded evidence). If a ledger row's `source_hash` no
  longer matches the current pair (the underlying facts changed since it
  was reviewed), that's a **hard-gate conflict** (build fails) — a stale
  decision is never silently reused. Checks four metrics against
  `baselines.json`: `order_check.total_regressions`, `order_check.high_high`,
  `order_check.unclassified`, `order_check.unclassified_high_high`.
- **`resolve_references.py`** (baseline gate) — tries to resolve every
  `see_also`/`from` target against `word`/`forms`/`spelling_forms` of other
  entries; checks `resolve_references.unresolved` against `baselines.json`.
- **`quality_scan.py`** (hard gate, 0 tolerance) — independent structural
  checks (Russian text leaking into `av`, Avar text leaking into `ru`,
  outlier-length `word`), gated on `known_words` to avoid flagging real
  Avar/Russian homographs. Fails the build if any finding remains — this
  is enforced by construction in `build_dataset.py`'s `detect_parse_issues()`
  gate (stage 4), so this script's job is to confirm that guarantee holds.
- **`compare_with_av_ru.py`** (optional, never gates the build) —
  fuzzy-matches headwords against the modern `data/av-ru.jsonl` for
  spot-checking (uses `rapidfuzz`).
- **`build_review_html.py`** (optional, NOT part of `build_all.sh`) —
  generates a local static HTML review site from
  `tmp/av-ru.1967/needs_review.jsonl` (av-ru-1967-review-batch-3-2026-09-17.md,
  "P1. Построить HTML review queue"): one page per review item (rendered
  page image, raw OCR, proposed entry JSON, reasons/parse_issues,
  neighbor headwords, stable id/source hash, current decision-ledger
  status if any) plus a priority-ordered index (boundary-high-demoted >
  page-boundary-carry > oversized-span > touches-order-regression >
  medium-confidence > low-confidence) and a reviewed/remaining progress
  count. NOT wired into `build_all.sh` because rendering ~570 distinct
  page images from the PDF takes ~20+ minutes on a cold cache (page
  images are cached by filename under `tmp/av-ru.1967/review_html/pages/`,
  so repeat runs are fast — use `--force-images` to bust the cache,
  `--skip-images` to iterate on HTML/layout without waiting on renders).
  ```bash
  python3 scripts/av-ru-1967/build_review_html.py
  ```

### `data/av-ru.1967.decisions.jsonl` / `decision_ledger.py`

Committed, persistent review-decision ledger (av-ru-1967-review-batch-3-
2026-09-17.md, "P0. Создать persistent decision ledger") — replaces
scattering triage results across `/memories`, `tmp/`, or chat history. Each
row: `id` (stable string), `source_hash` (short hash of the exact facts the
decision was based on), `decision` (`accepted`/`rejected`/`corrected`/
`allowlisted`), `category`, `reason`, `reviewer`, `reviewed_at`, `evidence`,
`expected_entry`. `scripts/av-ru-1967/decision_ledger.py` provides
`load_decisions()`/`check_decision()`/hashing helpers; currently consumed
by `check_order.py` (order-regression pairs) — if the underlying facts
change since a decision was recorded (the hash no longer matches), that's a
`conflict`, hard-gated (never silently reused). Seeded with the 13
previously `/memories`-only triaged high/high order regressions, the p.551
carry-page decision, and the 7 confirmed-legitimate oversized accepted
spans.

### `baselines.json` / `baseline.py`

Shared helper (`scripts/av-ru-1967/baseline.py`) used by `check_accepted.py`,
`check_order.py`, `resolve_references.py` and `build_page_ledger.py`.
`baselines.json` records the exact EXPECTED value for each metric —
`check_metric()` requires the current value to match it precisely (a true
monotonic ratchet, per av-ru-1967-review-batch-3-2026-09-17.md's "P0.
Сделать реальный baseline ratchet"): a missing baseline entry is a
failure, a regression is a failure, and an *improvement* is ALSO a
failure until `baselines.json` is updated to the new, lower number in the
same commit. This forced sync is what makes it a ratchet — the ceiling
can only ever move because someone consciously edited the file.
