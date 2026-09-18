#!/usr/bin/env bash
# Clean, two-run reproducibility test (av-ru-1967-review-batch-5-2026-09-18.md,
# P0 "Исправить невоспроизводимый page ledger", requirement 3).
#
# Runs the full documented pipeline (build_all.sh) TWICE, from a
# completely clean tmp/av-ru.1967/ state each time (build_all.sh itself
# now wipes it at the start), and fails if:
# - either run exits non-zero;
# - the two runs produce different hashes for any committed generated
#   artifact;
# - the resulting artifacts differ from what's currently committed in git
#   (working tree not clean after the build — a silent, uncommitted drift).
#
# Usage (from repo root, inside the .venv-av-ru-1967 virtualenv):
#   scripts/av-ru-1967/check_reproducibility.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

ARTIFACTS=(
  "data/av-ru.1967.jsonl"
  "data/av-ru.1967.provenance.jsonl"
  "data/av-ru.1967.page_ledger.jsonl"
  "data/av-ru.1967.bracket_anomalies.jsonl"
  "data/av-ru.1967.missing_links_classification.jsonl"
)

hash_artifacts() {
  for f in "${ARTIFACTS[@]}"; do
    sha256sum "$f" 2>/dev/null || shasum -a 256 "$f"
  done
}

echo "=== reproducibility run 1/2 ==="
bash scripts/av-ru-1967/build_all.sh > /tmp/av-ru-1967-repro-run1.log 2>&1 || {
  echo "FAIL: run 1 exited non-zero, see /tmp/av-ru-1967-repro-run1.log"
  tail -40 /tmp/av-ru-1967-repro-run1.log
  exit 1
}
hash_artifacts > /tmp/av-ru-1967-repro-hashes1.txt

echo "=== git diff --exit-code (run 1 vs committed) ==="
if ! git diff --exit-code -- "${ARTIFACTS[@]}"; then
  echo "FAIL: run 1's committed generated artifacts differ from git HEAD — the build is not reproducing the committed state"
  exit 1
fi

echo "=== reproducibility run 2/2 (from clean tmp again) ==="
bash scripts/av-ru-1967/build_all.sh > /tmp/av-ru-1967-repro-run2.log 2>&1 || {
  echo "FAIL: run 2 exited non-zero, see /tmp/av-ru-1967-repro-run2.log"
  tail -40 /tmp/av-ru-1967-repro-run2.log
  exit 1
}
hash_artifacts > /tmp/av-ru-1967-repro-hashes2.txt

echo "=== comparing hashes across both runs ==="
if ! diff -u /tmp/av-ru-1967-repro-hashes1.txt /tmp/av-ru-1967-repro-hashes2.txt; then
  echo "FAIL: hashes differ between the two clean runs — the pipeline is NOT reproducible"
  exit 1
fi

echo "=== git diff --exit-code (run 2 vs committed) ==="
if ! git diff --exit-code -- "${ARTIFACTS[@]}"; then
  echo "FAIL: run 2's committed generated artifacts differ from git HEAD"
  exit 1
fi

echo "OK: two clean runs produced byte-identical artifacts, matching the committed state"
cat /tmp/av-ru-1967-repro-hashes2.txt
