#!/usr/bin/env python3
"""Build the unified boundary review queue (batch-6, items 4/5/7/8).

av-ru-1967-review-batch-6-segmentation-2026-09-19.md: rather than several
overlapping ledgers, one ranked list on top of article_stream.jsonl's 1674
`alphabet_relation: "regression"` rows (the local-interval boundary
analysis from build_article_stream.py / batch-6 item 3). Every regression
is a CANDIDATE symptom, not a confirmed bug — this script buckets each
into one of the doc's named categories using the SAME heuristics already
used elsewhere in this pipeline (check_order.classify(), the decision
ledger's existing confirmed/resolved rows), plus a simple confidence-based
suspicion score for ranking, and writes one row per candidate with both
neighbors, sort keys, and a `boundary_decision` slot (null until reviewed
— matches the classify_bracket_anomalies.py / classify_missing_links.py
pattern already used twice this project for "classified, not yet all
individually fixed").

Writes data/av-ru.1967.boundary_queue.jsonl (non-gating diagnostic).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from check_order import classify  # noqa: E402
from decision_ledger import (  # noqa: E402
    RESOLVED_DECISIONS,
    check_decision,
    load_decisions,
    order_regression_hash,
    order_regression_id,
)
from quality_scan import RUSSIAN_GRAMMAR_RE, has_avar_signal  # noqa: E402
from segment_entries import RUSSIAN_FUNCTION_WORDS, load_known_words  # noqa: E402

# check_order.py's own heuristic buckets that are already well-understood,
# documented-safe patterns (spot-checked in prior steps) rather than real
# boundary bugs — mapped straight to "source-order-exception".
_SAFE_SUGGESTED = {"hyphen-reduplication"}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _looks_like_false_headword(word: str, known_words: set[str]) -> bool:
    # Same gates as check_accepted.py's suspicious_headword_reason(): a
    # real Avar/Russian homograph ("как") or any word already confirmed in
    # the modern dictionary must NOT be flagged just for looking Russian —
    # without this, genuine self-gloss loanword headwords (пионервожатый,
    # мягкий) and homographs (как) dominate the false-positive rate.
    if has_avar_signal(word) or word in known_words:
        return False
    lowered = word.strip(",.;:!?").lower()
    return bool(RUSSIAN_GRAMMAR_RE.search(word)) or lowered in RUSSIAN_FUNCTION_WORDS


def categorize(
    row: dict[str, Any],
    prev_row: dict[str, Any] | None,
    known_words: set[str],
    decisions: dict[str, dict[str, Any]],
) -> tuple[str, str | None]:
    """Returns (category, resolved_note). `resolved_note` is set when an
    existing decision ledger row already covers this exact pair (by hash) —
    the queue still lists it (for the "all regressions get a boundary
    decision" stop condition) but it's not a fresh candidate to review."""
    prev_word = prev_row["headword"] if prev_row else ""
    word = row["headword"]
    ledger_id = order_regression_id(prev_word, word)
    ledger_key = order_regression_hash(
        prev_word, word, prev_row["page"] if prev_row else 0, row["page"], prev_row.get("raw_text", "") if prev_row else "", row.get("raw_text", "")
    )
    status, decision_row = check_decision(decisions, ledger_id, ledger_key)
    if status == "valid" and decision_row["decision"] in RESOLVED_DECISIONS:
        return "source-order-exception", f"resolved:{decision_row['category']}"

    suggested = classify(prev_word, word, known_words) if prev_row else "unclassified"
    if suggested in _SAFE_SUGGESTED:
        return "source-order-exception", f"suggested:{suggested}"
    # check_order.classify()'s own "false-headword" branch has no
    # known_words/avar-signal gate (it flags ANY Russian-function-word or
    # grammar-suffix match on EITHER neighbor) — a real Avar/Russian
    # homograph like "\u043a\u0430\u043a" would trigger it on every regression it's
    # involved in. Re-verify against THIS row's own word with the same
    # gates check_accepted.py's suspicious-headword check uses before
    # trusting that suggestion.
    if suggested == "false-headword" and _looks_like_false_headword(word, known_words):
        return "probable-false-headword", None

    own_confidence = row.get("parse_confidence")
    if own_confidence != "high":
        # a regression whose OWN word is already low/medium-confidence OCR
        # is genuinely uncertain, not a confidently-wrong boundary — same
        # distinction check_accepted.py's suspicious-headword logic draws.
        return "ocr-headword-uncertain", None
    if _looks_like_false_headword(word, known_words):
        return "probable-false-headword", None
    if prev_row is not None and (prev_row.get("raw_text_length") or len(prev_row.get("raw_text", ""))) > 500:
        # a long preceding span is exactly the missed-mid-paragraph-
        # headword-split shape found repeatedly this project (batch-5's 5
        # bracket-anomaly splits, batch-6's 4 dead-zone splits).
        return "probable-missed-headword", None
    return "unclassified-boundary-candidate", None


def suspicion_score(row: dict[str, Any], category: str) -> int:
    score = 0
    if row.get("parse_confidence") == "high":
        score += 2
    if category == "probable-false-headword":
        score += 3
    elif category == "probable-missed-headword":
        score += 2
    elif category == "unclassified-boundary-candidate":
        score += 1
    if row.get("boundary_confidence") == "low":
        score += 1
    return score


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", default="data/av-ru.1967.article_stream.jsonl")
    parser.add_argument("--known-words", default="data/av-ru.jsonl")
    parser.add_argument("--out", default="data/av-ru.1967.boundary_queue.jsonl")
    args = parser.parse_args()

    known_words = load_known_words(Path(args.known_words))
    stream = _load_jsonl(Path(args.stream))
    decisions = load_decisions()

    by_id = {r["article_id"]: r for r in stream}

    previous_decisions = {
        row["article_id"]: row.get("boundary_decision")
        for row in _load_jsonl(Path(args.out))
        if row.get("boundary_decision") is not None
    }

    queue: list[dict[str, Any]] = []
    for i, row in enumerate(stream):
        if row["alphabet_relation"] != "regression":
            continue
        prev_row = stream[i - 1] if i > 0 else None
        category, resolved_note = categorize(row, prev_row, known_words, decisions)
        score = suspicion_score(row, category)
        queue.append(
            {
                "article_id": row["article_id"],
                "headword": row["headword"],
                "headword_raw": row["headword_raw"],
                "page": row["page"],
                "column": row["column"],
                "category": category,
                "resolved_note": resolved_note,
                "suspicion_score": score,
                "parse_confidence": row.get("parse_confidence"),
                "boundary_confidence": row.get("boundary_confidence"),
                "current_outcome": row.get("current_outcome"),
                "previous_article_id": row.get("previous_article_id"),
                "previous_headword": row.get("previous_headword"),
                "next_article_id": row.get("next_article_id"),
                "next_headword": row.get("next_headword"),
                "raw_text": row.get("raw_text", "")[:300],
                "previous_raw_text": (prev_row or {}).get("raw_text", "")[:300],
                "operation": None,
                "needs_pdf_review": None,
                "boundary_decision": previous_decisions.get(row["article_id"]),
            }
        )

    queue.sort(key=lambda r: -r["suspicion_score"])

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in queue:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    from collections import Counter

    print(f"boundary queue: {len(queue)} candidates, wrote {out_path}")
    print("by category:", dict(Counter(r["category"] for r in queue).most_common()))
    print("by suspicion_score:", dict(sorted(Counter(r["suspicion_score"] for r in queue).items(), reverse=True)))
    resolved = sum(1 for r in queue if r["resolved_note"])
    reviewed = sum(1 for r in queue if r["boundary_decision"])
    print(f"already resolved by existing decision ledger: {resolved}")
    print(f"already individually reviewed (boundary_decision set): {reviewed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
