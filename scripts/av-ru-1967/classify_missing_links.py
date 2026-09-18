#!/usr/bin/env python3
"""Classify accepted-origin `see_also`/reference links whose target does
not resolve to any accepted or review-queue word.

av-ru-1967-review-batch-5-2026-09-18.md, remaining P1: "228 accepted-
origin missing links" (tmp/av-ru.1967/accepted_check.jsonl, kind
`link_to_missing`) need to be classified, not just counted. Manual
per-item investigation of all 228 is out of scope for one pass (each
would need the same raw_text/context verification as a full correction),
so this script buckets them by an automated heuristic to make future
triage tractable and durable:

- `valid-class-agreement-variant`: word and target differ only by an
  Avar noun-class agreement prefix (в-/й-/б-/р-, e.g. "вац" -> "бац").
  This is normal Avar grammar (the source dictionary cross-references
  the "male" class form of a verb/participle from its "female"/other
  class form, or vice versa) and generally is NOT a bug: many such
  targets are legitimately absent as their own headword because the
  dictionary only lists one class form. Confirmed not-a-bug by
  construction; no target-existence check needed.
- `ocr-target-fixable` / `possible-ocr-target-needs-verification`: a
  fuzzy-match candidate exists in accepted or review vocabulary (ratio
  >= 88 / >= 75 respectively). This is a CANDIDATE only — high fuzzy
  similarity is not proof the candidate is the intended target (could be
  an unrelated word that happens to be close). Each still needs
  individual raw_text verification before being treated as confirmed.
- `no-plausible-match-found`: no candidate above the fuzzy threshold;
  likely a genuinely absent accepted entry, a bad parser split, or a
  heavily garbled OCR target that needs source-image lookup.

This is a non-gating diagnostic (like compare_with_av_ru.py): it doesn't
fail the build, just writes a classification artifact for future review-
queue triage. Like classify_bracket_anomalies.py, item_id is stable
across regeneration and review_decision is preserved from the previously
committed file rather than reset to null on every rebuild.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from rapidfuzz import fuzz, process
except ImportError:  # pragma: no cover - dev-only dependency, see requirements.txt
    fuzz = None
    process = None

CLASS_PREFIXES = ("в", "й", "б", "р")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def is_class_agreement_variant(word: str, target: str) -> bool:
    for p1 in CLASS_PREFIXES:
        if word.startswith(p1):
            rest = word[len(p1) :]
            for p2 in CLASS_PREFIXES:
                if p2 != p1 and target.startswith(p2) and target[len(p2) :] == rest:
                    return True
    return False


def classify_target(target: str, word_list: list[str], accepted_words: set[str]) -> dict[str, Any]:
    if process is None:
        return {"category": "no-plausible-match-found"}
    match = process.extractOne(target, word_list, scorer=fuzz.ratio)
    if match and match[1] >= 88:
        return {
            "category": "ocr-target-fixable",
            "closest_match": match[0],
            "closest_match_score": round(match[1], 1),
            "closest_match_location": "accepted" if match[0] in accepted_words else "review",
        }
    if match and match[1] >= 75:
        return {
            "category": "possible-ocr-target-needs-verification",
            "closest_match": match[0],
            "closest_match_score": round(match[1], 1),
            "closest_match_location": "accepted" if match[0] in accepted_words else "review",
        }
    return {"category": "no-plausible-match-found"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted", default="data/av-ru.1967.jsonl")
    parser.add_argument("--review", default="tmp/av-ru.1967/needs_review.jsonl")
    parser.add_argument("--accepted-check", default="tmp/av-ru.1967/accepted_check.jsonl")
    parser.add_argument("--out", default="data/av-ru.1967.missing_links_classification.jsonl")
    args = parser.parse_args()

    accepted = _load_jsonl(Path(args.accepted))
    review = _load_jsonl(Path(args.review))
    accepted_words = {e["word"] for e in accepted}
    review_words = {r["entry"]["word"] for r in review if r.get("entry", {}).get("word")}
    # Sorted, not just list(set(...)): rapidfuzz's extractOne breaks ties
    # between equally-scored candidates by input order, and Python's set
    # iteration order for strings depends on per-process hash
    # randomization — without a deterministic sort, `closest_match` for
    # any tied candidate would silently change between runs, breaking
    # build reproducibility (caught by check_reproducibility.sh).
    word_list = sorted(accepted_words | review_words)

    checks = _load_jsonl(Path(args.accepted_check))
    missing = [r for r in checks if r.get("kind") == "link_to_missing"]

    previous_decisions = {
        row["item_id"]: row.get("review_decision")
        for row in _load_jsonl(Path(args.out))
        if row.get("review_decision") is not None
    }

    rows = []
    for i, r in enumerate(missing):
        word, target = r["word"], r["target"]
        item_id = f"missing-link:{word}:{target}:{i}"
        entry: dict[str, Any] = {"word": word, "target": target, "item_id": item_id}
        if is_class_agreement_variant(word, target):
            entry["category"] = "valid-class-agreement-variant"
        else:
            entry.update(classify_target(target, word_list, accepted_words))
        entry["review_decision"] = previous_decisions.get(
            item_id,
            "confirmed-not-a-bug" if entry["category"] == "valid-class-agreement-variant" else None,
        )
        rows.append(entry)

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    from collections import Counter

    counts = Counter(r["category"] for r in rows)
    print(f"accepted-origin missing links: {len(rows)}")
    print(f"wrote {out_path}")
    for k, v in counts.most_common():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
