"""Shared baseline-gate helper for the av-ru.1967 diagnostic scripts.

av-ru-1967-review-batch-2-2026-09-17.md, "P1. Исправить декларацию полного
pipeline": build_all.sh ran check_order.py/resolve_references.py/
quality_scan.py as report-only, so the build succeeded even at 900 order
regressions, 1204 unresolved links and (before Step 33) 9 quality_scan
findings — nothing actually enforced "don't get worse". This module lets
each diagnostic script compare its own metrics against a committed
baseline file and fail the build (non-zero exit) on regression.

av-ru-1967-review-batch-3-2026-09-17.md, "P0. Сделать реальный baseline
ratchet": the original `value <= baseline` version was NOT a real ratchet
— a metric that improved (e.g. 900 -> 700) but whose baselines.json entry
wasn't updated could quietly regress back up to the old, worse baseline
(899) and still pass. A missing baseline entry also passed silently
instead of failing. Both are fixed now: `check_metric` requires the value
to match the committed baseline EXACTLY (batch-3's option 1). Any drift,
better or worse, fails the build until `baselines.json` is updated in the
same commit — that forced sync IS the ratchet.

These are explicitly temporary, non-zero expected values (per the review: "После
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
    """Returns True (gate passes) only if `value` matches the committed
    expected value for `name` EXACTLY. A missing baseline entry is a
    failure (not a silent pass). A value that improved on the committed
    number is ALSO a failure, forcing whoever landed the improvement to
    lower `baselines.json` in the same commit."""
    if name not in baselines:
        print(f"[baseline] FAIL: {name} = {value} has no recorded baseline (missing baseline = failure, add one to baselines.json)")
        return False
    expected = baselines[name]
    if value == expected:
        print(f"[baseline] ok: {name} = {value} (matches expected {expected})")
        return True
    if value < expected:
        print(f"[baseline] FAIL: {name} = {value} improved on expected {expected} — update baselines.json to {value} in this commit")
        return False
    print(f"[baseline] FAIL: {name} = {value} regressed from expected {expected}")
    return False
