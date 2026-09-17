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
from extract_geometry import (  # noqa: E402
    CONTINUATION_START_RE,
    DEFAULT_PDF,
    TRAILING_HYPHEN_RE,
    extract_page,
)

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from build_site import (  # noqa: E402
    AVAR_ALPHABET,
    make_rank,
    make_sort_key,
    make_tokenizer,
    normalize_palochka,
)

_AVAR_SORT_KEY = make_sort_key(make_rank(AVAR_ALPHABET), make_tokenizer("av"))

# 'о' misread as digit '6' by OCR in some bold runs (found on pages 138, 217,
# ...: *в6рхалъи for *ворхалъи). Not part of the project's normalize_palochka
# contract (that's only for the palochka glyph itself), so handled locally
# and only as a segmentation-matching aid — never treated as verified text.
DIGIT_GLYPH_RE = re.compile(r"[6]")


def normalize_token(text: str) -> tuple[str, bool]:
    """Return (normalized-for-matching text, digit_glyph_suspect).

    Applies the project's palochka normalization (fixes e.g. 'ч1' -> 'чӏ',
    common since palochka OCRs as digit '1') and flags embedded '6' digits
    likely standing in for 'о'. Only used to decide segmentation boundaries;
    the original OCR text is preserved separately for human review.

    Skips palochka normalization entirely for a literal '||' spelling
    variant: normalize_palochka() treats a lone '|' as a palochka-glyph
    candidate and rewrites it to '1' when not preceded by a digraph base
    letter (e.g. "айги||айгияли" -> "айги11айгияли"), which would destroy
    the '||' before SPELLING_VARIANT_RE ever sees it.
    """
    if "||" in text:
        return text, False
    normalized = normalize_palochka(text)
    suspect = bool(DIGIT_GLYPH_RE.search(normalized))
    if suspect:
        normalized = DIGIT_GLYPH_RE.sub("о", normalized)
    return normalized, suspect


# A single dictionary word-token: optional leading '*' (classifier marker),
# Avar/Cyrillic letters incl. palochka (Ӏ/ӏ) and internal hyphens, optional
# trailing punctuation carried over from OCR word splitting.
HEADWORD_RE = re.compile(
    r"^\*?[А-Яа-яЁёӀӏ]+(?:-[А-Яа-яЁёӀӏ]+)*[.,;:!?)\u00ad]*$"
)
# "||" spelling variant (cf. handoff doc: "мажикь||мажбикь"). This is always
# its own headword, even when the previous token ends only with a comma
# (seen embedded mid-sentence in a ср.-list, e.g. p.29 "*айги||айгияли") —
# '|' can never appear inside HEADWORD_RE, so without this the whole token
# was invisible to segmentation, not just failing the boundary check.
SPELLING_VARIANT_RE = re.compile(
    r"^(\*?)([А-Яа-яЁёӀӏ]+)\|\|([А-Яа-яЁёӀӏ]+)([.,;:!?)]*)$"
)
# Only sentence-ending punctuation closes an article; ';' and ')' merely
# separate senses/parentheticals *within* the same article (verified against
# page 23: multi-sense entries stay open across ';' and end on '.'/'?'/'!').
TERMINATOR_RE = re.compile(r"[.?!]$")

