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
from quality_scan import RUSSIAN_GRAMMAR_RE, looks_russian_only  # noqa: E402
from segment_entries import load_known_words  # noqa: E402
from geometry_lookup import bbox_for  # noqa: E402

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


# av-ru-1967-review-batch-2-2026-09-17.md, "P1. Довести forms до
# семантически корректной структуры": the printed `[forms_raw]` bracket
# mixes real inflected-form values with case/mood/declension-class
# grammar labels ("род. п.", "повел.", "1-го скл.", "2-го скл.", "мн.") and
# stray separator punctuation (typist commas between clauses). Neither
# belongs in forms[] — only the actual form values should survive.
FORM_GRAMMAR_MARKERS = {
    # case names (падеж)
    "род", "дат", "местн", "эрг",
    # generic grammar words that appear standalone in forms_raw brackets
    "п", "скл", "мн", "ед", "повел",
}
# "1-го скл.", "2-го скл." (declension class), OCR'd with a '-' or '~'
# between the digit and "го"/"й" (e.g. "2~го" for "2-го").
_ORDINAL_MARKER_RE = re.compile(r"^\d+[-~]?(го|й)$")
# Punctuation/marker characters a cleaned form value should never start or
# end with — plain separator noise from the printed bracket, not part of
# the word itself.
_FORM_STRIP_CHARS = ".,;:^_*[]{}\\~"


def _is_form_grammar_marker(bare: str) -> bool:
    if not bare or bare.isdigit():
        return True
    if _ORDINAL_MARKER_RE.match(bare):
        return True
    return bare.lower() in FORM_GRAMMAR_MARKERS


def parse_forms_raw(forms_raw: str, known_words: set[str] | None = None) -> list[str]:
    """Extract just the form values from a bracket like "род. п. 1-го скл.
    авторасул, 2-го скл. авторалъул" or "повел, бабаде" — drop case/mood/
    declension-class grammar markers and any leftover separator
    punctuation, keeping only the printed inflected-form values (multiple
    explicitly printed forms, e.g. per declension class, are kept as
    separate list entries)."""
    known_words = known_words or set()
    forms: list[str] = []
    for raw_token in forms_raw.replace(",", " ").split():
        bare = raw_token.strip(_FORM_STRIP_CHARS)
        if _is_form_grammar_marker(bare):
            continue
        if any(ch.isdigit() for ch in bare):
            # A real Avar form with a stray OCR digit glued on (e.g. a
            # misread superscript reference), not a case/declension marker
            # itself (those are filtered above) — strip the digit(s) rather
            # than dropping the whole value.
            bare = "".join(ch for ch in bare if not ch.isdigit())
        if not bare:
            continue
        if looks_russian_only(bare, known_words) and not has_avar_signal(bare):
            # Plain Russian text leaking into the forms bracket (not an
            # Avar inflected form at all) — never belongs in forms[].
            continue
        forms.append(bare)
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


# av-ru-1967-review-batch-2-2026-09-17.md, "P0. Пересмотреть смысл
# confidence: high": bold detection alone (segment_entries' `confidence`,
# aka boundary confidence) doesn't prove the article's CONTENT parsed
# cleanly — a bogus headword or a merged/garbled article can still have
# high boundary confidence. These are the raw structural OCR-noise
# characters the review explicitly named (found live in accepted entries:
# "*рёт!и", "1и_[ро(3.", "гЫкълу", "бородавкӏ^") — any of them surviving
# into a final entry means something upstream didn't parse cleanly, so the
# entry needs a human look rather than automatic publication.
RAW_MARKER_CHARS = ("*", "[", "]", "^", "_", "{", "}", "\\")


