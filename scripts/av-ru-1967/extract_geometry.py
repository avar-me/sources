#!/usr/bin/env python3
"""Geometric word/line extraction for the 1967 Saidov dictionary PDF.

Step 1 of av-ru-1967-parsing-handoff.md: dump per-page word geometry
(column, bbox, font, bold/italic) without attempting article segmentation.
Requires pdfplumber (see scripts/av-ru-1967/README.md for env setup).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pdfplumber

DEFAULT_PDF = "books/saidov_m_avarskorusskii_slovar.pdf"
HEADER_TOP_LIMIT = 20.0  # points from page top; running head + page number live here
LINE_CLUSTER_TOLERANCE = 2.5  # points; words within this "top" delta join one line
DEFAULT_COLUMN_SPLIT = 136.0  # fallback gap between columns, in points

# Running head looks like "abu — 24 — ava" (left-page-word, page number, right-page-word).
HEADER_PATTERN = re.compile(r"^\S+\s+—\s+\d+\s+—\s+\S+$")


def is_bold(fontname: str) -> bool:
    return "bold" in fontname.lower()


def is_italic(fontname: str) -> bool:
    lowered = fontname.lower()
    return "italic" in lowered or "oblique" in lowered


def find_column_split(xs: list[float]) -> float:
    """Find the widest gap between word x0 values in the plausible middle band."""
    xs = sorted(xs)
    best_gap = 0.0
    best_mid = DEFAULT_COLUMN_SPLIT
    for a, b in zip(xs, xs[1:]):
        if 60.0 < a < 200.0 and (b - a) > best_gap:
            best_gap = b - a
            best_mid = (a + b) / 2
    return best_mid if best_gap > 4.0 else DEFAULT_COLUMN_SPLIT


def cluster_lines(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group words into visual lines by proximity of `top`, then sort by x0."""
    ordered = sorted(words, key=lambda w: (w["top"], w["x0"]))
    lines: list[list[dict[str, Any]]] = []
    for word in ordered:
        if lines and abs(word["top"] - lines[-1][0]["top"]) <= LINE_CLUSTER_TOLERANCE:
            lines[-1].append(word)
        else:
            lines.append([word])
    result = []
    for line in lines:
        line.sort(key=lambda w: w["x0"])
        result.append(
            {
                "top": round(min(w["top"] for w in line), 2),
                "bottom": round(max(w["bottom"] for w in line), 2),
                "text": " ".join(w["text"] for w in line),
                "words": line,
            }
        )
    return result


def extract_page(page, page_number: int) -> dict[str, Any]:
    raw_words = page.extract_words(
        use_text_flow=False,
        keep_blank_chars=False,
        extra_attrs=["fontname", "size"],
    )
    words = []
    for w in raw_words:
        words.append(
            {
                "text": w["text"],
                "x0": round(w["x0"], 2),
                "x1": round(w["x1"], 2),
                "top": round(w["top"], 2),
                "bottom": round(w["bottom"], 2),
                "fontname": w.get("fontname", ""),
                "size": round(w.get("size", 0.0), 2),
                "bold": is_bold(w.get("fontname", "")),
                "italic": is_italic(w.get("fontname", "")),
            }
        )

    header_words = [w for w in words if w["top"] < HEADER_TOP_LIMIT]
    body_words = [w for w in words if w["top"] >= HEADER_TOP_LIMIT]
    header_text = " ".join(w["text"] for w in sorted(header_words, key=lambda w: w["x0"]))
    header_recognized = bool(HEADER_PATTERN.match(header_text)) if header_text else False

    split_x = find_column_split([w["x0"] for w in body_words]) if body_words else DEFAULT_COLUMN_SPLIT
    left_words = [w for w in body_words if w["x0"] < split_x]
    right_words = [w for w in body_words if w["x0"] >= split_x]

    return {
        "page": page_number,
        "width": round(page.width, 2),
        "height": round(page.height, 2),
        "header_text": header_text,
        "header_recognized": header_recognized,
        "column_split_x": round(split_x, 2),
        "left": cluster_lines(left_words),
        "right": cluster_lines(right_words),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default=DEFAULT_PDF, help="path to the source PDF")
    parser.add_argument("--start", type=int, required=True, help="first physical page number (1-based)")
    parser.add_argument("--end", type=int, required=True, help="last physical page number, inclusive")
    parser.add_argument(
        "--out-dir",
        default="tmp/av-ru.1967/geometry",
        help="directory to write one JSON file per page",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(args.pdf) as pdf:
        total = len(pdf.pages)
        if args.start < 1 or args.end > total:
            print(f"error: page range must be within 1..{total}", file=sys.stderr)
            return 1
        for page_number in range(args.start, args.end + 1):
            page = pdf.pages[page_number - 1]
            data = extract_page(page, page_number)
            out_path = out_dir / f"page-{page_number:04d}.json"
            out_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
