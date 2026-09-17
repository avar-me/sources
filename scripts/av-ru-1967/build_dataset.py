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
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from parse_articles import LABEL_NORMALIZE  # noqa: E402
from segment_entries import load_known_words  # noqa: E402

ROMAN_TO_INT = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}

# handoff doc: "||" spelling variants ("авадан||аваданго") are sometimes OCR'd
# with ц/Ц instead of "||" (е.г. "аваданцаваданго" for exactly that doc example).
# segment_entries.SPELLING_VARIANT_RE only catches the literal "||" form, so
# this survives as one bogus merged headword. Only split when the second
# half starts with the first (the doc's own examples are all "X" + "X" or
# "X" + "X"+suffix) — confirmed against 29 real cases in the corpus, all
# looking like genuine phonetic/orthographic variant pairs, not coincidence.
PIPE_CORRUPTION_RE = re.compile(r"^([а-яёӏ]{3,})[цЦ]([а-яёӏ]+)$")


def split_pipe_corruption(word: str) -> tuple[str, list[str] | None]:
    match = PIPE_CORRUPTION_RE.match(word)
    if match:
        first, second = match.group(1), match.group(2)
        if second.startswith(first):
            return first, [first, second]
    return word, None


# 'о' misread as bold 'б' (and digit '6', cf. segment_entries.DIGIT_GLYPH_RE)
# turned out to be the same underlying phenomenon as the printed stress
# accent over a headword's stressed vowel (see av-ru-1967-parsing-handoff.md,
# "Ударение"): the accented glyph gets exported as a visually-similar but
# wrong letter — о́->б, и́->й, е́->ё — confirmed e.g. by p.262's "кирй [род.
# п. кирйдул]" resolving only once "й" is read back as the stressed "и"
# ("кири", matching data/av-ru.jsonl's "кисан", stress: 4 for the same
# family). Too risky to blindly substitute everywhere (б, й, ё are all
# common real letters too), so this only fires when the original word fails
# to resolve against the modern dictionary AND exactly one single-position
# substitution does resolve. The resolved position becomes the entry's
# `stress` (1-based, matches schema) since all four substitutions are for
# stressed vowels.
STRESS_GLYPHS = {"6": "о", "б": "о", "й": "и", "ё": "е"}


def rescue_word(word: str, known_words: set[str]) -> tuple[str, int | None]:
    if not word or word in known_words:
        return word, None
    candidates: dict[str, int] = {}
    for i, ch in enumerate(word):
        replacement = STRESS_GLYPHS.get(ch)
        if replacement:
            candidates[word[:i] + replacement + word[i + 1 :]] = i + 1
    matches = [c for c in candidates if c in known_words]
    if len(matches) == 1:
        return matches[0], candidates[matches[0]]
    return word, None

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


AVAR_DIGRAPHS = ("гъ", "гь", "гӏ", "къ", "кь", "кӏ", "лъ", "тӏ", "хъ", "хь", "хӏ", "цӏ", "чӏ")


def has_avar_signal(text: str) -> bool:
    lowered = text.lower()
    return any(d in lowered for d in AVAR_DIGRAPHS) or "ӏ" in text


