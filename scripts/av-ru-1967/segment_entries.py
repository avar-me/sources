#!/usr/bin/env python3
"""Article-boundary segmentation for the 1967 Saidov dictionary PDF.

Step 3 of av-ru-1967-parsing-handoff.md ("Сегментация статей"): given the
per-page word geometry from extract_geometry.py, propose headword candidate
positions with a confidence and the reasons behind each decision. This does
NOT parse senses/examples yet — it only finds where articles start.

Requires pdfplumber (see scripts/av-ru-1967/README.md for env setup).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
from extract_geometry import DEFAULT_PDF, extract_page  # noqa: E402

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from build_site import AVAR_ALPHABET, make_rank, make_sort_key, make_tokenizer  # noqa: E402

_AVAR_SORT_KEY = make_sort_key(make_rank(AVAR_ALPHABET), make_tokenizer("av"))

# A single dictionary word-token: optional leading '*' (classifier marker),
# Avar/Cyrillic letters incl. palochka (Ӏ/ӏ) and internal hyphens, optional
# trailing punctuation carried over from OCR word splitting.
HEADWORD_RE = re.compile(
    r"^\*?[А-Яа-яЁёӀӏ]+(?:-[А-Яа-яЁёӀӏ]+)*[.,;:!?)\u00ad]*$"
)
# Only sentence-ending punctuation closes an article; ';' and ')' merely
# separate senses/parentheticals *within* the same article (verified against
# page 23: multi-sense entries stay open across ';' and end on '.'/'?'/'!').
TERMINATOR_RE = re.compile(r"[.?!]$")
# 'ср.'/'см.' introduce a list of cross-reference targets (also set bold,
# since they are Avar words) that must not be mistaken for new headwords.
REFERENCE_LIST_RE = re.compile(r"^(ср|см)[.,]*$", re.IGNORECASE)
BARE_FROM_RE = re.compile(r"^от$", re.IGNORECASE)
ROMAN_RE = re.compile(r"^(I{1,3}|IV|V)$")
# Bare-lookup thresholds: pages with fewer than this many bold body words are
# treated as "bold metadata lost" (cf. handoff doc: 69/597 pages, e.g. p.400).
LOW_BOLD_WORD_COUNT = 5

# Grammatical/stylistic abbreviations from the handoff doc's normalization
# table (schemas/av-ru.md labels) plus case markers seen right after a
# headword (e.g. p.31 "эрг. п.", "род. п."). Italic tagging survives even on
# pages where bold metadata is lost, so "headword candidate immediately
# followed by one of these" is a bold-independent segmentation signal.
LABEL_SET = {
    "масд.", "понуд.", "учащ.", "нареч.", "мест.", "числ.", "межд.",
    "повел.", "уст.", "разг.", "перен.", "погов.", "посл.", "анат.",
    "биол.", "бот.", "бран.", "вет.", "грам.", "диал.", "зоол.", "ирон.",
    "ист.", "ласк.", "лит.", "мат.", "мед.", "рел.", "собир.", "фольк.",
    "гл.", "букв.", "род.", "дат.", "местн.", "эрг.", "им.", "твор.",
    "направ.", "ед.", "мн.", "скл.", "обращ.", "п.", "ср.", "см.",
}
LABEL_LOOKAHEAD_WINDOW = 4


def load_known_words(av_ru_path: Path) -> set[str]:
    """Word forms from the modern av-ru.jsonl, used only as a segmentation
    hint on pages where OCR bold metadata is missing. Never used to invent
    or overwrite 1967 content."""
    known: set[str] = set()
    if not av_ru_path.exists():
        return known
    with av_ru_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            for key in ("word", "forms", "spelling_forms", "gender_forms"):
                value = entry.get(key)
                if isinstance(value, str):
                    known.add(value)
                elif isinstance(value, list):
                    known.update(v for v in value if isinstance(v, str))
    return known


def strip_word(token: str) -> str:
    return token.lstrip("*").rstrip(".,;:!?)\u00ad").lower()


def page_word_stream(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a page's geometry dump into left-column-then-right-column
    reading order, one dict per word with page/column/line context added."""
    stream: list[dict[str, Any]] = []
    for column in ("left", "right"):
        for line_index, line in enumerate(data[column]):
            for word in line["words"]:
                stream.append(
                    {
                        **word,
                        "page": data["page"],
                        "column": column,
                        "line_index": line_index,
                    }
                )
    return stream


def bold_word_count(stream: list[dict[str, Any]]) -> int:
    return sum(1 for w in stream if w["bold"])


# "1." / "2)" etc right after a headword split grammatically distinct groups
# (cf. handoff doc: "категории и переводы даются под отдельными полужирными
# цифрами"). This marker carries no distinct font on low-bold pages, so it
# is checked regardless of italic/bold.
NUMBERED_SENSE_RE = re.compile(r"^\d[.)]$")


