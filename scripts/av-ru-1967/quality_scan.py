#!/usr/bin/env python3
"""Structural quality scan of data/av-ru.1967.jsonl, independent of the
alphabetical-order/see_also heuristics already used (check_order.py,
resolve_references.py). Looks for internal inconsistencies that don't
require book-wide context:

- `word` matching a Russian-only grammatical ending (infinitive/adjective)
  — candidate for the "isolated bold Russian word became the headword" bug
  found earlier via the order-check, but scanned over the WHOLE dataset
  instead of only the pairs that happened to violate alphabetical order.
- `examples[].ru` containing an Avar-specific digraph/palochka — the av/ru
  split inside a sense went wrong (Avar text leaked into the Russian side).
- `examples[].av` containing common Russian function words and no Avar
  digraph/palochka at all — the reverse leak (Russian text tagged as `av`).
- outlier-length `word` (much longer than typical) — candidate for two
  articles merged into one headword string.

Purely diagnostic: writes tmp/av-ru.1967/quality_scan.jsonl, never edits
data/av-ru.1967.jsonl.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path
from typing import Any

RUSSIAN_GRAMMAR_RE = re.compile(
    r"(ться|ть|ий|ая|ое|ые|ение|ание|ность)$"
)
AVAR_DIGRAPHS = ("гъ", "гь", "гӏ", "къ", "кь", "кӏ", "лъ", "тӏ", "хъ", "хь", "хӏ", "цӏ", "чӏ")
PALOCHKA = ("\u04c0", "\u04cf")
RUSSIAN_FUNCTION_WORDS = {
    "и", "но", "а", "или", "что", "как", "не", "это", "который", "она", "он",
    "они", "все", "уже", "если", "когда", "чтобы", "его", "ее", "их", "то",
}


def has_avar_signal(text: str) -> bool:
    lowered = text.lower()
    return any(d in lowered for d in AVAR_DIGRAPHS) or any(p in text for p in PALOCHKA)


def looks_russian_only(text: str) -> bool:
    words = re.findall(r"[а-яё]+", text.lower())
    if not words:
        return False
    hits = sum(1 for w in words if w in RUSSIAN_FUNCTION_WORDS)
    return hits >= 1 and not has_avar_signal(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="data/av-ru.1967.jsonl")
    parser.add_argument("--out", default="tmp/av-ru.1967/quality_scan.jsonl")
    args = parser.parse_args()

    entries = [json.loads(line) for line in Path(args.source).open("r", encoding="utf-8")]
    lengths = [len(e["word"]) for e in entries]
    mean_len = statistics.mean(lengths)
    stdev_len = statistics.pstdev(lengths)
    length_cutoff = mean_len + 4 * stdev_len

    findings: list[dict[str, Any]] = []

    for e in entries:
        word = e["word"]

        if RUSSIAN_GRAMMAR_RE.search(word) and not has_avar_signal(word):
            findings.append({"kind": "russian-word-as-headword", "word": word})

        if len(word) > length_cutoff:
            findings.append({"kind": "outlier-length-word", "word": word, "length": len(word)})

        for sense in e.get("senses", []):
            for ex in sense.get("examples", []):
                av, ru = ex.get("av", ""), ex.get("ru", "")
                if has_avar_signal(ru):
                    findings.append(
                        {"kind": "avar-leaked-into-ru", "word": word, "av": av, "ru": ru}
                    )
                if looks_russian_only(av):
                    findings.append(
                        {"kind": "russian-leaked-into-av", "word": word, "av": av, "ru": ru}
                    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for f in findings:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")

    by_kind: dict[str, int] = {}
    for f in findings:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    print(f"{len(entries)} entries scanned, {len(findings)} findings")
    for kind, count in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        print(f"  {kind}: {count}")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
