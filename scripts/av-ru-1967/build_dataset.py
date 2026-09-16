#!/usr/bin/env python3
"""Convert draft_articles.jsonl into a schema-valid av-ru.1967.jsonl.

Step 6 (schema conversion) of av-ru-1967-parsing-handoff.md's pipeline:
maps the draft, provenance-carrying article shape produced by
parse_articles.py onto schemas/av-ru.schema.json exactly — no `page`,
`raw_text`, `confidence`, `labels_raw`, `marker`, etc. survive into the
output. Fields that can't be mapped safely (unresolved forms_raw pieces,
labels without a safe normalization, low-confidence articles) are simply
omitted from the entry rather than guessed — see the handoff doc's
"критерии готовности" for what's still expected to happen before this
output can be considered final/reviewed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from parse_articles import LABEL_NORMALIZE  # noqa: E402
from segment_entries import load_known_words  # noqa: E402

ROMAN_TO_INT = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}

# 'о' misread as bold 'б' is a second OCR glyph confusion distinct from the
# already-handled digit '6' (cf. segment_entries.DIGIT_GLYPH_RE): confirmed
# by internal cross-checks such as p.464's "*сбкІкІин масд. глагола
# сокІкІинабизе." — same root, spelled with 'о' two words later in the same
# entry. Too risky to blindly substitute everywhere ('б' is a common real
# letter), so this only fires when the original word fails to resolve
# against the modern dictionary AND exactly one single-position 'б'->'о'
# substitution does resolve.
CONFUSABLE_GLYPHS = {"6": "о", "б": "о"}


def rescue_word(word: str, known_words: set[str]) -> str:
    if not word or word in known_words:
        return word
    candidates = set()
    for i, ch in enumerate(word):
        replacement = CONFUSABLE_GLYPHS.get(ch)
        if replacement:
            candidates.add(word[:i] + replacement + word[i + 1 :])
    matches = [c for c in candidates if c in known_words]
    if len(matches) == 1:
        return matches[0]
    return word

# Case-marker abbreviations that map onto a schema-named "*from" field, with
# the Russian case name used to phrase the accompanying comment (matching
# existing data/av-ru.jsonl conventions, e.g. "родительный падеж от 'X'").
CASE_FIELD = {
    "род": ("genitivefrom", "родительный падеж"),
    "дат": ("dativefrom", "дательный падеж"),
    "местн": ("locativefrom", "местный падеж"),
    "эрг": ("ergativefrom", "эргативный падеж"),
}

SENSE_KEY_ORDER = [
    "text", "precomment", "labels", "forms",
    "masdarfrom", "masdarforceto", "genitivefrom", "pluralfor", "pluralfrom",
    "forceto", "participlefrom", "deverbfrom", "locativefrom", "ergativefrom",
    "dativefrom", "ablativefrom", "casefrom", "refwordnum", "link_helper",
    "comment", "comment_lang", "examples",
]
ENTRY_KEY_ORDER = [
    "word", "stress", "homonym", "stem", "forms", "gender_forms",
    "spelling_forms", "labels", "precomment", "exclamation", "senses",
    "see_also", "pos", "form", "source",
]


def normalize_labels(labels_raw: list[str]) -> list[str]:
    out: list[str] = []
    for raw in labels_raw:
        out.extend(LABEL_NORMALIZE.get(raw.strip(",."), []))
    return out


def parse_forms_raw(forms_raw: str) -> list[str]:
    """Extract just the form values from a bracket like "род. п. алъул;
    мн. ал" — drop the case-label words (they end in '.'), keep the rest."""
    forms: list[str] = []
    for chunk in forms_raw.split(";"):
        tokens = chunk.strip().split()
        forms.extend(t for t in tokens if t and not t.endswith("."))
    return forms


def ordered(d: dict[str, Any], order: list[str]) -> dict[str, Any]:
    """Reorder to the project's documented key order, dropping anything not
    in the schema's allowed key list (defense in depth: build_entry/
    convert_sense should already only ever set schema-valid keys)."""
    return {k: d[k] for k in order if k in d}


def convert_example(example: dict[str, Any]) -> dict[str, Any] | None:
    av = (example.get("av") or "").strip()
    ru = (example.get("ru") or "").strip()
    if not av or not ru:
        return None
    return {"av": av, "ru": ru}


