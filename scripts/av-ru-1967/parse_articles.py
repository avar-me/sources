#!/usr/bin/env python3
"""Draft lexical parsing of segmented 1967 dictionary articles.

Step 4 of av-ru-1967-parsing-handoff.md: turn each headword span found by
segment_entries.py into a draft article (labels/forms/senses/examples).

This is explicitly a DRAFT/pilot output for human review, not the final
data/av-ru.1967.jsonl. It deliberately keeps raw abbreviation strings
(`labels_raw`, `forms_raw`) instead of committing to final schema label
names or pos/form values — the handoff doc warns against guessing those
without cross-checking data/av-ru.jsonl's accepted vocabulary, and see_also
targets can't be resolved until the whole dictionary has been parsed (step
5, "второй проход"). Requires pdfplumber (see scripts/av-ru-1967/README.md).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from extract_geometry import (  # noqa: E402
    CONTINUATION_START_RE,
    DEFAULT_PDF,
    TRAILING_HYPHEN_RE,
)
from segment_entries import (  # noqa: E402
    AVAR_DIGRAPHS,
    BARE_FROM_RE,
    HEADWORD_RE,
    MAX_BRACKET_TOKENS,
    NUMBERED_SENSE_RE,
    REFERENCE_LIST_RE,
    ROMAN_RE,
    RUSSIAN_FUNCTION_WORDS,
    TERMINATOR_RE,
    bold_is_reliable,
    is_label_token,
    load_known_words,
    load_or_extract,
    normalize_token,
    page_word_stream,
    segment_stream,
    strip_word,
)


def has_avar_signal(word: str) -> bool:
    lowered = word.lower()
    return any(d in lowered for d in AVAR_DIGRAPHS) or "ӏ" in word

# Unlike segment_entries.TERMINATOR_RE (headword boundaries, where ';' is
# explicitly excluded), a numbered sense marker legitimately follows ';'.
SENSE_BOUNDARY_RE = re.compile(r"[.;?!]$")

# "масд. глагола X" (masdar of verb X) is a second from-reference marker
# alongside bare "от" (cf. handoff doc: "масдар от инфинитива... формула масд. глагола X").
# Plural "глаголов X I и II" (masdar shared by both homonym verbs, e.g.
# p.284's "къин масд. глаголов къине I и II") uses the same marker shape.
MASDAR_FROM_RE = re.compile(r"^глагол(а|ов)$", re.IGNORECASE)

# "I и II" (or missing-space-OCR "Iи II") right after a headword/reference
# target lists which homonyms a shared masdar/понуд. form applies to — see
# consume_trailing_homonyms(). ROMAN_RE itself only matches a clean "I"/"II"
# token; this covers the fused "Iи" OCR variant (found on p.284's "къин").
HOMONYM_FUSED_RE = re.compile(r"^(I{1,3}|IV|V)и$")

# Doc's normalization table (av-ru-1967-parsing-handoff.md, "Нормализация
# сокращений и labels") for abbreviations safe to turn directly into a
# labels[] entry. Deliberately excludes мест./числ./межд./нареч./гл. — those
# read as `pos`, which the doc says must not be guessed from a bare
# abbreviation without corroborating structure.
LABEL_NORMALIZE: dict[str, list[str]] = {
    "анат": ["анатомия"],
    "биол": ["биология"],
    "бот": ["ботаника"],
    "бран": ["бранное слово", "выражение"],
    "вет": ["ветеринария"],
    "грам": ["грамматика"],
    "диал": ["диалектизм"],
    "зоол": ["зоология"],
    "ирон": ["в ироническом смысле"],
    "ист": ["исторический термин"],
    "ласк": ["ласкательная форма"],
    "лит": ["литература, литературоведение"],
    "мат": ["математика"],
    "мед": ["медицина"],
    "перен": ["в переносном значении"],
    "погов": ["поговорка"],
    "понуд": ["понудительная форма"],
    "посл": ["пословица"],
    "поэт": ["поэтическое слово"],
    "разг": ["разговорное слово", "выражение"],
    "рел": ["религия"],
    "собир": ["собирательное существительное"],
    "уст": ["устаревшее слово"],
    "учащ": ["учащательная форма"],
    "фольк": ["фольклор"],
}

DIAMOND_RE_CHARS = set("<>◊❖♦")


def is_diamond(token: str) -> bool:
    return bool(token) and all(c in DIAMOND_RE_CHARS for c in token)


def build_article_spans(stream: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Slice a page's word stream into one span per detected headword.

    The last candidate's span runs to the end of the page and is marked
    `continues_next_page` if it doesn't end on a real terminator — see
    `stitch_carry()` in main() for how the continuation is picked back up
    on the next page.
    """
    spans = []
    for idx, cand in enumerate(candidates):
        start = cand["index"]
        end = candidates[idx + 1]["index"] if idx + 1 < len(candidates) else len(stream)
        tokens = stream[start:end]
        continues = bool(tokens) and not TERMINATOR_RE.search(tokens[-1]["norm"])
        spans.append({"candidate": cand, "tokens": tokens, "continues_next_page": continues})
    return spans


