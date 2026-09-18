#!/usr/bin/env python3
"""Classify draft articles whose raw_text has unbalanced '[' / ']' counts.

av-ru-1967-review-batch-4-2026-09-17.md, item 6: "классифицировать 96
unclosed-bracket signals на 60 страницах". These are almost always a
single OCR glyph substitution (the closing ']' misread as '!', '1', 'Ц',
dropped entirely, etc., or the opening '[' misread as '\\', 'Ы', dropped)
inside an otherwise complete, coherent entry — NOT a segmentation failure.
Cross-referencing against draft_outcomes.jsonl confirms: of the current
96, 95 are already filtered to the review queue (never published) by the
existing confidence heuristics, and only 1 (шал, homonym 1) reached
accepted — fixed via data/av-ru.1967.corrections.jsonl (see decisions).

This is a non-gating diagnostic (like compare_with_av_ru.py): it doesn't
fail the build, just writes a classification artifact for future review-
queue triage (batch-4 item 9) and prints a summary.

av-ru-1967-review-batch-5-2026-09-18.md, P1 "Исправить семантику bracket
decision": the bulk `bracket-anomalies:batch-4-item-6` decision in
data/av-ru.1967.decisions.jsonl used `decision: "allowlisted"` for 95
items that are still UNRESOLVED in the review queue, which wrongly reads
as "data confirmed correct" rather than "triaged, not yet individually
reviewed". Fixed by (a) using `classified_pending_review` instead, and
(b) committing this artifact (as data/av-ru.1967.bracket_anomalies.jsonl,
not a gitignored tmp file) with a stable `item_id` and a `review_decision`
field (`null` until a future individual review round fills it in) per
row, so each of the 96 anomalies is durably trackable, not just a count.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

POVEL_RE = re.compile(r"\[повел[,.]?\s*\S+!")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def classify(raw_text: str) -> str:
    opens = raw_text.count("[")
    closes = raw_text.count("]")
    if opens > closes:
        if POVEL_RE.search(raw_text):
            return "missing-close-after-повел-imperative-marker"
        return "extra-open-no-close"
    return "extra-close-no-open-or-mismatched"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--draft-outcomes", default="tmp/av-ru.1967/draft_outcomes.jsonl")
    parser.add_argument("--out", default="data/av-ru.1967.bracket_anomalies.jsonl")
    args = parser.parse_args()

    drafts = _load_jsonl(Path(args.drafts))
    outcomes = {row["draft_index"]: row["outcome"] for row in _load_jsonl(Path(args.draft_outcomes))}

    # A stable item_id survives regeneration (it's page+word+draft_index
    # based, not a row position), so any review_decision already recorded
    # by a human/agent review round in the previously committed file must
    # be preserved here rather than reset to null on every rebuild.
    previous_decisions = {
        row["item_id"]: row.get("review_decision")
        for row in _load_jsonl(Path(args.out))
        if row.get("review_decision") is not None
    }

    rows = []
    for i, d in enumerate(drafts):
        raw_text = d.get("raw_text", "")
        if raw_text.count("[") == raw_text.count("]"):
            continue
        item_id = f"bracket-anomaly:p{d.get('page')}:{d.get('word')}:{i}"
        rows.append(
            {
                "item_id": item_id,
                "draft_index": i,
                "page": d.get("page"),
                "word": d.get("word"),
                "outcome": outcomes.get(i, "?"),
                "bucket": classify(raw_text),
                "raw_text_preview": raw_text[:200],
                "review_decision": previous_decisions.get(item_id),
            }
        )

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    pages = {r["page"] for r in rows}
    outcome_counts = Counter(r["outcome"] for r in rows)
    bucket_counts = Counter(r["bucket"] for r in rows)

    print(f"unclosed-bracket draft articles: {len(rows)} on {len(pages)} pages")
    print(f"wrote {out_path}")
    print("by outcome:")
    for k, v in outcome_counts.most_common():
        print(f"  {k}: {v}")
    print("by bucket:")
    for k, v in bucket_counts.most_common():
        print(f"  {k}: {v}")
    accepted_words = [r["word"] for r in rows if r["outcome"] == "accepted"]
    if accepted_words:
        print(f"accepted-outcome words needing individual review: {accepted_words}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
