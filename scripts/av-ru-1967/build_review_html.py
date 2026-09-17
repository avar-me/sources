#!/usr/bin/env python3
"""Static HTML review queue for tmp/av-ru.1967/needs_review.jsonl.

av-ru-1967-review-batch-3-2026-09-17.md, "P1. Построить HTML review
queue": review entries so far only existed as raw JSONL rows — no visual
way for a human reviewer to see the scanned page next to the proposed
JSON, no priority ordering, no link to the persistent decision ledger, no
progress report. This generates a self-contained local HTML site (one page
per priority-ordered review item, cross-linked, each with a rendered
page image PLUS a cropped close-up of the item's own printed line
(via geometry_lookup.py's bbox, when available), the raw OCR text,
proposed entry JSON, reasons/parse_issues, neighbor headwords, stable
id/source hash, and current decision-ledger status).

This is intentionally NOT part of build_all.sh's default run: rendering
one image per distinct review-queue page (570+ pages) is slow on a cold
cache. Run it explicitly:

    python3 scripts/av-ru-1967/build_review_html.py

Output goes to tmp/av-ru.1967/review_html/ (gitignored, regenerated on
demand) — page images are cached by filename, so repeat runs after the
first are fast unless --force-images is passed.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from decision_ledger import load_decisions, review_item_hash, review_item_id  # noqa: E402
from geometry_lookup import bbox_for  # noqa: E402

CROP_PAD_POINTS = 20  # extra margin around the matched line's bbox, in PDF points

PRIORITY_LABELS = [
    "boundary-high-demoted",
    "page-boundary-carry",
    "oversized-span",
    "touches-order-regression",
    "medium-confidence",
    "low-confidence",
]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def classify_priority(row: dict[str, Any], regression_pages: set[int]) -> tuple[int, str]:
    if row.get("confidence") == "high" and row.get("parse_issues"):
        return 0, PRIORITY_LABELS[0]
    if row.get("continues_next_page"):
        return 1, PRIORITY_LABELS[1]
    if len(row.get("raw_text") or "") > 1000:
        return 2, PRIORITY_LABELS[2]
    if row.get("page") in regression_pages:
        return 3, PRIORITY_LABELS[3]
    if row.get("confidence") == "medium":
        return 4, PRIORITY_LABELS[4]
    return 5, PRIORITY_LABELS[5]


PAGE_RESOLUTION = 150


def render_page_image(pdf, page_num: int, out_dir: Path, force: bool) -> str:
    out_path = out_dir / f"page-{page_num:04d}.png"
    if force or not out_path.exists():
        image = pdf.pages[page_num - 1].to_image(resolution=PAGE_RESOLUTION)
        image.save(str(out_path))
    return out_path.name


def crop_item_image(page_png_path: Path, bbox: tuple[float, float, float, float], crops_dir: Path, name: str, force: bool) -> str | None:
    """Crop a close-up of one item's printed line out of the already-
    rendered full-page PNG (cheap — no extra PDF render needed)."""
    out_path = crops_dir / f"{name}.png"
    if not force and out_path.exists():
        return out_path.name
    from PIL import Image

    scale = PAGE_RESOLUTION / 72.0
    x0, top, x1, bottom = bbox
    x0 -= CROP_PAD_POINTS
    x1 += CROP_PAD_POINTS
    top -= CROP_PAD_POINTS * 2
    bottom += CROP_PAD_POINTS * 2
    with Image.open(page_png_path) as img:
        w, h = img.size
        left = max(0, int(x0 * scale))
        right = min(w, int(x1 * scale))
        upper = max(0, int(top * scale))
        lower = min(h, int(bottom * scale))
        if right <= left or lower <= upper:
            return None
        crop = img.crop((left, upper, right, lower))
        crop.save(str(out_path))
    return out_path.name


def item_html(row: dict[str, Any], item_id: str, decision_row: dict[str, Any] | None, page_image: str | None, crop_image: str | None) -> str:
    entry = row.get("entry", {})
    decision_html = (
        f"<p class='decision'>Decision: <b>{html.escape(decision_row['decision'])}</b> "
        f"({html.escape(decision_row['category'])}) — {html.escape(decision_row['reason'])}</p>"
        if decision_row
        else "<p class='decision pending'>Decision: none yet</p>"
    )
    page_num = row.get("page")
    crop_html = (
        f"<img src='crops/{crop_image}' alt='crop for {html.escape(str(page_num))}' class='crop'>"
        if crop_image
        else "<p><i>no bbox available for this item (see geometry_lookup.py)</i></p>"
    )
    image_html = (
        f"<img src='pages/{page_image}' alt='page {page_num}' loading='lazy'>"
        if page_image
        else "<p><i>page image not rendered</i></p>"
    )
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>{html.escape(row.get('word_raw') or entry.get('word') or item_id)}</title>
<link rel="stylesheet" href="style.css"></head>
<body>
<a href="index.html">&laquo; back to index</a>
<h1>{html.escape(entry.get('word') or row.get('word_raw') or '')}</h1>
<p class="meta">page {row.get('page')} · column {row.get('column')} · top {row.get('top')} ·
confidence {row.get('confidence')} · id <code>{html.escape(item_id)}</code></p>
<p class="meta">prev: {html.escape(str(row.get('prev_word')))} · next: {html.escape(str(row.get('next_word')))} ·
continues_next_page: {row.get('continues_next_page')}</p>
<p class="reasons">reasons: {html.escape(', '.join(row.get('reasons') or []))} ·
parse_issues: {html.escape(', '.join(row.get('parse_issues') or []))}</p>
{decision_html}
<h2>Close-up</h2>
{crop_html}
<h2>Full page</h2>
{image_html}
<h2>Raw OCR</h2>
<pre>{html.escape(row.get('raw_text') or '')}</pre>
<h2>Proposed entry</h2>
<pre>{html.escape(json.dumps(entry, ensure_ascii=False, indent=2))}</pre>
</body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--needs-review", default="tmp/av-ru.1967/needs_review.jsonl")
    parser.add_argument("--order-check", default="tmp/av-ru.1967/order_check.jsonl")
    parser.add_argument("--pdf", default="books/saidov_m_avarskorusskii_slovar.pdf")
    parser.add_argument("--geometry-dir", default="tmp/av-ru.1967/geometry")
    parser.add_argument("--out-dir", default="tmp/av-ru.1967/review_html")
    parser.add_argument("--force-images", action="store_true")
    parser.add_argument("--skip-images", action="store_true", help="Skip rendering page images (fast, for iterating on HTML/layout).")
    args = parser.parse_args()

    rows = _load_jsonl(Path(args.needs_review))
    order_issues = _load_jsonl(Path(args.order_check))
    regression_pages: set[int] = set()
    for issue in order_issues:
        regression_pages.add(issue["prev"]["page"])
        regression_pages.add(issue["next"]["page"])

    decisions = load_decisions()

    out_dir = Path(args.out_dir)
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    crops_dir = out_dir / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    geometry_dir = Path(args.geometry_dir)

    items = []
    for row in rows:
        priority_rank, priority_label = classify_priority(row, regression_pages)
        items.append((priority_rank, priority_label, row))
    items.sort(key=lambda t: (t[0], t[2].get("page") or 0, t[2].get("top") or 0))

    pdf = None
    if not args.skip_images:
        import pdfplumber

        pdf = pdfplumber.open(args.pdf)

    rendered_pages: dict[int, str] = {}
    (out_dir / "style.css").write_text(
        "body{font-family:sans-serif;max-width:900px;margin:2em auto;padding:0 1em}"
        "img{max-width:100%;border:1px solid #ccc}"
        "img.crop{border:2px solid #060}"
        "pre{background:#f5f5f5;padding:1em;overflow-x:auto;white-space:pre-wrap}"
        ".pending{color:#a00}.decision{color:#060}"
        "table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #ddd;padding:4px 8px;text-align:left;font-size:0.9em}"
        "tr.decided{background:#eafbea}\n",
        encoding="utf-8",
    )

    index_rows = []
    decided_count = 0
    for priority_rank, priority_label, row in items:
        word = row.get("entry", {}).get("word") or row.get("word_raw") or "?"
        page = row.get("page")
        top = row.get("top")
        column = row.get("column")
        item_id = review_item_id(word, page, column, top)
        item_hash = review_item_hash(word, page, column, top, row.get("raw_text") or "")
        decision_row = decisions.get(item_id)
        if decision_row and decision_row.get("source_hash") == item_hash:
            decided_count += 1
        else:
            decision_row = None

        page_image = None
        if pdf is not None and page is not None:
            if page not in rendered_pages:
                rendered_pages[page] = render_page_image(pdf, page, pages_dir, args.force_images)
            page_image = rendered_pages[page]

        crop_image = None
        bbox = row.get("bbox") or bbox_for(geometry_dir, page, column, top)
        if page_image and bbox:
            crop_image = crop_item_image(
                pages_dir / page_image, tuple(bbox), crops_dir, f"item-{len(index_rows):05d}", args.force_images
            )

        filename = f"item-{len(index_rows):05d}.html"
        (out_dir / filename).write_text(item_html(row, item_id, decision_row, page_image, crop_image), encoding="utf-8")
        index_rows.append((priority_label, word, page, filename, decision_row is not None))

    by_priority: dict[str, int] = {}
    for label, *_ in index_rows:
        by_priority[label] = by_priority.get(label, 0) + 1

    def _row_html(label: str, word: str, page: Any, filename: str, decided: bool) -> str:
        row_class = "decided" if decided else ""
        decided_text = "yes" if decided else ""
        return (
            f"<tr class='{row_class}'>"
            f"<td>{html.escape(label)}</td><td>{html.escape(word)}</td><td>{page}</td>"
            f"<td><a href='{filename}'>open</a></td><td>{decided_text}</td></tr>"
        )

    table_rows = "\n".join(
        _row_html(label, word, page, filename, decided)
        for label, word, page, filename, decided in index_rows
    )
    summary_rows = "\n".join(f"<li>{html.escape(label)}: {count}</li>" for label, count in sorted(by_priority.items()))
    index_html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>av-ru.1967 review queue</title>
<link rel="stylesheet" href="style.css"></head>
<body>
<h1>av-ru.1967 review queue</h1>
<p>{len(index_rows)} items total. {decided_count} already have a ledger decision, {len(index_rows) - decided_count} remaining.</p>
<h2>By priority</h2>
<ul>{summary_rows}</ul>
<h2>All items (priority order)</h2>
<table><tr><th>priority</th><th>word</th><th>page</th><th></th><th>decided</th></tr>
{table_rows}
</table>
</body></html>
"""
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")

    print(f"{len(index_rows)} review items written to {out_dir}/index.html")
    for label, count in sorted(by_priority.items()):
        print(f"  {label}: {count}")
    print(f"progress: {decided_count} decided, {len(index_rows) - decided_count} remaining")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
