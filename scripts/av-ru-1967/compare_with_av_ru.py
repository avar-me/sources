#!/usr/bin/env python3
"""Diagnostic comparison of data/av-ru.1967.jsonl against data/av-ru.jsonl.

Step 5/9 of av-ru-1967-parsing-handoff.md ("Сравнение с основным av-ru"):
purely diagnostic, never used to overwrite 1967 content with the modern
dictionary's wording. Produces:

- words only in av-ru.1967 (not in the modern dictionary at all — some are
  real 1967-only vocabulary, some are still-uncaught OCR garbage);
- words only in the modern av-ru (expected, different edition, not a bug);
- fuzzy-match candidates for the "only in 1967" words (small edit distance
  to a real modern word) — the doc's "потенциальные OCR-кандидаты с малым
  расстоянием редактирования", a lead for further OCR correction work, NOT
  an instruction to silently rewrite anything;
- matched words with a very different sense count, as a rough diagnostic
  signal (different editions legitimately differ, so this is informative
  only, not an error list).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rapidfuzz import process, fuzz


def load_words(path: Path) -> dict[str, list[dict[str, Any]]]:
    by_word: dict[str, list[dict[str, Any]]] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            by_word.setdefault(entry["word"], []).append(entry)
    return by_word


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-1967", default="data/av-ru.1967.jsonl")
    parser.add_argument("--source-main", default="data/av-ru.jsonl")
    parser.add_argument("--out-dir", default="tmp/av-ru.1967/compare")
    parser.add_argument(
        "--max-edit-distance",
        type=int,
        default=2,
        help="only report a fuzzy candidate within this edit distance",
    )
    args = parser.parse_args()

    words_1967 = load_words(Path(args.source_1967))
    words_main = load_words(Path(args.source_main))

    only_1967 = sorted(set(words_1967) - set(words_main))
    only_main = sorted(set(words_main) - set(words_1967))
    common = sorted(set(words_1967) & set(words_main))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "only_1967.txt").write_text("\n".join(only_1967), encoding="utf-8")
    (out_dir / "only_main.txt").write_text("\n".join(only_main), encoding="utf-8")

    print(f"1967: {len(words_1967)} distinct words, main: {len(words_main)} distinct words")
    print(f"common: {len(common)}, only in 1967: {len(only_1967)}, only in main: {len(only_main)}")

    # Fuzzy-match "only in 1967" words against the main word list.
    main_word_list = list(words_main.keys())
    candidates = []
    for word in only_1967:
        match = process.extractOne(word, main_word_list, scorer=fuzz.ratio)
        if match is None:
            continue
        best_word, score, _ = match
        # ratio-based distance approximation: convert score back to an edit-
        # distance-like cutoff via length; keep only close, short-distance hits.
        max_len = max(len(word), len(best_word))
        approx_distance = round((1 - score / 100) * max_len)
        if approx_distance <= args.max_edit_distance and best_word != word:
            candidates.append((word, best_word, approx_distance))

    candidates.sort(key=lambda c: c[2])
    with (out_dir / "ocr_candidates.jsonl").open("w", encoding="utf-8") as fh:
        for word, best_word, dist in candidates:
            fh.write(
                json.dumps(
                    {"word_1967": word, "closest_main_word": best_word, "approx_distance": dist},
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"OCR-candidate near-misses (<= {args.max_edit_distance}): {len(candidates)}")

    # Matched words with very different sense counts (diagnostic only).
    sense_diff = []
    for word in common:
        n1967 = len(words_1967[word][0].get("senses", []))
        nmain = len(words_main[word][0].get("senses", []))
        if abs(n1967 - nmain) >= 3:
            sense_diff.append((word, n1967, nmain))
    with (out_dir / "sense_count_diff.jsonl").open("w", encoding="utf-8") as fh:
        for word, n1967, nmain in sense_diff:
            fh.write(
                json.dumps({"word": word, "senses_1967": n1967, "senses_main": nmain}, ensure_ascii=False)
                + "\n"
            )
    print(f"matched words with sense-count difference >= 3: {len(sense_diff)}")
    print(f"reports written to {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
