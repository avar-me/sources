#!/usr/bin/env bash
# Single documented entry point for the av-ru.1967 pipeline (Этап 1 of
# av-ru-1967-review-2026-09-17.md: reproducibility before anything else).
#
# Regenerates data/av-ru.1967.jsonl from books/saidov_m_avarskorusskii_slovar.pdf
# and runs every diagnostic script, failing fast (set -e) on the first
# hard error. Diagnostic scripts that only *report* findings (check_order.py,
# resolve_references.py, quality_scan.py) do not fail the build by
# themselves yet — their counts are printed so a human decides whether the
# current numbers are an acceptable baseline. validate_schema.py DOES fail
# the build (schema violations, duplicate lines, soft hyphens, empty
# examples, self-loops are never acceptable).
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

echo "=== check_order (report only) ==="
python3 "$SCRIPTS_DIR/check_order.py"

echo "=== resolve_references (report only) ==="
python3 "$SCRIPTS_DIR/resolve_references.py"

echo "=== quality_scan (report only) ==="
python3 "$SCRIPTS_DIR/quality_scan.py"

echo "=== build complete: $OUT ==="
wc -l "$OUT"
sha256sum "$OUT" 2>/dev/null || shasum -a 256 "$OUT"
