#!/usr/bin/env python3
"""Book-wide alphabetical order check for draft articles.

The 1967 dictionary is one continuous A-Z listing across pages 23-619, so
any two consecutive parsed articles should have non-decreasing Avar sort
keys. A regression usually means a real segmentation/parsing bug (a missed
headword, a merged article, wrong reading order across columns/pages) —
not just an OCR stress-mark artifact, since those were already flagged
separately during segmentation (see "alphabet-regression" in segments.jsonl).

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

_SORT_KEY = make_sort_key(make_rank(AVAR_ALPHABET), make_tokenizer("av"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--out", default="tmp/av-ru.1967/order_check.jsonl")
    args = parser.parse_args()

    articles_path = Path(args.articles)
    out_path = Path(args.out)

    prev = None
    prev_key = None
    issues = []
    total = 0
    with articles_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            article = json.loads(line)
            total += 1
            key = _SORT_KEY(article["word"])
            if prev is not None and key < prev_key:
                issues.append(
                    {
                        "prev": {
                            "page": prev["page"],
                            "word": prev["word"],
                            "confidence": prev["confidence"],
                            "raw_text": prev["raw_text"][:120],
                        },
                        "next": {
                            "page": article["page"],
                            "word": article["word"],
                            "confidence": article["confidence"],
                            "raw_text": article["raw_text"][:120],
                        },
                    }
                )
            prev, prev_key = article, key

    with out_path.open("w", encoding="utf-8") as fh:
        for issue in issues:
            fh.write(json.dumps(issue, ensure_ascii=False) + "\n")

    both_high = sum(
        1 for i in issues if i["prev"]["confidence"] == "high" and i["next"]["confidence"] == "high"
    )
    print(f"{total} articles, {len(issues)} order regressions ({both_high} both high-confidence)")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