def candidate_id(cand: dict[str, Any]) -> str:
    """Stable id for a segment_stream() candidate — (page, column, index)
    uniquely identifies its position in the page's word stream.
    av-ru-1967-review-batch-4-2026-09-17.md, "1. Ввести per-candidate
    outcome ledger": every candidate must get exactly one outcome, so it
    needs an id that survives independent of anything downstream."""
    return f"candidate:{cand['page']}:{cand['column']}:{cand['index']}"


def stitch_tokens(prev_tokens: list[dict[str, Any]], next_tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Join a page's dangling last tokens with the next page's leading
    tokens, rejoining a line-wrap hyphen split across the page boundary
    itself (extract_geometry.dehyphenate_column/segment_entries.dehyphenate_stream
    only handle within-page splits — found via p.358/359's "ниж...ни-" +
    "жеца" -> "нижеца")."""
    if prev_tokens and next_tokens:
        match = TRAILING_HYPHEN_RE.match(prev_tokens[-1]["text"])
        if match and CONTINUATION_START_RE.match(next_tokens[0]["text"]):
            text = match.group(1) + match.group(2) + next_tokens[0]["text"]
            norm, digit_suspect = normalize_token(text)
            merged_last = {
                **prev_tokens[-1],
                "text": text,
                "norm": norm,
                "digit_suspect": digit_suspect,
                "x1": next_tokens[0].get("x1", prev_tokens[-1].get("x1")),
            }
            return prev_tokens[:-1] + [merged_last] + next_tokens[1:]
    return prev_tokens + next_tokens


def consume_header(tokens: list[dict[str, Any]], pos: int) -> tuple[list[str], str | None, int]:
    """After the headword (and optional homonym numeral), consume immediate
    italic labels and a single `[...]` forms bracket, in either order."""
    labels_raw: list[str] = []
    forms_raw: str | None = None
    n = len(tokens)
    while pos < n:
        tok = tokens[pos]
        norm = tok["norm"]
        if tok["italic"] and is_label_token(norm):
            labels_raw.append(norm)
            pos += 1
            continue
        if norm.startswith("["):
            # A real forms bracket ("[род. п. X; мн. Y]") never spans more
            # than a handful of words — bound it the same way
            # segment_entries.segment_stream's in_brackets is bounded
            # (MAX_BRACKET_TOKENS), so an OCR-lost "]" can't swallow the
            # rest of the article's senses/examples into `forms_raw`
            # (found via "ахӏи" per av-ru-1967-review-2026-09-17.md's "P0.
            # Незакрытая квадратная скобка"). If the bracket never closes
            # within the bound, drop it entirely rather than guessing —
            # the words fall through as ordinary sense text instead.
            start = pos
            bracket: list[str] = []
            closed = False
            while pos < n and pos - start <= MAX_BRACKET_TOKENS:
                cur = tokens[pos]["norm"]
                bracket.append(cur.lstrip("["))
                pos += 1
                if "]" in cur:
                    closed = True
                    break
            if closed:
                forms_raw = " ".join(bracket).rstrip("]")
                continue
            # Never closed within the bound — stop consuming the header
            # here (don't loop on the same "[" token forever) and leave
            # `pos` at the bracket's start so it falls through as ordinary
            # sense/example text instead of being guessed at. Bounded on
            # token count alone, NOT on hitting a "." — abbreviations like
            # "1-го скл." legitimately end in "." inside a real, longer
            # multi-declension-class bracket (found via p.82's
            # "библиотекарь [род. п. 1-го скл. библиотекарасул, 2-го скл.
            # библиотекаралъул]").
            pos = start
            break
        break
    return labels_raw, forms_raw, pos


def split_senses(tokens: list[dict[str, Any]], pos: int) -> list[list[dict[str, Any]]]:
    """Split the remaining body on numbered-sense markers (1)/2./etc). Unlike
    headword boundaries, a ';' *does* separate senses here (cf. handoff doc:
    "аби 1) высказывание; ...; 2) помолвка; ..." — sense 1 ends on ';', not
    on a full stop)."""
    n = len(tokens)
    boundaries = [pos]
    i = pos
    while i < n:
        if NUMBERED_SENSE_RE.match(tokens[i]["norm"]) and (
            i == pos or SENSE_BOUNDARY_RE.search(tokens[i - 1]["norm"])
        ):
            boundaries.append(i)
        i += 1
    boundaries.append(n)
    boundaries = sorted(set(boundaries))
    return [tokens[a:b] for a, b in zip(boundaries, boundaries[1:]) if tokens[a:b]]


def consume_trailing_homonyms(tokens: list[dict[str, Any]], i: int) -> int:
    """Consume roman-numeral homonym decoration ("I", "I и II", or the
    missing-space OCR variant "Iи II") right after a headword or reference
    target ("...от бичизе I и II.") — decorative ("applies to both/all of
    these homonyms"), not sense content. Found via p.93/284/418/469/493's
    russian-leaked-into-av findings, all sharing this exact header shape."""
    n = len(tokens)
    if i >= n:
        return i
    text = tokens[i]["norm"].rstrip(".")
    if ROMAN_RE.match(text):
        i += 1
        need_separator = True
    elif HOMONYM_FUSED_RE.match(text):
        # "Iи" == "I" + "и" glued together by OCR — the separator is
        # already spent, so the next numeral follows directly, no "и".
        i += 1
        need_separator = False
    else:
        return i
    while i < n:
        if need_separator:
            if (
                i + 1 < n
                and tokens[i]["norm"].lower() == "и"
                and ROMAN_RE.match(tokens[i + 1]["norm"].rstrip("."))
            ):
                i += 2
            else:
                break
        elif ROMAN_RE.match(tokens[i]["norm"].rstrip(".")):
            i += 1
            need_separator = True
        else:
            break
    return i


def parse_sense(tokens: list[dict[str, Any]], bold_reliable: bool = True) -> dict[str, Any]:
    marker = None
    pos = 0
    if tokens and NUMBERED_SENSE_RE.match(tokens[0]["norm"]):
        marker = tokens[0]["norm"]
        pos = 1
    labels_raw, _forms, pos = consume_header(tokens, pos)

    text_parts: list[str] = []
    examples: list[dict[str, str]] = []
    reference_targets: list[str] = []
    from_targets: list[str] = []
    masdar_targets: list[str] = []

    i = pos
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        norm = tok["norm"]
        stripped = norm.strip(",.")

        if tok["italic"] and REFERENCE_LIST_RE.match(stripped):
            i += 1
            while i < n:
                if HEADWORD_RE.match(tokens[i]["norm"]) and not tokens[i]["italic"]:
                    reference_targets.append(strip_word(tokens[i]["norm"]))
                if TERMINATOR_RE.search(tokens[i]["norm"]):
                    i += 1
                    break
                i += 1
            continue

        if MASDAR_FROM_RE.match(stripped) and i + 1 < n and not tokens[i + 1]["italic"] and HEADWORD_RE.match(tokens[i + 1]["norm"]):
            masdar_targets.append(strip_word(tokens[i + 1]["norm"]))
            i = consume_trailing_homonyms(tokens, i + 2)
            continue

        if BARE_FROM_RE.match(stripped) and i + 1 < n and not tokens[i + 1]["italic"] and HEADWORD_RE.match(tokens[i + 1]["norm"]):
            # "от X" morphological reference — accept regardless of the
            # marker's own font (seen both plain and italic), but only when
            # the next token looks like an actual headword-shaped target,
            # not a government label like "кого-чего-л." (always italic).
            from_targets.append(strip_word(tokens[i + 1]["norm"]))
            i = consume_trailing_homonyms(tokens, i + 2)
            continue

        if bold_reliable and tok["bold"] and not tok["italic"]:
            # Contiguous bold run = one Avar example phrase. Only trusted
            # on pages where bold reliably marks Avar text — on a
            # font-inverted page (bold_reliable=False) this would swap av
            # and ru (bold there tags the *Russian* translation instead),
            # so such tokens fall through to plain `text` below instead.
            run = [norm]
            j = i + 1
            while j < n:
                if tokens[j]["bold"] and not tokens[j]["italic"]:
                    run.append(tokens[j]["norm"])
                    j += 1
                    continue
                # A word in the middle of (or right after) the bold run
                # sometimes lost its own bold in OCR (opposite of the
                # stray-bold-Russian-word case, e.g. p.538's "гьедин" —
                # still clearly Avar since it contains a digraph, but not
                # bold, with the bold run resuming right after it on
                # "лъимаде"). Absorb it into `av` either way — whether bold
                # resumes after or this is genuinely the last av word
                # before `ru` begins — rather than treating it as an
                # example boundary and leaving a stray empty-`ru` example.
                if not tokens[j]["italic"] and has_avar_signal(tokens[j]["norm"]):
                    run.append(tokens[j]["norm"])
                    j += 1
                    continue
                break
            av = " ".join(run)
            # Everything up to the next example-separating ';' (or end) is
            # this example's Russian translation.
            ru_tokens = []
            k = j
            while k < n and not (tokens[k]["bold"] and not tokens[k]["italic"]):
                ru_tokens.append(tokens[k]["norm"])
                if norm_ends_segment(tokens[k]["norm"]):
                    k += 1
                    break
                k += 1
            examples.append({"av": av, "ru": " ".join(ru_tokens).strip()})
            i = k
            continue

        text_parts.append(norm)
        i += 1

    sense: dict[str, Any] = {}
    if marker:
        sense["marker"] = marker
    if labels_raw:
        sense["labels_raw"] = labels_raw
    text = " ".join(text_parts).strip()
    if text:
        sense["text"] = text
    if examples:
        sense["examples"] = examples
    if reference_targets:
        sense["reference_targets"] = reference_targets
    if from_targets:
        sense["from_targets"] = from_targets
    if masdar_targets:
        sense["masdar_targets"] = masdar_targets
    return sense


def norm_ends_segment(token: str) -> bool:
    return token.endswith(";") or bool(TERMINATOR_RE.search(token))


def normalize_labels(labels_raw: list[str]) -> list[str]:
    out: list[str] = []
    for raw in labels_raw:
        out.extend(LABEL_NORMALIZE.get(raw.strip(",."), []))
    return out


def is_russian_function_word(text: str, known_words: set[str]) -> bool:
    """RUSSIAN_FUNCTION_WORDS membership, also matching an indefinite-particle
    suffix glued onto a listed word ("какой-то", "какой-нибудь", "какой-либо"
    from "какой" — found via p.554's "цо" entry, where "какой-то;
    какой-нибудь;" got stray-bold and split into a bogus example). Gated on
    known_words the same way looks_like_bare_russian is — "как" (Arabic-derived
    "намаз") is both a listed Russian word AND a real Avar headword, so an
    exact-text match alone isn't enough to safely demote its bold."""
    lowered = text.strip(",.;:!?").lower()
    if lowered in RUSSIAN_FUNCTION_WORDS:
        return lowered not in known_words
    for suffix in ("-то", "-нибудь", "-либо"):
        if lowered.endswith(suffix) and lowered[: -len(suffix)] in RUSSIAN_FUNCTION_WORDS:
            return True
    return False


def demote_stray_function_words(
    tokens: list[dict[str, Any]], known_words: set[str]
) -> list[dict[str, Any]]:
    """A bold-not-italic token that's an isolated Russian pronoun/adverb
    (found on otherwise-normal pages, e.g. p.294's "его" mid-sentence in
    "я заставлю его") is never a real Avar example — treat it as plain text by
    clearing its bold flag, so it neither starts a bogus example nor cuts
    a real one short while its ru-side is still being collected."""
    out = []
    for tok in tokens:
        if tok["bold"] and not tok["italic"] and is_russian_function_word(tok["norm"], known_words):
            tok = {**tok, "bold": False}
        out.append(tok)
    return out


def parse_article(
    span: dict[str, Any], bold_reliable: bool = True, known_words: set[str] | None = None
) -> dict[str, Any]:
    cand = span["candidate"]
    tokens = demote_stray_function_words(span["tokens"], known_words or set())
    raw_text = " ".join(t["text"] for t in tokens)

    pos = 1  # skip the headword token itself
    if pos < len(tokens) and (
        ROMAN_RE.match(tokens[pos]["norm"]) or HOMONYM_FUSED_RE.match(tokens[pos]["norm"])
    ):
        pos = consume_trailing_homonyms(tokens, pos)

    labels_raw, forms_raw, pos = consume_header(tokens, pos)

    diamond_at = None
    for i in range(pos, len(tokens)):
        if is_diamond(tokens[i]["norm"]):
            diamond_at = i
            break

    body_tokens = tokens[pos:diamond_at] if diamond_at is not None else tokens[pos:]
    sense_spans = split_senses(body_tokens, 0)
    senses = [parse_sense(s, bold_reliable) for s in sense_spans]
    senses = [s for s in senses if s]

    article: dict[str, Any] = {
        "page": cand["page"],
        "column": cand.get("column"),
        "top": cand.get("top"),
        "word": cand["word_guess"],
        "word_raw": cand["raw"],
        "star": cand["star"],
        "confidence": cand["confidence"],
        "reasons": cand.get("reasons", []),
    }
    if cand["homonym"]:
        article["homonym"] = cand["homonym"]
    if cand.get("spelling_variants"):
        article["spelling_variants"] = cand["spelling_variants"]
    if labels_raw:
        article["labels_raw"] = labels_raw
        normalized = normalize_labels(labels_raw)
        if normalized:
            article["labels"] = normalized
    if forms_raw:
        article["forms_raw"] = forms_raw
    if senses:
        article["senses"] = senses
    if diamond_at is not None:
        diamond_sense = parse_sense(tokens[diamond_at + 1 :], bold_reliable)
        if diamond_sense:
            article["diamond_sense"] = diamond_sense
    if span["continues_next_page"]:
        article["continues_next_page"] = True
    # av-ru-1967-review-batch-4-2026-09-17.md, item 7 "Исправить multi-page
    # provenance": a merged carry's tokens carry their own physical `page`
    # (page_word_stream() tags every token before any cross-page stitching
    # happens), so the SET of distinct pages among an article's own tokens
    # is a real structural fact — not just the candidate's starting page —
    # and lets an intervening zero-candidate page (e.g. p.551, entirely
    # absorbed into p.550's "цебё") be linked back to its absorbing article
    # instead of a hardcoded per-page explanation string.
    source_pages = sorted({t["page"] for t in tokens if "page" in t})
    if len(source_pages) > 1:
        article["source_pages"] = source_pages
    article["raw_text"] = raw_text
    return article


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default=DEFAULT_PDF)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--geometry-dir", default="tmp/av-ru.1967/geometry")
    parser.add_argument("--av-ru", default="data/av-ru.jsonl")
    parser.add_argument("--out", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--outcomes", default="tmp/av-ru.1967/candidate_outcomes.jsonl")
    args = parser.parse_args()

    known_words = load_known_words(Path(args.av_ru))
    geometry_dir = Path(args.geometry_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    articles: list[dict[str, Any]] = []
    # av-ru-1967-review-batch-4-2026-09-17.md, "1. Ввести per-candidate
    # outcome ledger": every segment_stream() candidate gets exactly one
    # outcome here — "own-article" (it became its own draft article) or
    # "merged-into:<candidate_id>" (its span got swallowed into a
    # cross-page carry continuation instead, see the carry-handling block
    # below — the only place a candidate DOESN'T produce its own span).
    candidate_outcomes: list[dict[str, Any]] = []
    # Carries an unterminated last span across a page boundary: {"candidate":
    # ..., "tokens": [...]} for the previous page's dangling last article, to
    # be re-parsed together with whatever continues at the top of the next
    # page (see stitch_tokens() and the "suspect first candidate" check
    # below — found via p.358/359's "ниж" entry, whose "ни-" continuation
    # "жеца" was otherwise mis-detected as a brand-new bold headword).
    carry: dict[str, Any] | None = None
    for page_number in range(args.start, args.end + 1):
        data = load_or_extract(args.pdf, page_number, geometry_dir)
        stream = page_word_stream(data)
        candidates = segment_stream(stream, known_words)
        bold_reliable = bold_is_reliable(stream)
        spans = build_article_spans(stream, candidates)

        if carry is not None:
            if spans and spans[0]["candidate"]["index"] == 0:
                # The page's very first token was independently detected as
                # a new headword candidate. Since the previous entry didn't
                # end on a real terminator, this is almost certainly still
                # that entry's own continuation (a stray bold word, not a
                # genuine new headword) — swallow the whole span into the
                # continuation rather than trusting it.
                continuation_tokens = spans[0]["tokens"]
                candidate_outcomes.append(
                    {
                        "candidate_id": candidate_id(spans[0]["candidate"]),
                        "page": spans[0]["candidate"]["page"],
                        "column": spans[0]["candidate"]["column"],
                        "index": spans[0]["candidate"]["index"],
                        "word_guess": spans[0]["candidate"].get("word_guess"),
                        "outcome": f"merged-into:{candidate_id(carry['candidate'])}",
                    }
                )
                spans = spans[1:]
            else:
                first_idx = spans[0]["candidate"]["index"] if spans else len(stream)
                continuation_tokens = stream[:first_idx]
            merged_tokens = stitch_tokens(carry["tokens"], continuation_tokens)
            merged_continues = bool(merged_tokens) and not TERMINATOR_RE.search(merged_tokens[-1]["norm"])
            merged_span = {
                "candidate": carry["candidate"],
                "tokens": merged_tokens,
                "continues_next_page": merged_continues,
            }
            articles[-1] = parse_article(merged_span, bold_reliable, known_words)
            carry = {"candidate": carry["candidate"], "tokens": merged_tokens} if merged_continues else None

        page_articles = [parse_article(span, bold_reliable, known_words) for span in spans]
        articles.extend(page_articles)
        for span in spans:
            candidate_outcomes.append(
                {
                    "candidate_id": candidate_id(span["candidate"]),
                    "page": span["candidate"]["page"],
                    "column": span["candidate"]["column"],
                    "index": span["candidate"]["index"],
                    "word_guess": span["candidate"].get("word_guess"),
                    "outcome": "own-article",
                }
            )
        if spans and spans[-1]["continues_next_page"]:
            carry = {"candidate": spans[-1]["candidate"], "tokens": spans[-1]["tokens"]}
        print(f"page {page_number}: {len(page_articles)} draft articles")

    with out_path.open("w", encoding="utf-8") as fh:
        for article in articles:
            fh.write(json.dumps(article, ensure_ascii=False) + "\n")
    print(f"wrote {len(articles)} draft articles to {out_path}")

    outcomes_path = Path(args.outcomes)
    with outcomes_path.open("w", encoding="utf-8") as fh:
        for row in candidate_outcomes:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    own_article = sum(1 for r in candidate_outcomes if r["outcome"] == "own-article")
    merged = len(candidate_outcomes) - own_article
    print(
        f"wrote {len(candidate_outcomes)} candidate outcomes to {outcomes_path} "
        f"({own_article} own-article, {merged} merged-into-carry)"
    )
    if own_article != len(articles):
        print(
            f"ACCOUNTING MISMATCH: {own_article} own-article outcomes but {len(articles)} draft articles"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
