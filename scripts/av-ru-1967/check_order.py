#!/usr/bin/env python3
"""Book-wide alphabetical order check for draft articles.

The 1967 dictionary is one continuous A-Z listing across pages 23-619, so
any two consecutive parsed articles should have non-decreasing Avar sort
keys. A regression usually means a real segmentation/parsing bug (a missed
headword, a merged article, wrong reading order across columns/pages) —
not just an OCR stress-mark artifact. Words are rescued the same way
build_dataset.py does (STRESS_GLYPHS б/6/й/ё substitution + '||'-as-ц/Ц
pipe-corruption split, both gated on known_words) before computing the
sort key, so a headword like "бёлъине" (should read "белъине") doesn't
masquerade as a segmentation bug just because its stressed vowel got OCR'd
as the wrong letter — real segmentation bugs (a missed headword, a merged
article, wrong reading order across columns/pages) are what's left over.

Reads draft_articles.jsonl (one line per article, in book reading order —
see parse_articles.py) and reports every backward step with enough context
to look the pair up in the PDF.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from build_site import AVAR_ALPHABET, make_rank, make_sort_key, make_tokenizer  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from baseline import check_metric, load_baselines  # noqa: E402
from build_dataset import rescue_word, split_pipe_corruption  # noqa: E402
from decision_ledger import (  # noqa: E402
    check_decision,
    load_decisions,
    order_regression_hash,
    order_regression_id,
)
from quality_scan import RUSSIAN_GRAMMAR_RE  # noqa: E402
from segment_entries import RUSSIAN_FUNCTION_WORDS, load_known_words  # noqa: E402

_SORT_KEY = make_sort_key(make_rank(AVAR_ALPHABET), make_tokenizer("av"))


def rescued_word(word: str, known_words: set[str]) -> str:
    word, _ = split_pipe_corruption(word)
    word, _ = rescue_word(word, known_words)
    return word


def _is_hyphen_reduplication(word: str) -> bool:
    """"бакк-баккизе" vs "бакки" — a hyphenated reduplicated verb form and its
    plain counterpart sort differently around the hyphen than a naïve
    expectation, purely due to how the shared tokenizer handles "-" (not a
    segmentation bug — spot-checked several of these pairs, both sides are
    genuinely distinct, cleanly-parsed entries). Detected as: contains "-"
    and one side of the hyphen is a prefix of the other."""
    if "-" not in word:
        return False
    parts = word.split("-")
    return any(
        (a == b or a.startswith(b) or b.startswith(a))
        for a, b in zip(parts, parts[1:])
    )


def classify(prev_word: str, next_word: str, known_words: set[str]) -> str:
    """Best-effort, UNPROVEN root-cause guess for a regression pair — per
    av-ru-1967-review-batch-3-2026-09-17.md's "P1. Сделать классификацию
    regressions доказуемой", this is only ever a `suggested_category` — a
    heuristic hypothesis, not a fact. It only becomes `confirmed_category`
    once a human decision with scan evidence is recorded in
    data/av-ru.1967.decisions.jsonl (see decision_ledger.py). Checked in
    order of confidence — a pair can match more than one heuristic, so the
    first, most specific match wins."""
    for w in (prev_word, next_word):
        if ("й" in w or "ё" in w) and w not in known_words:
            return "stress-glyph-unresolved"
    if _is_hyphen_reduplication(prev_word) or _is_hyphen_reduplication(next_word):
        return "hyphen-reduplication"
    for w in (prev_word, next_word):
        lowered = w.strip(",.;:!?").lower()
        if lowered in RUSSIAN_FUNCTION_WORDS or RUSSIAN_GRAMMAR_RE.search(lowered):
            return "false-headword"
    return "unclassified"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--known-words", default="data/av-ru.jsonl")
    parser.add_argument("--out", default="tmp/av-ru.1967/order_check.jsonl")
    args = parser.parse_args()

    articles_path = Path(args.articles)
    out_path = Path(args.out)
    known_words = load_known_words(Path(args.known_words))
    decisions = load_decisions()

    prev = None
    prev_key = None
    issues = []
    total = 0
    ledger_conflicts = 0
    with articles_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            article = json.loads(line)
            total += 1
            word = rescued_word(article["word"], known_words)
            key = _SORT_KEY(word)
            if prev is not None and key < prev_key:
                prev_word = prev["word_rescued"]
                suggested = classify(prev_word, word, known_words)
                ledger_id = order_regression_id(prev_word, word)
                ledger_key = order_regression_hash(prev_word, word, prev["page"], article["page"])
                status, row = check_decision(decisions, ledger_id, ledger_key)
                confirmed = row["category"] if status == "valid" else None
                if status == "conflict":
                    ledger_conflicts += 1
                issues.append(
                    {
                        "suggested_category": suggested,
                        "confirmed_category": confirmed,
                        "ledger_status": status,
                        "category": confirmed or suggested,
                        "prev": {
                            "page": prev["page"],
                            "word": prev_word,
                            "confidence": prev["confidence"],
                            "raw_text": prev["raw_text"][:120],
                        },
                        "next": {
                            "page": article["page"],
                            "word": word,
                            "confidence": article["confidence"],
                            "raw_text": article["raw_text"][:120],
                        },
                    }
                )
            article["word_rescued"] = word
            prev, prev_key = article, key

    with out_path.open("w", encoding="utf-8") as fh:
        for issue in issues:
            fh.write(json.dumps(issue, ensure_ascii=False) + "\n")

    both_high = sum(
        1 for i in issues if i["prev"]["confidence"] == "high" and i["next"]["confidence"] == "high"
    )
    print(f"{total} articles, {len(issues)} order regressions ({both_high} both high-confidence)")
    by_category: dict[str, int] = {}
    by_category_high_high: dict[str, int] = {}
    for i in issues:
        by_category[i["category"]] = by_category.get(i["category"], 0) + 1
        if i["prev"]["confidence"] == "high" and i["next"]["confidence"] == "high":
            by_category_high_high[i["category"]] = by_category_high_high.get(i["category"], 0) + 1
    for cat, count in sorted(by_category.items(), key=lambda kv: -kv[1]):
        print(f"  {cat}: {count} ({by_category_high_high.get(cat, 0)} high/high)")
    print(f"wrote {out_path}")
    confirmed_count = sum(1 for i in issues if i["ledger_status"] == "valid")
    print(f"  {confirmed_count} of {len(issues)} regressions have a confirmed (ledger) category")
    if ledger_conflicts:
        print(f"  LEDGER CONFLICT: {ledger_conflicts} decision(s) no longer match their source facts — re-review needed")

    # av-ru-1967-review-batch-2-2026-09-17.md, "P1. Исправить декларацию полного
    # pipeline": these are temporary, non-zero baselines (unlike
    # quality_scan.py's hard 0) — the build fails if any of them get WORSE,
    # but doesn't yet require perfection. Lower baselines.json as real fixes
    # land (see check_metric's "improved" note).
    baselines = load_baselines()
    ok = True
    ok &= check_metric("order_check.total_regressions", len(issues), baselines)
    ok &= check_metric("order_check.high_high", both_high, baselines)
    ok &= check_metric("order_check.unclassified", by_category.get("unclassified", 0), baselines)
    ok &= check_metric(
        "order_check.unclassified_high_high",
        by_category_high_high.get("unclassified", 0),
        baselines,
    )
    # av-ru-1967-review-batch-3-2026-09-17.md, "P0. Создать persistent decision
    # ledger": a decision whose source facts no longer match what's in the
    # ledger must NEVER be silently reused — hard 0, not a baseline.
    if ledger_conflicts:
        print(f"HARD GATE FAILED: {ledger_conflicts} decision_ledger conflict(s)")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
