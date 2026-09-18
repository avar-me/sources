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

sys.path.insert(0, str(Path(__file__).parent))
from baseline import check_metric, load_baselines  # noqa: E402


def normalize(word: str) -> str:
    return normalize_palochka(word).lower().strip("*")


# av-ru-1967-review-batch-4-2026-09-17.md, item 10 "Разобрать accepted ->
# missing links приоритетным batch": the same б/6/й/ё stress-mark notation
# difference that closed 267 of check_accepted.py's accepted->missing
# findings (a bold headword printed WITH a stress mark vs. the same word
# referenced in running text WITHOUT one, or vice versa) accounts for 740
# of these 1204 draft-level unresolved candidates too — checked here as a
# second, explicit fallback (not folded into `normalize()` itself) so a
# resolution report can still distinguish "exact/palochka match" from
# "only matched after stress-mark normalization" if that's ever useful.
_STRESS_NORMALIZE = str.maketrans({"б": "о", "6": "о", "й": "и", "ё": "е"})


def stress_normalize(word: str) -> str:
    return normalize(word).translate(_STRESS_NORMALIZE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--out", default="tmp/av-ru.1967/unresolved_links.jsonl")
    args = parser.parse_args()

    articles = [json.loads(line) for line in Path(args.articles).open("r", encoding="utf-8")]
    known = {normalize(a["word"]) for a in articles}
    known_stress_norm: dict[str, list[str]] = {}
    for a in articles:
        known_stress_norm.setdefault(stress_normalize(a["word"]), []).append(a["word"])

    resolved = 0
    unresolved: list[dict[str, Any]] = []
    for article in articles:
        for sense in article.get("senses", []):
            for kind, key in (("see", "reference_targets"), ("from", "from_targets")):
                for target in sense.get(key, []):
                    if normalize(target) in known:
                        resolved += 1
                        continue
                    stress_matches = known_stress_norm.get(stress_normalize(target))
                    if stress_matches and len(stress_matches) == 1:
                        resolved += 1
                        continue
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

    baselines = load_baselines()
    ok = check_metric("resolve_references.unresolved", len(unresolved), baselines)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