# A real forms bracket ("[род. п. X; мн. Y]") never spans more than a
# handful of words. If OCR drops the closing "]", segment_stream's
# `in_brackets` state used to stay True for the rest of the page, silently
# suppressing every subsequent headword candidate (found via p.??'s "ахѳи",
# whose `forms` swallowed dozens of following dictionary entries all the
# way to "аят" per av-ru-1967-review-2026-09-17.md's "P0. Незакрытая
# квадратная скобка"). Give up waiting past this many tokens.
MAX_BRACKET_TOKENS = 15
# 'ср.'/'см.' introduce a list of cross-reference targets (also set bold,
# since they are Avar words) that must not be mistaken for new headwords.
REFERENCE_LIST_RE = re.compile(r"^(ср|см)[.,]*$", re.IGNORECASE)
BARE_FROM_RE = re.compile(r"^от$", re.IGNORECASE)
ROMAN_RE = re.compile(r"^(I{1,3}|IV|V)$")
# A bare Russian grammatical form can never be a genuine Avar headword on
# its own — found via quality_scan.py turning up ~100+ high-confidence
# "headwords" like "закрывать"/"горячий" even on pages where the page-level
# bold-reliability check (below) doesn't fire, because only ONE stray word
# on an otherwise-fine page got bold. Token-level, so it catches this
# regardless of which page it's on. Verb endings (ть/ться) are an
# unambiguous 100%-Russian signal — Avar borrows Russian nouns as-is but
# always re-verbalizes borrowed verbs with its own morphology, never keeps
# a bare Russian infinitive as a lexeme. Noun-ish endings (ие/ая/ое/...) are
# weaker (a genuine borrowed noun could end that way), so those only count
# when the word ALSO fails to resolve against the modern dictionary.
STRONG_RUSSIAN_ENDING_RE = re.compile(r"(ться|ть)$")
WEAK_RUSSIAN_ENDING_RE = re.compile(r"(ий|ая|ое|ые|ение|ание|ность)$")
AVAR_DIGRAPHS = ("гъ", "гь", "гӏ", "къ", "кь", "кӏ", "лъ", "тӏ", "хъ", "хь", "хӏ", "цӏ", "чӏ")
# Closed-class Russian function words/pronouns: unlike nouns, a language
# essentially never borrows another language's pronouns/adverbs/particles
# wholesale, so any exact match here is never a genuine Avar headword.
# Found via p.262, where a page-wide "bold marks everything, not just
# Avar" pattern let "откуда" through as a bogus headword four times (it's
# the *translation* of several real headwords like "кисан", "кисаго").
RUSSIAN_FUNCTION_WORDS = {
    "где", "куда", "откуда", "когда", "почему", "зачем", "что",
    "кто", "чей", "какой", "который", "сколько", "здесь", "там", "туда",
    "оттуда", "везде", "всюду", "нигде", "никуда", "ниоткуда", "никогда",
    "вы", "мы", "он", "она", "оно", "они", "это", "нибудь", "либо",
    "его", "ему", "её", "ей", "их", "им", "ими", "меня", "мне", "мной",
    "тебя", "тебе", "тобой", "нас", "нам", "нами", "вас", "вам", "вами",
    "себя", "себе", "собой", "на", "не", "и", "к", "в", "с", "чтоб", "отовсюду",
    # Recurring Russian GLOSS words (not grammatically closed-class, but
    # each showed up as a bogus headword multiple times across unrelated
    # pages per av-ru-1967-review-2026-09-17.md's "P0. Русский текст
    # становится заглавным словом" — a stray-bold first word of a
    # translation continuation, never a genuine Avar headword. Unlike the
    # pronouns/particles above, these are content nouns, so kept to a
    # narrow, evidence-based list rather than trying to reject "any"
    # Russian noun (that would risk real Avar loanwords).
    "как", "занятие", "ймя", "имя", "сокрытие", "бытиё", "нагоняй", "укрытие",
}


def looks_like_bare_russian(word: str, known_words: set[str]) -> bool:
    lowered = word.lower()
    if any(d in lowered for d in AVAR_DIGRAPHS) or "ӏ" in word:
        return False
    if lowered in RUSSIAN_FUNCTION_WORDS:
        # Still deferred to known_words first — "как" (Arabic-derived
        # "namaz") was found colliding with this exact class of word, so
        # even closed-class Russian words aren't rejected blindly.
        return word not in known_words
    if STRONG_RUSSIAN_ENDING_RE.search(word):
        return True
    return bool(WEAK_RUSSIAN_ENDING_RE.search(word)) and word not in known_words


# Bare-lookup threshold: pages with fewer than this many bold-not-italic body
# words are treated as "bold metadata lost" (cf. handoff doc: 69/597 pages,
# e.g. p.400). Kept above a handful, since a few incidental bold cross-
# reference targets can appear even on pages where headwords aren't bold at
# all (e.g. p.221: 5 stray bold "ср." targets, headwords all plain).
LOW_BOLD_WORD_COUNT = 10


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
# The book sometimes prints a label immediately followed by a comma instead
# of its own period (e.g. "повел," rather than "повел."), so comparisons
# strip both before matching against this period-less form of LABEL_SET.
LABEL_SET_BARE = {label.rstrip(".") for label in LABEL_SET}
LABEL_LOOKAHEAD_WINDOW = 4