def convert_sense(draft_sense: dict[str, Any], article_labels_raw: list[str]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    out: dict[str, Any] = {}
    see_also: list[dict[str, str]] = []
    combined_labels_raw = article_labels_raw + draft_sense.get("labels_raw", [])

    text = draft_sense.get("text")
    if text:
        out["text"] = text

    sense_labels = normalize_labels(draft_sense.get("labels_raw", []))
    if sense_labels:
        out["labels"] = sense_labels

    masdar_targets = draft_sense.get("masdar_targets", [])
    if masdar_targets:
        target = masdar_targets[0]
        out["masdarfrom"] = target
        out["comment"] = f"масдар от '{target}'"
        for t in masdar_targets:
            see_also.append({"target": t, "kind": "from"})

    from_targets = draft_sense.get("from_targets", [])
    if from_targets:
        target = from_targets[0]
        case_key = next(
            (
                key
                for raw in combined_labels_raw
                if (key := raw.strip(",.").lower()) in CASE_FIELD
            ),
            None,
        )
        if case_key and "masdarfrom" not in out:
            field, name = CASE_FIELD[case_key]
            out[field] = target
            out.setdefault("comment", f"{name} от '{target}'")
        else:
            out.setdefault("comment", f"от '{target}'")
        for t in from_targets:
            see_also.append({"target": t, "kind": "from"})

    examples = [convert_example(e) for e in draft_sense.get("examples", [])]
    examples = [e for e in examples if e]
    if examples:
        out["examples"] = examples

    for target in draft_sense.get("reference_targets", []):
        see_also.append({"target": target, "kind": "see"})

    return out, see_also


def build_entry(article: dict[str, Any], known_words: set[str], stats: dict[str, int]) -> dict[str, Any] | None:
    word = (article.get("word") or "").strip()
    if not word:
        return None
    rescued = rescue_word(word, known_words)
    if rescued != word:
        stats["rescued"] = stats.get("rescued", 0) + 1
        word = rescued

    entry: dict[str, Any] = {"word": word}

    homonym_int = ROMAN_TO_INT.get(article.get("homonym") or "")
    if homonym_int:
        entry["homonym"] = homonym_int

    forms_raw = article.get("forms_raw")
    if forms_raw:
        values = [rescue_word(v, known_words) for v in parse_forms_raw(forms_raw)]
        if values:
            seen = {word}
            forms = [word]
            for v in values:
                if v not in seen:
                    seen.add(v)
                    forms.append(v)
            entry["forms"] = forms

    spelling_variants = article.get("spelling_variants")
    if spelling_variants and len(set(spelling_variants)) >= 2:
        entry["spelling_forms"] = spelling_variants

    article_labels_raw = article.get("labels_raw", [])
    entry_labels = normalize_labels(article_labels_raw)
    if entry_labels:
        entry["labels"] = entry_labels

    senses_out: list[dict[str, Any]] = []
    see_also_all: list[dict[str, str]] = []
    draft_senses = list(article.get("senses", []))
    if article.get("diamond_sense"):
        draft_senses.append(article["diamond_sense"])
    for draft_sense in draft_senses:
        converted, sa = convert_sense(draft_sense, article_labels_raw)
        if converted:
            senses_out.append(ordered(converted, SENSE_KEY_ORDER))
        see_also_all.extend(sa)
    if senses_out:
        entry["senses"] = senses_out

    if see_also_all:
        seen_pairs = set()
        deduped = []
        for sa in see_also_all:
            target = rescue_word(sa["target"], known_words)
            if not target or target == word:
                continue
            key = (target, sa["kind"])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            deduped.append({**sa, "target": target})
        if deduped:
            entry["see_also"] = deduped

    return ordered(entry, ENTRY_KEY_ORDER)


def strip_soft_hyphens(value: Any) -> Any:
    """Remove stray U+00AD left over where a line-wrap hyphen couldn't be
    safely rejoined (e.g. across a page boundary) — the word stays split
    into two space-separated pieces for a human to fix, but no invisible
    control character leaks into the shipped data."""
    if isinstance(value, str):
        return value.replace("\u00ad", "")
    if isinstance(value, list):
        return [strip_soft_hyphens(v) for v in value]
    if isinstance(value, dict):
        return {k: strip_soft_hyphens(v) for k, v in value.items()}
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--out", default="data/av-ru.1967.jsonl")
    parser.add_argument("--av-ru", default="data/av-ru.jsonl")
    args = parser.parse_args()

    known_words = load_known_words(Path(args.av_ru))
    stats: dict[str, int] = {}
    count = 0
    seen_lines: set[str] = set()
    with Path(args.articles).open("r", encoding="utf-8") as fh, Path(args.out).open(
        "w", encoding="utf-8"
    ) as out_fh:
        for line in fh:
            article = json.loads(line)
            entry = build_entry(article, known_words, stats)
            if entry is None:
                continue
            entry = strip_soft_hyphens(entry)
            serialized = json.dumps(entry, ensure_ascii=False)
            if serialized in seen_lines:
                # Byte-identical entries are always segmentation noise
                # (e.g. a stray bold word repeatedly misread as a bare
                # headword stub) — dropping the repeat loses nothing, since
                # keeping N copies of the exact same object is never
                # meaningful for a dictionary.
                continue
            seen_lines.add(serialized)
            out_fh.write(serialized + "\n")
            count += 1
    print(f"wrote {count} entries to {args.out}")
    if stats.get("rescued"):
        print(f"rescued {stats['rescued']} word(s) via known-word б/6->о correction")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