def _strings_in(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            out.extend(_strings_in(v))
        return out
    if isinstance(value, dict):
        out = []
        for v in value.values():
            out.extend(_strings_in(v))
        return out
    return []


# av-ru-1967-review-batch-2-2026-09-17.md, "P1. Довести forms до
# семантически корректной структуры", requirement 4 ("проверять аварский
# допустимый алфавит формы"): a mid-word uppercase letter in a cleaned
# forms[] value is essentially never a real spelling (this book's headwords
# and forms are lowercase) — it's almost always a mis-OCR'd separator, e.g.
# "дурцалЦдурцаби" for "дурцал; дурцаби" or "мухьлулН" for a garbled case
# ending. parse_forms_raw() only strips grammar markers/punctuation at
# token *boundaries*, so this kind of mid-token corruption needs its own
# check rather than silently publishing a malformed form value.
_VALID_FORM_RE = re.compile(r"[а-яёӏ]+(-[а-яёӏ]+)*")


def _looks_like_valid_form(value: str) -> bool:
    return bool(_VALID_FORM_RE.fullmatch(value))


def detect_parse_issues(entry: dict[str, Any], known_words: set[str]) -> list[str]:
    """Content-level defects that boundary confidence alone can't see —
    returns an empty list for a clean entry. Non-empty means `parse_confidence`
    is "low" (see main()). Reuses quality_scan.py's own leak-detection
    heuristics so "accepted" and "0 quality_scan findings" mean the same
    thing (av-ru-1967-review-batch-2-2026-09-17.md criterion #9), instead of
    maintaining a second, driftable copy of the same checks."""
    issues: list[str] = []
    for s in _strings_in(entry):
        for ch in RAW_MARKER_CHARS:
            if ch in s:
                issues.append(f"raw-marker:{ch}")
    if RUSSIAN_GRAMMAR_RE.search(entry.get("word", "")) and not has_avar_signal(entry.get("word", "")) and entry["word"] not in known_words:
        issues.append("russian-word-as-headword")
    for f in entry.get("forms", []):
        if not _looks_like_valid_form(f):
            issues.append("malformed-form-value")
    for sense in entry.get("senses", []):
        for ex in sense.get("examples", []):
            av, ru = ex.get("av", ""), ex.get("ru", "")
            if has_avar_signal(ru):
                issues.append("avar-leaked-into-ru")
            if looks_russian_only(av, known_words):
                issues.append("russian-leaked-into-av")
    return sorted(set(issues))


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
        values = [rescue_word(v, known_words)[0] for v in parse_forms_raw(forms_raw, known_words)]
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
    parser.add_argument("--provenance", default="data/av-ru.1967.provenance.jsonl")
    parser.add_argument("--draft-outcomes", default="tmp/av-ru.1967/draft_outcomes.jsonl")
    parser.add_argument("--geometry-dir", default="tmp/av-ru.1967/geometry")
    parser.add_argument("--av-ru", default="data/av-ru.jsonl")
    args = parser.parse_args()

    known_words = load_known_words(Path(args.av_ru))
    geometry_dir = Path(args.geometry_dir)
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
    #
    # av-ru-1967-review-batch-3-2026-09-17.md, "P1. Сохранить полную
    # provenance duplicate groups": collect EVERY candidate per group (not
    # just the eventual winner) so data/av-ru.1967.provenance.jsonl can
    # record where every merged duplicate came from, not only the one that
    # got published.
    CONF_RANK = {"high": 2, "medium": 1, "low": 0}
    with Path(args.articles).open("r", encoding="utf-8") as fh:
        articles = [json.loads(line) for line in fh]

    # av-ru-1967-review-batch-4-2026-09-17.md, "1. Ввести per-candidate
    # outcome ledger": every draft article (indexed by its position in
    # draft_articles.jsonl) must end up with exactly one outcome —
    # "accepted", "review", "dropped-empty-word" (build_entry found no
    # usable word), "duplicate-of:<winning draft_index>", or
    # "dropped-bare-stub-duplicate" — so accounting never loses articles
    # to an implicit count-difference.
    outcomes: list[str | None] = [None] * len(articles)

    candidates: dict[str, list[tuple[int, int, dict[str, Any], dict[str, Any]]]] = {}
    for i, article in enumerate(articles):
        entry = build_entry(article, known_words, stats)
        if entry is None:
            outcomes[i] = "dropped-empty-word"
            continue
        entry = strip_soft_hyphens(entry)
        serialized = json.dumps(entry, ensure_ascii=False)
        rank = CONF_RANK.get(article.get("confidence"), -1)
        # av-ru-1967-review-batch-2-2026-09-17.md, "P0. Не терять
        # provenance в review queue": book-neighbor headwords (the
        # articles immediately before/after in reading order) let a
        # reviewer place a needs_review candidate without reopening the
        # PDF — cheap to attach here since draft_articles.jsonl is already
        # in book reading order.
        neighbors = {
            "prev_word": articles[i - 1]["word"] if i > 0 else None,
            "next_word": articles[i + 1]["word"] if i + 1 < len(articles) else None,
        }
        candidates.setdefault(serialized, []).append((rank, i, {**article, **neighbors}, entry))

    entries: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    entries_draft_index: list[int] = []
    for members in candidates.values():
        # First member with the highest rank wins — same tie-break as the
        # old `rank > existing[0]` single-pass comparison (first-seen among
        # equal ranks), just computed over the full group instead of
        # incrementally.
        best_rank = max(m[0] for m in members)
        winner = next(m for m in members if m[0] == best_rank)
        _rank, winner_index, article, entry = winner
        for m in members:
            if m is not winner:
                outcomes[m[1]] = f"duplicate-of:{winner_index}"
        # av-ru-1967-review-2026-09-17.md, "P0. Low-confidence статьи
        # попадают в основной JSONL": the docstring above claimed
        # low-confidence articles were excluded, but build_entry() never
        # actually checked `confidence` — every article, regardless of
        # segmentation confidence, ended up in the published file. Only
        # `high` (a real bold headword match, or the equally strict
        # spelling-variant-pipe case) goes to data/av-ru.1967.jsonl;
        # `medium`/`low` go to a separate review queue instead, tagged
        # with the reason so a human can triage without re-deriving it.
        #
        # av-ru-1967-review-batch-2-2026-09-17.md, "P0. Пересмотреть смысл
        # confidence: high": boundary confidence (bold detection) alone
        # doesn't prove the CONTENT parsed cleanly. A `high` article whose
        # final entry still contains a raw structural marker (leftover "*",
        # unmatched "[al ]", "^", "_", etc.) or av/ru cross-contamination
        # gets demoted to the review queue instead of published, with the
        # concrete `parse_issues` list attached so a reviewer doesn't have
        # to re-derive why it was flagged.
        parse_issues = detect_parse_issues(entry, known_words)
        if article.get("confidence") == "high" and not parse_issues:
            entries.append(entry)
            entries_draft_index.append(winner_index)
            outcomes[winner_index] = "accepted"
            # av-ru-1967-review-batch-3-2026-09-17.md, "P0. Реализовать
            # независимые gates для accepted/review/draft" (accepted
            # entries without source provenance: 0) + "P1. Сохранить
            # полную provenance duplicate groups": one committed row per
            # accepted entry, in the same order as data/av-ru.1967.jsonl,
            # recording where it came from, the rule that picked it among
            # its duplicate-group siblings, and every OTHER candidate that
            # was merged into it (not just the winner) — including whether
            # those candidates actually came from different source spans
            # (different page/column/raw_text) despite producing an
            # identical final entry, which the review specifically asked
            # to surface rather than silently discard.
            other_members = [m for m in members if m is not winner]
            spans_differ = any(
                (m[2].get("page"), m[2].get("column"), m[2].get("raw_text"))
                != (article.get("page"), article.get("column"), article.get("raw_text"))
                for m in other_members
            )
            prov_row = {
                "word": entry.get("word"),
                "page": article.get("page"),
                "column": article.get("column"),
                "top": article.get("top"),
                "confidence": article.get("confidence"),
                "reasons": article.get("reasons", []),
                "raw_text_length": len(article.get("raw_text") or ""),
                "bbox": bbox_for(geometry_dir, article.get("page"), article.get("column"), article.get("top")),
                "selection_rule": "highest-confidence-first-seen" if other_members else "unique",
                "duplicate_group_spans_differ": spans_differ,
                "duplicate_group": [
                    {
                        "page": m[2].get("page"),
                        "column": m[2].get("column"),
                        "top": m[2].get("top"),
                        "confidence": m[2].get("confidence"),
                        "reasons": m[2].get("reasons", []),
                        "raw_text_preview": (m[2].get("raw_text") or "")[:100],
                        "bbox": bbox_for(geometry_dir, m[2].get("page"), m[2].get("column"), m[2].get("top")),
                    }
                    for m in other_members
                ],
            }
            # batch-4 item 7: a carry-stitched article's tokens can
            # originate from more than one physical page (e.g. a whole
            # zero-candidate intervening page fully absorbed) —
            # parse_articles.py only sets source_pages when it's more
            # than just article["page"], so keep it sparse here too.
            if article.get("source_pages"):
                prov_row["source_pages"] = article["source_pages"]
            provenance.append(prov_row)
        else:
            outcomes[winner_index] = "review"
            review_row = {
                "page": article.get("page"),
                "column": article.get("column"),
                "top": article.get("top"),
                "confidence": article.get("confidence"),
                "reasons": article.get("reasons", []),
                "parse_issues": parse_issues,
                "prev_word": article.get("prev_word"),
                "next_word": article.get("next_word"),
                "continues_next_page": article.get("continues_next_page", False),
                "word_raw": article.get("word_raw"),
                "raw_text": article.get("raw_text"),
                "bbox": bbox_for(geometry_dir, article.get("page"), article.get("column"), article.get("top")),
                "entry": entry,
            }
            if article.get("source_pages"):
                review_row["source_pages"] = article["source_pages"]
            needs_review.append(review_row)

    # A bare {"word": X} stub next to another entry with the same word that
    # DOES have content is always redundant segmentation noise (a stray
    # token that produced no body before the next real headword) — drop it,
    # never the other way around, and never touch a bare stub that has no
    # such sibling (that might be a legitimate reference-only article).
    words_with_content = {
        e["word"] for e in entries if set(e.keys()) != {"word"}
    }
    keep = [
        not (set(e.keys()) == {"word"} and e["word"] in words_with_content) for e in entries
    ]
    filtered = [e for e, k in zip(entries, keep) if k]
    filtered_provenance = [p for p, k in zip(provenance, keep) if k]
    for draft_index, k in zip(entries_draft_index, keep):
        if not k:
            outcomes[draft_index] = "dropped-bare-stub-duplicate"
    stats["dropped_bare_duplicates"] = len(entries) - len(filtered)

    with Path(args.out).open("w", encoding="utf-8") as out_fh:
        for entry in filtered:
            out_fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    provenance_path = Path(args.provenance)
    with provenance_path.open("w", encoding="utf-8") as prov_fh:
        for row in filtered_provenance:
            prov_fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    review_path = Path(args.needs_review)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    with review_path.open("w", encoding="utf-8") as review_fh:
        for row in needs_review:
            review_fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    # av-ru-1967-review-batch-4-2026-09-17.md, "1. Ввести per-candidate
    # outcome ledger": every draft article must have exactly one outcome by
    # this point — the page ledger consumes this instead of a naive
    # segment-vs-draft count difference.
    outcomes_path = Path(args.draft_outcomes)
    unaccounted = 0
    with outcomes_path.open("w", encoding="utf-8") as outc_fh:
        for i, article in enumerate(articles):
            outcome = outcomes[i]
            if outcome is None:
                unaccounted += 1
                outcome = "UNACCOUNTED"
            outc_fh.write(
                json.dumps(
                    {
                        "draft_index": i,
                        "page": article.get("page"),
                        "column": article.get("column"),
                        "top": article.get("top"),
                        "word": article.get("word"),
                        "outcome": outcome,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"wrote {len(articles)} draft outcomes to {outcomes_path} ({unaccounted} unaccounted)")

    print(f"wrote {len(filtered)} entries to {args.out}")
    print(f"wrote {len(filtered_provenance)} provenance rows to {provenance_path}")
    print(f"wrote {len(needs_review)} medium/low-confidence entries to {review_path} (not published)")
    demoted_by_issues = sum(1 for r in needs_review if r.get("confidence") == "high" and r.get("parse_issues"))
    if demoted_by_issues:
        print(f"of those, {demoted_by_issues} were boundary-high but demoted for parse_issues (raw markers / av-ru contamination)")
    if stats.get("rescued"):
        print(f"rescued {stats['rescued']} word(s) via known-word б/6/й/ё stress-glyph correction")
    if stats.get("stress_recorded"):
        print(f"recorded stress position for {stats['stress_recorded']} of those word(s)")
    if stats.get("pipe_corruption_split"):
        print(f"split {stats['pipe_corruption_split']} ц/Ц-as-'||' word(s) into spelling_forms")
    if stats.get("dropped_bare_duplicates"):
        print(f"dropped {stats['dropped_bare_duplicates']} bare-stub duplicate(s)")
    if unaccounted:
        print(f"HARD GATE FAILED: {unaccounted} draft article(s) have no outcome")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

