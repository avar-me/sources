#!/usr/bin/env python3
"""Shared geometry lookup helpers for the av-ru.1967 pipeline.

Cross-references an article's (page, column, top) — already tracked
everywhere in provenance/needs_review — against the per-page geometry
dumps written by extract_geometry.py (tmp/av-ru.1967/geometry/), to get an
actual bounding box for that headword's printed line. Used to add `bbox`
to data/av-ru.1967.provenance.jsonl (batch-3 P1 "Сохранить полную
provenance duplicate groups") and to crop a per-item scan image for the
HTML review queue (batch-3 P1 "Построить HTML review queue") instead of
embedding the whole page.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

Bbox = tuple[float, float, float, float]  # (x0, top, x1, bottom), PDF points


def load_geometry(page: int, geometry_dir: Path) -> dict[str, Any] | None:
    path = geometry_dir / f"page-{page:04d}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def find_line(geometry: dict[str, Any] | None, column: str | None, top: float | None, tolerance: float = 0.5) -> dict[str, Any] | None:
    if not geometry or not column or top is None:
        return None
    for line in geometry.get(column, []):
        if abs(line["top"] - top) < tolerance:
            return line
    # Fallback: a bold headword mid-line (not the line's own first word) has
    # its own per-word `top` that can differ from the line's aggregate
    # `top` (the first word's) by a point or two — segment_entries.py's
    # candidates record the WORD's own top, not the line's. Search each
    # line's individual words before giving up (batch-4 item 8: this was
    # the root cause for аспирантура/ассистентка/варислъи/махшел having no
    # bbox at all despite a perfectly valid page/column/top).
    for line in geometry.get(column, []):
        for word in line.get("words") or []:
            if abs(word["top"] - top) < tolerance:
                return line
    return None


def line_bbox(line: dict[str, Any] | None) -> Bbox | None:
    if not line:
        return None
    words = line.get("words") or []
    if not words:
        return None
    x0 = min(w["x0"] for w in words)
    x1 = max(w["x1"] for w in words)
    return (x0, line["top"], x1, line["bottom"])


def bbox_for(geometry_dir: Path, page: int | None, column: str | None, top: float | None) -> Bbox | None:
    """Convenience one-shot lookup: geometry file -> matching line -> bbox."""
    if page is None:
        return None
    geometry = load_geometry(page, geometry_dir)
    line = find_line(geometry, column, top)
    return line_bbox(line)