def label_follows(stream: list[dict[str, Any]], i: int) -> bool:
    """True if an italic grammatical label appears within a few tokens after
    position i, before the next terminator, or a numbered-sense marker is
    the immediate next token. Bold-independent alternative to the primary
    bold signal, for pages where bold metadata is missing."""
    if i + 1 < len(stream) and NUMBERED_SENSE_RE.match(stream[i + 1]["text"]):
        return True
    steps = 0
    j = i + 1
    while j < len(stream) and steps < LABEL_LOOKAHEAD_WINDOW:
        tok = stream[j]
        if tok["italic"] and tok["text"].rstrip(",") in LABEL_SET:
            return True
        if TERMINATOR_RE.search(tok["text"]):
            break
        j += 1
        steps += 1
    return False


def segment_stream(
    stream: list[dict[str, Any]], known_words: set[str]
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    last_headword: str | None = None
    last_sort_key = None
    prev: dict[str, Any] | None = None
    bold_available = bold_word_count(stream) >= LOW_BOLD_WORD_COUNT
    # True while inside a "ср./см. X, Y, Z." cross-reference list: those X/Y/Z
    # are bold Avar words too, but they are reference targets, not headwords.
    in_reference_list = False
    skip_next_bold = False  # one-shot suppression right after a bare "от"
    in_brackets = False  # forms list "[род. п. X; мн. Y]" — never a headword

    for i, word in enumerate(stream):
        text = word["text"]
        stripped = text.strip(",.")

        if in_brackets:
            if "]" in text:
                in_brackets = False
            prev = word
            continue

        if "[" in text:
            in_brackets = "]" not in text
            prev = word
            continue

        if in_reference_list:
            if TERMINATOR_RE.search(text):
                in_reference_list = False
            prev = word
            continue

        if word["italic"] and REFERENCE_LIST_RE.match(stripped):
            # The marker's own abbreviation period ("ср.") is not a sentence
            # terminator, so the list always opens here regardless of it.
            in_reference_list = True
            prev = word
            continue

        if not word["bold"] and not word["italic"] and BARE_FROM_RE.match(stripped):
            skip_next_bold = True
            prev = word
            continue

        if word["italic"]:
            # A grammatical/stylistic label, never a headword itself.
            prev = word
            continue

        if not HEADWORD_RE.match(text):
            prev = word
            continue

        base = strip_word(text)
        if not base:
            prev = word
            continue

        if skip_next_bold and word["bold"]:
            skip_next_bold = False
            prev = word
            continue
        skip_next_bold = False

        at_boundary = prev is None or bool(TERMINATOR_RE.search(prev["text"]))
        if not at_boundary:
            prev = word
            continue

        reasons = []
        confidence = "low"

        if word["bold"] and not word["italic"]:
            reasons.append("bold")
            confidence = "high"
        else:
            if not bold_available and base in known_words:
                reasons.append("known-word-fallback")
                confidence = "medium"
            if not bold_available and label_follows(stream, i):
                reasons.append("label-lookahead")
                confidence = "medium"
            if not reasons:
                prev = word
                continue

        sort_key = _AVAR_SORT_KEY(base)
        if last_sort_key is not None and sort_key < last_sort_key:
            reasons.append("alphabet-regression")
            confidence = "low"

        # Roman-numeral homonym marker directly after the headword.
        homonym = None
        if i + 1 < len(stream) and ROMAN_RE.match(stream[i + 1]["text"]):
            nxt = stream[i + 1]
            if nxt["bold"] == word["bold"]:
                homonym = stream[i + 1]["text"]
                reasons.append("homonym-roman-numeral")

        candidates.append(
            {
                "page": word["page"],
                "column": word["column"],
                "top": word["top"],
                "raw": text,
                "word_guess": base,
                "homonym": homonym,
                "star": text.lstrip().startswith("*"),
                "confidence": confidence,
                "reasons": reasons,
            }
        )
        last_headword = base
        last_sort_key = sort_key
        prev = word

    return candidates


def load_or_extract(pdf_path: str, page_number: int, geometry_dir: Path | None) -> dict[str, Any]:
    if geometry_dir is not None:
        cached = geometry_dir / f"page-{page_number:04d}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))
    with pdfplumber.open(pdf_path) as pdf:
        return extract_page(pdf.pages[page_number - 1], page_number)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default=DEFAULT_PDF)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument(
        "--geometry-dir",
        default="tmp/av-ru.1967/geometry",
        help="reuse cached extract_geometry.py output if present",
    )
    parser.add_argument("--av-ru", default="data/av-ru.jsonl")
    parser.add_argument(
        "--out",
        default="tmp/av-ru.1967/segments.jsonl",
        help="one JSON candidate per line",
    )
    args = parser.parse_args()

    known_words = load_known_words(Path(args.av_ru))
    geometry_dir = Path(args.geometry_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_candidates: list[dict[str, Any]] = []
    for page_number in range(args.start, args.end + 1):
        data = load_or_extract(args.pdf, page_number, geometry_dir)
        stream = page_word_stream(data)
        candidates = segment_stream(stream, known_words)
        all_candidates.extend(candidates)
        low_bold = bold_word_count(stream) < LOW_BOLD_WORD_COUNT
        print(
            f"page {page_number}: {len(candidates)} candidates"
            + (" (bold metadata missing, used known-word fallback)" if low_bold else "")
        )

    with out_path.open("w", encoding="utf-8") as fh:
        for candidate in all_candidates:
            fh.write(json.dumps(candidate, ensure_ascii=False) + "\n")
    print(f"wrote {len(all_candidates)} candidates to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
