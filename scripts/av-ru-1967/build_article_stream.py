#!/usr/bin/env python3
"""Build the unified, physically-ordered article stream (batch-6, item 1).

av-ru-1967-review-batch-6-segmentation-2026-09-19.md: before this, the
accepted/review split hid the book's true physical layout from any single
tool — check_order.py sees the full draft stream but not `current_entry`/
`current_outcome`; check_accepted.py sees only the published subset, so a
page with zero accepted entries (a "dead zone") is invisible to it. This
script merges draft_articles.jsonl (physical book order, ALL outcomes) with
data/av-ru.1967.jsonl+provenance (accepted) and needs_review.jsonl (review)
into ONE row per physical article, with a stable `article_id` (position-
based, survives content fixes — item 1's requirement), and does the local
alphabetical-interval boundary analysis (item 3) against the nearest
TRUSTED anchors on each side — trusted meaning parse-confidence "high",
regardless of accepted/review outcome, which is exactly what makes dead
zones (pages with zero ACCEPTED anchors but real high-confidence review
articles) analyzable at all (item 6).

Writes data/av-ru.1967.article_stream.jsonl, one row per draft article
(13k+ rows) in physical book order. Non-gating diagnostic (like
compare_with_av_ru.py) — this is infrastructure for the boundary review
queue (build_boundary_queue.py), not a build-breaking check itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from check_order import _SORT_KEY, classify, rescued_word  # noqa: E402
from segment_entries import load_known_words  # noqa: E402


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def article_id(page: int, column: str, top: float) -> str:
    col = (column or "?")[:1]
    return f"p{page:04d}-{col}-{int(round(top * 100)):05d}"


def _key3(row: dict[str, Any]) -> tuple[int, str, float]:
    return (row["page"], row["column"], round(row["top"], 2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--draft-outcomes", default="tmp/av-ru.1967/draft_outcomes.jsonl")
    parser.add_argument("--accepted", default="data/av-ru.1967.jsonl")
    parser.add_argument("--provenance", default="data/av-ru.1967.provenance.jsonl")
    parser.add_argument("--review", default="tmp/av-ru.1967/needs_review.jsonl")
    parser.add_argument("--known-words", default="data/av-ru.jsonl")
    parser.add_argument("--out", default="data/av-ru.1967.article_stream.jsonl")
    args = parser.parse_args()

    known_words = load_known_words(Path(args.known_words))
    drafts = _load_jsonl(Path(args.drafts))
    outcomes = _load_jsonl(Path(args.draft_outcomes))
    accepted = _load_jsonl(Path(args.accepted))
    provenance = _load_jsonl(Path(args.provenance))
    review = _load_jsonl(Path(args.review))

    assert len(drafts) == len(outcomes), "draft_articles.jsonl / draft_outcomes.jsonl out of sync"

    # Keyed by physical position, not by list order — apply_corrections.py
    # removes/replaces accepted entries in place, so a draft's original
    # (page, column, top) may no longer have a matching accepted row (it was
    # a false headword that got removed) even though the outcome ledger
    # still says "accepted" (that ledger reflects the PRE-correction state).
    current_by_key: dict[tuple[int, str, float], dict[str, Any]] = {}
    for entry, prov in zip(accepted, provenance):
        current_by_key[_key3(prov)] = {"outcome": "accepted", "entry": entry, "bbox": prov.get("bbox"), "prov": prov}
    for row in review:
        current_by_key[_key3(row)] = {"outcome": "review", "entry": row.get("entry", {}), "bbox": row.get("bbox")}

    # First pass: rescue words + sort keys for the WHOLE physical stream
    # (every draft article, regardless of outcome) — this is what makes
    # dead-zone pages analyzable: a page with 0 accepted entries can still
    # have high-confidence REVIEW articles serving as trusted anchors.
    rescued: list[str] = []
    keys: list[tuple] = []
    for d in drafts:
        w = rescued_word(d["word"], known_words)
        rescued.append(w)
        keys.append(_SORT_KEY(w))

    trusted = [d.get("confidence") == "high" for d in drafts]

    rows: list[dict[str, Any]] = []
    for i, d in enumerate(drafts):
        outcome_row = outcomes[i]
        draft_outcome = outcome_row["outcome"]
        key3 = (d["page"], d["column"], round(d["top"], 2))
        current = current_by_key.get(key3)
        if current is not None:
            current_outcome = current["outcome"]
            current_entry = current["entry"]
            bbox = current["bbox"]
        else:
            # accepted at parse time, but no longer present at this
            # position — either removed by a correction (false headword)
            # or genuinely dropped/duplicate at the draft stage.
            current_outcome = "removed-by-correction" if draft_outcome == "accepted" else draft_outcome
            current_entry = {}
            bbox = None

        prov = current.get("prov") if current else None
        source_pages = prov.get("source_pages") if prov else None
        if source_pages:
            source_spans = [{"page": p, "bbox": bbox if p == d["page"] else None} for p in source_pages]
        else:
            source_spans = [{"page": d["page"], "bbox": bbox}]

        rows.append(
            {
                "article_id": article_id(d["page"], d["column"], d["top"]),
                "draft_index": i,
                "headword_raw": d["word_raw"],
                "headword": rescued[i],
                "page": d["page"],
                "column": d["column"],
                "top": d["top"],
                "parse_confidence": d.get("confidence"),
                "parse_reasons": d.get("reasons", []),
                "source_spans": source_spans,
                "raw_text": d.get("raw_text", ""),
                "current_entry": current_entry,
                "current_outcome": current_outcome,
                "boundary_confidence": None,  # filled in pass 2
                "boundary_reasons": [],  # filled in pass 2
                "previous_article_id": None,
                "previous_headword": None,
                "next_article_id": None,
                "next_headword": None,
                "alphabet_relation": None,  # filled in pass 2
                "boundary_decision": None,
            }
        )

    # Second pass: physical neighbors + local-interval alphabet analysis
    # against the nearest TRUSTED anchor on each side (item 3/6).
    n = len(rows)
    for i, row in enumerate(rows):
        if i > 0:
            row["previous_article_id"] = rows[i - 1]["article_id"]
            row["previous_headword"] = rows[i - 1]["headword"]
        if i < n - 1:
            row["next_article_id"] = rows[i + 1]["article_id"]
            row["next_headword"] = rows[i + 1]["headword"]

        left = next((j for j in range(i - 1, -1, -1) if trusted[j]), None)
        right = next((j for j in range(i + 1, n) if trusted[j]), None)

        reasons = []
        if left is None or right is None:
            relation = "uncertain"
        else:
            in_order = keys[left] <= keys[i] <= keys[right]
            if keys[i] == keys[left] or keys[i] == keys[right]:
                relation = "equal"
            elif in_order:
                relation = "in-order"
            else:
                relation = "regression"
                if keys[i] < keys[left]:
                    reasons.append(f"below-trusted-left:{rows[left]['headword']}")
                if keys[i] > keys[right]:
                    reasons.append(f"above-trusted-right:{rows[right]['headword']}")

        if relation == "regression" and i > 0:
            reasons.append(f"suggested_category:{classify(rows[i - 1]['headword'], rows[i]['headword'], known_words)}")

        row["alphabet_relation"] = relation
        row["boundary_reasons"] = reasons
        if relation in ("in-order", "equal"):
            row["boundary_confidence"] = "high" if trusted[i] else "medium"
        elif relation == "regression":
            row["boundary_confidence"] = "low" if trusted[i] else "medium"
        else:
            row["boundary_confidence"] = "medium"

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    from collections import Counter

    print(f"wrote {len(rows)} article_stream rows to {out_path}")
    print("by current_outcome:", dict(Counter(r["current_outcome"].split(":")[0] for r in rows).most_common()))
    print("by alphabet_relation:", dict(Counter(r["alphabet_relation"] for r in rows).most_common()))
    print("by boundary_confidence:", dict(Counter(r["boundary_confidence"] for r in rows).most_common()))
    zero_trusted_pages = sorted({rows[i]["page"] for i in range(n) if not trusted[i]} - {rows[i]["page"] for i in range(n) if trusted[i]})
    if zero_trusted_pages:
        print(f"pages with ZERO trusted (high-confidence) anchors at all: {zero_trusted_pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
