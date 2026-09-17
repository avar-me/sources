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
from build_dataset import rescue_word, split_pipe_corruption  # noqa: E402
from segment_entries import load_known_words  # noqa: E402

_SORT_KEY = make_sort_key(make_rank(AVAR_ALPHABET), make_tokenizer("av"))


def rescued_word(word: str, known_words: set[str]) -> str:
    word, _ = split_pipe_corruption(word)
    word, _ = rescue_word(word, known_words)
    return word


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--known-words", default="data/av-ru.jsonl")
    parser.add_argument("--out", default="tmp/av-ru.1967/order_check.jsonl")
    args = parser.parse_args()

    articles_path = Path(args.articles)
    out_path = Path(args.out)
    known_words = load_known_words(Path(args.known_words))

    prev = None
    prev_key = None
    issues = []
    total = 0
    with articles_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            article = json.loads(line)
            total += 1
            word = rescued_word(article["word"], known_words)
            key = _SORT_KEY(word)
            if prev is not None and key < prev_key:
                issues.append(
                    {
                        "prev": {
                            "page": prev["page"],
                            "word": prev["word_rescued"],
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
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