def convert_example(example: dict[str, Any]) -> dict[str, Any] | None:
    av = (example.get("av") or "").strip()
    ru = (example.get("ru") or "").strip()
    if not av or not ru:
        return None
    if has_avar_signal(ru) and not has_avar_signal(av):
        # The av/ru split is almost certainly wrong here (Avar-looking text
        # ended up on the Russian side) — likely stray column/line
        # reconstruction noise on a handful of scattered pages, found via
        # quality_scan.py. Can't safely tell which way to swap it, so drop
        # rather than ship a known-wrong pair.
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
    word, pipe_spelling_forms = split_pipe_corruption(word)
    if pipe_spelling_forms:
        stats["pipe_corruption_split"] = stats.get("pipe_corruption_split", 0) + 1
    rescued, stress_pos = rescue_word(word, known_words)
    if rescued != word:
        stats["rescued"] = stats.get("rescued", 0) + 1
        word = rescued
    if stress_pos:
        stats["stress_recorded"] = stats.get("stress_recorded", 0) + 1

    entry: dict[str, Any] = {"word": word}
    if stress_pos:
        entry["stress"] = stress_pos

    homonym_int = ROMAN_TO_INT.get(article.get("homonym") or "")
    if homonym_int:
        entry["homonym"] = homonym_int

    forms_raw = article.get("forms_raw")
    if forms_raw:
        values = [rescue_word(v, known_words)[0] for v in parse_forms_raw(forms_raw)]
        if values:
            seen = {word}
            forms = [word]
            for v in values:
                if v not in seen:
                    seen.add(v)
                    forms.append(v)
            entry["forms"] = forms

    spelling_variants = article.get("spelling_variants") or pipe_spelling_forms
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
            target = rescue_word(sa["target"], known_words)[0]
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
    parser.add_argument("--needs-review", default="tmp/av-ru.1967/needs_review.jsonl")
    parser.add_argument("--av-ru", default="data/av-ru.jsonl")
    args = parser.parse_args()

    known_words = load_known_words(Path(args.av_ru))
    stats: dict[str, int] = {}
    # av-ru-1967-review-batch-2-2026-09-17.md, "P0. Исправить дедупликацию
    # до confidence-гейта": the old single-pass loop added every serialized
    # entry to one global `seen_lines` set BEFORE splitting by confidence —
    # if a low/medium duplicate of some entry happened to appear earlier in
    # the file than an identical high-confidence one, the high copy was
    # silently dropped entirely (never published, never queued for
    # review). Two-pass fix: first collect every (confidence, entry)
    # candidate per unique serialized entry, then keep only the
    # highest-confidence representative of each duplicate group.
    CONF_RANK = {"high": 2, "medium": 1, "low": 0}
    candidates: dict[str, tuple[int, dict[str, Any], dict[str, Any]]] = {}
    with Path(args.articles).open("r", encoding="utf-8") as fh:
        for line in fh:
            article = json.loads(line)
            entry = build_entry(article, known_words, stats)
            if entry is None:
                continue
            entry = strip_soft_hyphens(entry)
            serialized = json.dumps(entry, ensure_ascii=False)
            rank = CONF_RANK.get(article.get("confidence"), -1)
            existing = candidates.get(serialized)
            if existing is None or rank > existing[0]:
                candidates[serialized] = (rank, article, entry)

    entries: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    for _rank, article, entry in candidates.values():
        # av-ru-1967-review-2026-09-17.md, "P0. Low-confidence статьи
        # попадают в основной JSONL": the docstring above claimed
        # low-confidence articles were excluded, but build_entry() never
        # actually checked `confidence` — every article, regardless of
        # segmentation confidence, ended up in the published file. Only
        # `high` (a real bold headword match, or the equally strict
        # spelling-variant-pipe case) goes to data/av-ru.1967.jsonl;
        # `medium`/`low` go to a separate review queue instead, tagged
        # with the reason so a human can triage without re-deriving it.
        if article.get("confidence") == "high":
            entries.append(entry)
        else:
            needs_review.append(
                {
                    "page": article.get("page"),
                    "confidence": article.get("confidence"),
                    "word_raw": article.get("word_raw"),
                    "raw_text": article.get("raw_text"),
                    "entry": entry,
                }
            )

    # A bare {"word": X} stub next to another entry with the same word that
    # DOES have content is always redundant segmentation noise (a stray
    # token that produced no body before the next real headword) — drop it,
    # never the other way around, and never touch a bare stub that has no
    # such sibling (that might be a legitimate reference-only article).
    words_with_content = {
        e["word"] for e in entries if set(e.keys()) != {"word"}
    }
    filtered = [
        e for e in entries if not (set(e.keys()) == {"word"} and e["word"] in words_with_content)
    ]
    stats["dropped_bare_duplicates"] = len(entries) - len(filtered)

    with Path(args.out).open("w", encoding="utf-8") as out_fh:
        for entry in filtered:
            out_fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    review_path = Path(args.needs_review)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    with review_path.open("w", encoding="utf-8") as review_fh:
        for row in needs_review:
            review_fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"wrote {len(filtered)} entries to {args.out}")
    print(f"wrote {len(needs_review)} medium/low-confidence entries to {review_path} (not published)")
    if stats.get("rescued"):
        print(f"rescued {stats['rescued']} word(s) via known-word б/6/й/ё stress-glyph correction")
    if stats.get("stress_recorded"):
        print(f"recorded stress position for {stats['stress_recorded']} of those word(s)")
    if stats.get("pipe_corruption_split"):
        print(f"split {stats['pipe_corruption_split']} ц/Ц-as-'||' word(s) into spelling_forms")
    if stats.get("dropped_bare_duplicates"):
        print(f"dropped {stats['dropped_bare_duplicates']} bare-stub duplicate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