def is_label_token(token: str) -> bool:
    return token.strip(",.") in LABEL_SET_BARE


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
                norm, digit_suspect = normalize_token(word["text"])
                stream.append(
                    {
                        **word,
                        "norm": norm,
                        "digit_suspect": digit_suspect,
                        "page": data["page"],
                        "column": column,
                        "line_index": line_index,
                    }
                )
    return dehyphenate_stream(stream)


def dehyphenate_stream(stream: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rejoin a line-wrap hyphen split across the left/right column boundary.

    extract_geometry.dehyphenate_column() already handles the common
    within-column case; this catches the left-column's last line ending in a
    hyphen that continues on the right column's first line (both are
    adjacent in this flattened reading order already).
    """
    merged: list[dict[str, Any]] = []
    i = 0
    n = len(stream)
    while i < n:
        cur = stream[i]
        if i + 1 < n:
            match = TRAILING_HYPHEN_RE.match(cur["text"])
            nxt = stream[i + 1]
            if match and CONTINUATION_START_RE.match(nxt["text"]):
                text = match.group(1) + match.group(2) + nxt["text"]
                norm, digit_suspect = normalize_token(text)
                merged.append(
                    {**cur, "text": text, "norm": norm, "digit_suspect": digit_suspect, "x1": nxt["x1"]}
                )
                i += 2
                continue
        merged.append(cur)
        i += 1
    return merged


def bold_word_count(stream: list[dict[str, Any]]) -> int:
    """Count words plausibly bold-as-headword/Avar-text (bold, not italic).

    Some pages (e.g. 217) use a bold *italic* font only for grammatical
    labels and leave headwords in plain regular font — counting all bold
    words there would wrongly report "bold available" and disable the
    label/known-word fallback that is actually needed.
    """
    return sum(1 for w in stream if w["bold"] and not w["italic"])


# Fraction of bold-not-italic words that need to look Avar-ish (contain a
# digraph or palochka) before the primary bold signal is trusted. Found by
# scanning all 597 pages: normal pages sit ~0.15-0.8 (many short Avar words
# have no digraph, so it's never near 1.0), but a contiguous run of pages
# (e.g. 93-123) sits at 0.0-0.13 — bold there is assigned to the *Russian*
# translation instead of the Avar headword/example (page-97-style
# inversion, distinct from p.217's bold-italic-labels-only pattern: here
# there's plenty of bold-not-italic text, it's just the wrong language).
MIN_AVAR_BOLD_FRACTION = 0.10


def bold_is_reliable(stream: list[dict[str, Any]]) -> bool:
    bold_words = [w["norm"] for w in stream if w["bold"] and not w["italic"]]
    if len(bold_words) < LOW_BOLD_WORD_COUNT:
        return False
    avar_like = sum(
        1 for w in bold_words if any(d in w.lower() for d in AVAR_DIGRAPHS) or "ӏ" in w
    )
    return (avar_like / len(bold_words)) >= MIN_AVAR_BOLD_FRACTION


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
    if i + 1 < len(stream) and NUMBERED_SENSE_RE.match(stream[i + 1]["norm"]):
        return True
    steps = 0
    j = i + 1
    while j < len(stream) and steps < LABEL_LOOKAHEAD_WINDOW:
        tok = stream[j]
        if tok["italic"] and is_label_token(tok["norm"]):
            return True
        if TERMINATOR_RE.search(tok["norm"]):
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
    bold_available = bold_is_reliable(stream)
    # True while inside a "ср./см. X, Y, Z." cross-reference list: those X/Y/Z
    # are bold Avar words too, but they are reference targets, not headwords.
    in_reference_list = False
    skip_next_bold = False  # one-shot suppression right after a bare "от"
    in_brackets = False  # forms list "[род. п. X; мн. Y]" — never a headword
    in_brackets_since = 0  # index where the bracket opened, for MAX_BRACKET_TOKENS

    for i, word in enumerate(stream):
        text = word["norm"]
        stripped = text.strip(",.")

        variant_match = SPELLING_VARIANT_RE.match(text) if word["bold"] and not word["italic"] else None
        if variant_match:
            # Always a new headword, even mid-sentence after a comma or
            # inside a still-open ср.-list (cf. p.29 "*айги||айгияли"
            # embedded inside "ай"'s ср.-list) — the '||' pattern is
            # unambiguous on its own, so it interrupts any other state.
            in_reference_list = False
            in_brackets = False
            star, first, second, _trail = variant_match.groups()
            base = first.lower()
            sort_key = _AVAR_SORT_KEY(base)
            reasons = ["bold", "spelling-variant-pipe"]
            confidence = "high"
            if last_sort_key is not None and sort_key < last_sort_key:
                reasons.append("alphabet-regression")
                confidence = "low"
            candidates.append(
                {
                    "page": word["page"],
                    "column": word["column"],
                    "top": word["top"],
                    "index": i,
                    "raw": word["text"],
                    "word_guess": base,
                    "homonym": None,
                    "star": bool(star),
                    "confidence": confidence,
                    "reasons": reasons,
                    "spelling_variants": [base, second.lower()],
                }
            )
            last_headword = base
            last_sort_key = sort_key
            prev = word
            continue

        if in_brackets:
            if "]" in text:
                in_brackets = False
                prev = word
                continue
            if i - in_brackets_since > MAX_BRACKET_TOKENS:
                # Unclosed bracket — OCR lost the "]". Give up rather than
                # suppressing headword detection indefinitely, and let THIS
                # token (which triggered giving up) fall through to the
                # normal candidate checks below instead of being silently
                # skipped — it's often the real next headword. Bounded on
                # token count alone, NOT on hitting a "." — abbreviations
                # like "1-го скл." legitimately end in "." while still
                # inside a real, longer multi-declension-class bracket
                # (found via p.82's "библиотекарь [род. п. 1-го скл.
                # библиотекарасул, 2-го скл. библиотекаралъул]" — bailing
                # out at "скл." cut the bracket short and turned its own
                # form into a bogus headword).
                in_brackets = False
            else:
                prev = word
                continue

        if "[" in text:
            in_brackets = "]" not in text
            in_brackets_since = i
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

        if looks_like_bare_russian(base, known_words):
            prev = word
            continue

        if skip_next_bold and word["bold"]:
            skip_next_bold = False
            prev = word
            continue
        skip_next_bold = False

        at_boundary = prev is None or bool(TERMINATOR_RE.search(prev["norm"]))
        if not at_boundary and prev is not None and prev["norm"].rstrip().endswith(","):
            # A sentence-ending period is sometimes OCR'd as a comma (found
            # via p.262 "...помощи," and p.358 "...благодатный,", both
            # should read "."), silently swallowing the next real headword
            # into the previous entry. Narrow fallback: only accept it when
            # the very NEXT token immediately confirms a genuine headword
            # header shape — an italic label, a "[forms]" bracket, a
            # roman-numeral homonym marker, or (found via p.38's "ашбаз"
            # swallowing "аэродром аэродром, аэроплан аэроплан, ...", 299
            # occurrences book-wide) a direct Russian/Avar loanword whose
            # own gloss just repeats the same word — not just "some bold
            # word anywhere nearby", which fired far too often (1409 hits
            # book-wide) when tried with a wider lookahead window.
            nxt = stream[i + 1] if i + 1 < len(stream) else None
            self_gloss = (
                nxt is not None
                and base in known_words
                and nxt["norm"].strip(",.;").lower() == base.lower()
            )
            if (
                word["bold"]
                and not word["italic"]
                and base in known_words
                and nxt is not None
                and (
                    (nxt["italic"] and is_label_token(nxt["norm"]))
                    or nxt["norm"].startswith("[")
                    or ROMAN_RE.match(nxt["norm"])
                    or self_gloss
                )
            ):
                at_boundary = True
        if not at_boundary:
            prev = word
            continue

        reasons = []
        confidence = "low"

        if bold_available and word["bold"] and not word["italic"]:
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
        if i + 1 < len(stream) and ROMAN_RE.match(stream[i + 1]["norm"]):
            nxt = stream[i + 1]
            if nxt["bold"] == word["bold"]:
                homonym = stream[i + 1]["text"]
                reasons.append("homonym-roman-numeral")

        if word["digit_suspect"]:
            reasons.append("digit-glyph-suspect")
            confidence = "low"

        candidates.append(
            {
                "page": word["page"],
                "column": word["column"],
                "top": word["top"],
                "index": i,
                "raw": word["text"],
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
        low_bold = not bold_is_reliable(stream)
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
