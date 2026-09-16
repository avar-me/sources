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
# How close a gap's width must be to the single widest gap (as a fraction)
# to be considered a genuine competitor for the "closest to default" tie-
# break, rather than obviously-narrower noise (see find_column_split).
NEAR_WIDEST_RATIO = 0.85

# Running head looks like "abu — 24 — ava" (left-page-word, page number, right-page-word).
HEADER_PATTERN = re.compile(r"^\S+\s+—\s+\d+\s+—\s+\S+$")


def is_bold(fontname: str) -> bool:
    return "bold" in fontname.lower()


def is_italic(fontname: str) -> bool:
    lowered = fontname.lower()
    return "italic" in lowered or "oblique" in lowered


def find_column_split(xs: list[float]) -> float:
    """Find the column boundary among word x0 values in the plausible middle
    band.

    Prefers the widest gap (the true column margin is usually a clear,
    dominant gap), but when multiple gaps are close in width to each other
    (within NEAR_WIDEST_RATIO), picks whichever of *those* is closest to
    DEFAULT_COLUMN_SPLIT as a tie-breaker. Plain "always widest" fails on
    pages like 551, where a stray mid-line word start creates a slightly
    wider but wrong gap a few points off the true (near-default) margin.
    Plain "always closest to default" fails on pages like 165, where the
    true margin is a clearly dominant gap sitting far from the default
    136pt — picking the closer-to-default but much narrower gap there
    scrambles two columns' worth of a paragraph's continuation lines.
    """
    xs = sorted(xs)
    candidates = [
        (b - a, a, b) for a, b in zip(xs, xs[1:]) if 60.0 < a < 200.0 and (b - a) > 4.0
    ]
    if not candidates:
        return DEFAULT_COLUMN_SPLIT
    widest_gap = max(width for width, _, _ in candidates)
    near_widest = [c for c in candidates if c[0] >= widest_gap * NEAR_WIDEST_RATIO]
    _, best_a, best_b = min(
        near_widest, key=lambda c: abs((c[1] + c[2]) / 2 - DEFAULT_COLUMN_SPLIT)
    )
    return (best_a + best_b) / 2


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
        line = merge_split_letters(line)
        result.append(
            {
                "top": round(min(w["top"] for w in line), 2),
                "bottom": round(max(w["bottom"] for w in line), 2),
                "text": " ".join(w["text"] for w in line),
                "words": line,
            }
        )
    return result


# Some long bold words have their trailing letters split into separate
# single-character "words" by the OCR text layer (found p.107:
# "*бук1кГурк1ах" + 'ъ' + 'д' + 'и' + 'з' + 'а' + 'б' + 'и', each its own
# tightly-spaced token). Real single-letter Avar "words" essentially don't
# occur in this corpus, so a single letter separated from the previous
# token by less than a normal word-space (~5pt) is treated as a fragment of
# it instead of a separate word.
SINGLE_LETTER_RE = re.compile(r"^[а-яёӏӀ]$", re.IGNORECASE)
LETTER_FRAGMENT_MAX_GAP = 4.6


def merge_split_letters(line: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not line:
        return line
    result = [dict(line[0])]
    for tok in line[1:]:
        prev = result[-1]
        gap = tok["x0"] - prev["x1"]
        if (
            SINGLE_LETTER_RE.match(tok["text"])
            and 0 <= gap <= LETTER_FRAGMENT_MAX_GAP
            and tok["bold"] == prev["bold"]
            and tok["italic"] == prev["italic"]
        ):
            prev["text"] = prev["text"] + tok["text"]
            prev["x1"] = tok["x1"]
        else:
            result.append(dict(tok))
    return result


# Line-final hyphen (soft U+00AD or a plain '-') that continues into the
# next line's first word, e.g. "абади-" + "ялъ" -> "абадиялъ". An optional
# leading bracket/quote (e.g. "(от-") is kept as a prefix rather than
# blocking the match, and internal hyphens are allowed so compound words
# like "светло-корич-" + "невый" still match on their final, wrap-only
# hyphen. Only merged when the next word starts lower-case, to avoid
# swallowing a genuine new sentence/proper noun after a coincidental
# line-end hyphen.
TRAILING_HYPHEN_RE = re.compile(r"^([(\[«]?)([А-Яа-яЁёӀӏ]+(?:-[А-Яа-яЁёӀӏ]+)*)[-\u00ad]$")
CONTINUATION_START_RE = re.compile(r"^[а-яёӏ]")


def dehyphenate_column(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rejoin words split by a line-wrap hyphen within one column's lines."""
    lines = [dict(line, words=list(line["words"])) for line in lines]
    i = 0
    while i < len(lines) - 1:
        words = lines[i]["words"]
        next_words = lines[i + 1]["words"]
        if not words or not next_words:
            i += 1
            continue
        match = TRAILING_HYPHEN_RE.match(words[-1]["text"])
        if not match or not CONTINUATION_START_RE.match(next_words[0]["text"]):
            i += 1
            continue
        merged = dict(words[-1], text=match.group(1) + match.group(2) + next_words[0]["text"], x1=next_words[0]["x1"])
        words[-1] = merged
        next_words.pop(0)
        lines[i]["text"] = " ".join(w["text"] for w in words)
        if not next_words:
            del lines[i + 1]
            continue  # re-check lines[i] against its new next neighbour
        lines[i + 1]["text"] = " ".join(w["text"] for w in next_words)
        i += 1
    return lines


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
        "left": dehyphenate_column(cluster_lines(left_words)),
        "right": dehyphenate_column(cluster_lines(right_words)),
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
