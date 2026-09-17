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
fails the build). `check_order.py` and `resolve_references.py` are
**baseline gates** (`scripts/av-ru-1967/baselines.json`, via the shared
`baseline.py` helper): the build fails if their metrics regress past the
last committed baseline, but the baseline itself is allowed to be > 0 while
the remaining article-boundary/reference bugs are worked through (see the
review doc's "Этап 1"/"P0" sections). When a fix genuinely lowers one of
these counts, lower the corresponding value in `baselines.json` in the same
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
   ```bash
   python3 scripts/av-ru-1967/build_dataset.py --out data/av-ru.1967.jsonl
   ```

5. **`validate_schema.py`** — hard gate: schema validity, duplicate lines,
   soft hyphens, empty av/ru examples, see_also self-loops.
   ```bash
   python3 scripts/av-ru-1967/validate_schema.py --input data/av-ru.1967.jsonl
   ```

## Diagnostic scripts and gates

- **`check_order.py`** (baseline gate) — flags any two consecutive articles
  whose Avar sort keys go backwards (the whole book is one continuous A-Z
  listing across pages 23-619). Rescues stress-glyph/`||` OCR artifacts the
  same way `build_dataset.py` does before comparing, so remaining
  regressions are real segmentation bugs, not stress-mark noise. Each
  regression is classified (`classify()`) into `stress-glyph-unresolved`,
  `hyphen-reduplication`, `false-headword`, or `unclassified`, and checks
  four metrics against `baselines.json`: `order_check.total_regressions`,
  `order_check.high_high`, `order_check.unclassified`,
  `order_check.unclassified_high_high`.
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

### `baselines.json` / `baseline.py`

Shared helper (`scripts/av-ru-1967/baseline.py`) used by `check_order.py`
and `resolve_references.py`. `baselines.json` records the current
acceptable ceiling for each metric; `check_metric()` prints `[baseline] ok`
or `FAIL` and the script's `main()` turns any `FAIL` into a non-zero exit.
When fixing article-boundary/reference bugs, update the relevant number in
`baselines.json` downward in the same commit as the fix so the gate can't
regress back up unnoticed.
