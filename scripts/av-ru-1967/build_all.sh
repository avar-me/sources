#!/usr/bin/env bash
# Single documented entry point for the av-ru.1967 pipeline (Этап 1 of
# av-ru-1967-review-2026-09-17.md: reproducibility before anything else).
#
# Regenerates data/av-ru.1967.jsonl from books/saidov_m_avarskorusskii_slovar.pdf
# and runs every diagnostic script, failing fast (set -e) on the first
# hard error. Per av-ru-1967-review-batch-3-2026-09-17.md's "P0. Реализовать
# независимые gates для accepted/review/draft": check_accepted.py checks
# ONLY the published file (data/av-ru.1967.jsonl, in its own file order —
# order/false-headword/span-size/provenance/link gates); check_order.py and
# resolve_references.py check the FULL draft (every candidate the
# segmenter found, published or not) for source-recognition quality.
# validate_schema.py and quality_scan.py are unconditional hard gates (0
# tolerance); check_accepted.py, check_order.py and resolve_references.py
# are BASELINE gates (scripts/av-ru-1967/baselines.json) — they fail the
# build if their metrics get WORSE than the last committed baseline, but
# don't yet require perfection (see baseline.py's docstring).
# compare_with_av_ru.py is a separate, genuinely optional spot-check
# (fuzzy-match diagnostic) that does not gate the build.
#
# Usage (from repo root, inside the .venv-av-ru-1967 virtualenv):
#   scripts/av-ru-1967/build_all.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SCRIPTS_DIR="scripts/av-ru-1967"
OUT="data/av-ru.1967.jsonl"

echo "=== compile check ==="
python3 -m compileall -q "$SCRIPTS_DIR"

echo "=== step 1: extract_geometry ==="
rm -rf tmp/av-ru.1967/geometry
python3 "$SCRIPTS_DIR/extract_geometry.py" --start 23 --end 619

echo "=== step 3: segment_entries ==="
python3 "$SCRIPTS_DIR/segment_entries.py" --start 23 --end 619

echo "=== step 4: parse_articles ==="
python3 "$SCRIPTS_DIR/parse_articles.py" --start 23 --end 619

echo "=== step 6: build_dataset ==="
python3 "$SCRIPTS_DIR/build_dataset.py" --out "$OUT"

echo "=== validate_schema (hard gate) ==="
python3 "$SCRIPTS_DIR/validate_schema.py" --input "$OUT"

echo "=== check_accepted (baseline gate, accepted-only) ==="
python3 "$SCRIPTS_DIR/check_accepted.py"

echo "=== build_page_ledger (hard gate: completeness/zero-candidates; baseline: drops) ==="
python3 "$SCRIPTS_DIR/build_page_ledger.py"

echo "=== check_order (baseline gate, draft-only) ==="
python3 "$SCRIPTS_DIR/check_order.py"

echo "=== resolve_references (baseline gate, draft-only) ==="
python3 "$SCRIPTS_DIR/resolve_references.py"

echo "=== quality_scan (hard gate) ==="
python3 "$SCRIPTS_DIR/quality_scan.py"

echo "=== compare_with_av_ru (optional, does not gate the build) ==="
python3 "$SCRIPTS_DIR/compare_with_av_ru.py" || echo "compare_with_av_ru.py failed/unavailable — not a build failure"

echo "=== build complete: $OUT ==="
wc -l "$OUT"
sha256sum "$OUT" 2>/dev/null || shasum -a 256 "$OUT"
