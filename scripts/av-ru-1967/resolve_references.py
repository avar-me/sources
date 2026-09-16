#!/usr/bin/env python3
"""Resolve draft see_also candidates against the full parsed article list.

Step 5 of av-ru-1967-parsing-handoff.md ("второй проход"): reference_targets
(ср./см.) and from_targets (от X) collected by parse_articles.py are just
normalized word guesses until they can be checked against every other
article's `word` — which requires the whole book to be parsed first.

This does not mutate draft_articles.jsonl. It reports, per article: which
targets resolved to an exact `word` match, which resolved only after
palochka/case normalization, and which did not resolve at all (candidates
for the "unresolved links" review queue).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from build_site import normalize_palochka  # noqa: E402


def normalize(word: str) -> str:
    return normalize_palochka(word).lower().strip("*")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--out", default="tmp/av-ru.1967/unresolved_links.jsonl")
    args = parser.parse_args()

    articles = [json.loads(line) for line in Path(args.articles).open("r", encoding="utf-8")]
    known = {normalize(a["word"]) for a in articles}

    resolved = 0
    unresolved: list[dict[str, Any]] = []
    for article in articles:
        for sense in article.get("senses", []):
            for kind, key in (("see", "reference_targets"), ("from", "from_targets")):
                for target in sense.get(key, []):
                    if normalize(target) in known:
                        resolved += 1
                    else:
                        unresolved.append(
                            {
                                "page": article["page"],
                                "word": article["word"],
                                "kind": kind,
                                "target": target,
                                "raw_text": article["raw_text"][:160],
                            }
                        )

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as fh:
        for item in unresolved:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    total = resolved + len(unresolved)
    print(f"{total} see_also/from candidates: {resolved} resolved, {len(unresolved)} unresolved")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
