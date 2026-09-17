"""Shared baseline-gate helper for the av-ru.1967 diagnostic scripts.

av-ru-1967-review-batch-2-2026-09-17.md, "P1. Исправить декларацию полного
pipeline": build_all.sh ran check_order.py/resolve_references.py/
quality_scan.py as report-only, so the build succeeded even at 900 order
regressions, 1204 unresolved links and (before Step 33) 9 quality_scan
findings — nothing actually enforced "don't get worse". This module lets
each diagnostic script compare its own metrics against a committed
baseline file and fail the build (non-zero exit) on regression, while
still allowing an *improvement* to lower the baseline over time.

These are explicitly temporary, non-zero baselines (per the review: "После
закрытия текущего батча заменить временные baselines на нулевые требования
для accepted-набора") — quality_scan.py's own hard requirement is already 0
findings (Step 33), tracked directly rather than via a baseline entry.
"""

from __future__ import annotations

import json
from pathlib import Path

BASELINE_PATH = Path(__file__).parent / "baselines.json"


def load_baselines() -> dict[str, int]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def check_metric(name: str, value: int, baselines: dict[str, int]) -> bool:
    """Returns True (gate passes) if value <= the committed baseline for
    `name`. Prints a status line either way. Missing baseline entries pass
    with a warning rather than failing outright, so a newly-added metric
    doesn't immediately break the build before a baseline is committed for
    it."""
    limit = baselines.get(name)
    if limit is None:
        print(f"[baseline] {name} = {value} (no baseline recorded — add one to baselines.json)")
        return True
    if value > limit:
        print(f"[baseline] FAIL: {name} = {value} > baseline {limit}")
        return False
    marker = " (improved — consider lowering the baseline)" if value < limit else ""
    print(f"[baseline] ok: {name} = {value} (baseline {limit}){marker}")
    return True
