#!/usr/bin/env python3
"""Independent quality gate for the PUBLISHED file (data/av-ru.1967.jsonl),
as opposed to check_order.py/resolve_references.py which still (correctly)
diagnose the full draft. av-ru-1967-review-batch-3-2026-09-17.md, "P0.
Реализовать независимые gates для accepted/review/draft": `quality_scan.py`
returning 0 only proves internal consistency with the same heuristics that
built `accepted` in the first place — it is not an independent check that
the accepted set's own alphabetical order, headword language, span size,
duplicate/homonym shape, and see_also link targets are actually sound.

Reads:
- data/av-ru.1967.jsonl (accepted, in its committed file order — never
  re-sorted; the book is one continuous listing, so file order IS the
  thing being checked)
- data/av-ru.1967.provenance.jsonl (1:1, same order, page/column/top/
  duplicate-group per accepted entry — written by build_dataset.py)
- tmp/av-ru.1967/needs_review.jsonl (review-queue words, for see_also
  target categorization)

Writes tmp/av-ru.1967/accepted_check.jsonl (gitignored, regenerated every
build) and enforces baseline gates via baseline.py. Never edits
data/av-ru.1967.jsonl.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from build_site import AVAR_ALPHABET, make_rank, make_sort_key, make_tokenizer  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from baseline import check_metric, load_baselines  # noqa: E402
from build_dataset import RAW_MARKER_CHARS  # noqa: E402
from quality_scan import RUSSIAN_FUNCTION_WORDS, RUSSIAN_GRAMMAR_RE, has_avar_signal  # noqa: E402
from segment_entries import load_known_words  # noqa: E402


def _looks_ocr_invalid_target(target: str) -> bool:
    """A see_also/from target string that can't possibly be a real
    headword — a leftover raw structural marker character, or a bare
    digit/punctuation-only scrap. Distinct from "missing" (a plausible
    word that just isn't in accepted/review) — this is OCR noise that
    should never have become a target string at all."""
    if not target or not target.strip():
        return True
    if any(ch in target for ch in RAW_MARKER_CHARS):
        return True
    return not any(ch.isalpha() for ch in target)

_SORT_KEY = make_sort_key(make_rank(AVAR_ALPHABET), make_tokenizer("av"))

# Span-size threshold matches batch-3's own "spans > 1000 chars" framing
# (raw_text length of the *source draft article*, tracked in provenance as
# raw_text_length — not the serialized accepted JSON, which is always much
# shorter after schema conversion).
LONG_SPAN_CHARS = 1000


def _is_bare_or_fragment(entry: dict[str, Any]) -> bool:
    """True if the entry has no substantive gloss content at all — either
    a bare `{"word": ...}` stub, or every sense's `text`/examples are tiny
    fragments (a single stray preposition, an abbreviated cross-reference
    like 'ср.', a mid-sentence scrap). A genuine directly-borrowed Avar
    loanword entry (e.g. 'амбар', 'авантюра' — Step 29's self-gloss
    loanword pattern) always has at least a clean single-word gloss or a
    real example sentence; a segmentation artifact (a Russian gloss word
    that got mis-bolded into becoming its own headword) typically doesn't,
    because there was never a real Avar article there to begin with."""
    if set(entry.keys()) == {"word"}:
        return True
    for sense in entry.get("senses", []):
        text = (sense.get("text") or "").strip(" ,.;:")
        if len(text) > 2:
            return False
        for ex in sense.get("examples", []):
            av = (ex.get("av") or "").strip()
            ru = (ex.get("ru") or "").strip()
            if len(av) > 4 and len(ru) > 4:
                return False
    return True


def suspicious_headword_reason(word: str, entry: dict[str, Any], known_words: set[str], russian_lexicon: set[str]) -> str | None:
    """av-ru-1967-review-batch-3-2026-09-17.md, "P0. Исправить
    false-headword detection без бесконечного blacklist": the old check
    (RUSSIAN_GRAMMAR_RE suffix + a dozen hand-picked function words) misses
    ordinary Russian nouns/adjectives entirely (голова, ложка, конверт,
    девочки, ...). Real Avar/Russian homographs (е.g. "как") are protected
    by the `word not in known_words` gate on both checks. This is still a
    dictionary-based signal, not the full structural (layout/font/indent)
    classifier the review asks for — see report.md for that gap."""
    if has_avar_signal(word) or word in known_words:
        return None
    lowered = word.strip(",.;:!?").lower()
    if RUSSIAN_GRAMMAR_RE.search(word) or lowered in RUSSIAN_FUNCTION_WORDS:
        return "russian-grammar-or-function-word"
    if lowered in russian_lexicon and _is_bare_or_fragment(entry):
        return "matches-russian-lexicon-and-lacks-content"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted", default="data/av-ru.1967.jsonl")
    parser.add_argument("--provenance", default="data/av-ru.1967.provenance.jsonl")
    parser.add_argument("--needs-review", default="tmp/av-ru.1967/needs_review.jsonl")
    parser.add_argument("--av-ru", default="data/av-ru.jsonl")
    parser.add_argument("--ru-av", default="data/ru-av.jsonl")
    parser.add_argument("--out", default="tmp/av-ru.1967/accepted_check.jsonl")
    args = parser.parse_args()

    accepted = [json.loads(line) for line in Path(args.accepted).open("r", encoding="utf-8")]
    provenance = [json.loads(line) for line in Path(args.provenance).open("r", encoding="utf-8")]
    if len(accepted) != len(provenance):
        print(
            f"FATAL: {len(accepted)} accepted entries but {len(provenance)} provenance rows "
            "(build_dataset.py must emit exactly one provenance row per accepted entry)"
        )
        return 1

    known_words = load_known_words(Path(args.av_ru))
    russian_lexicon = load_known_words(Path(args.ru_av))

    review_words: set[str] = set()
    review_see_also: list[tuple[str, dict[str, str]]] = []
    review_path = Path(args.needs_review)
    if review_path.exists():
        with review_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                entry = row.get("entry", {})
                w = entry.get("word")
                if w:
                    review_words.add(w)
                    for ref in entry.get("see_also", []):
                        review_see_also.append((w, ref))

    accepted_words = {e["word"] for e in accepted}

    findings: dict[str, list[dict[str, Any]]] = {
        "order_regression": [],
        "suspicious_headword": [],
        "oversized_span": [],
        "missing_provenance": [],
        "link_to_missing": [],
    }

    # --- order regressions, computed directly on accepted's own file order,
    # no stress-glyph rescue: accepted is supposed to already be final, so a
    # regression here is either a real ordering bug or a headword that's
    # still wrong content — rescuing it away would hide exactly what this
    # gate exists to find. ---
    prev_word: str | None = None
    prev_key = None
    for e, p in zip(accepted, provenance):
        word = e["word"]
        key = _SORT_KEY(word)
        if prev_key is not None and key < prev_key:
            findings["order_regression"].append(
                {"prev": prev_word, "next": word, "page": p.get("page")}
            )
        prev_word, prev_key = word, key

    # --- suspicious headword language ---
    for e, p in zip(accepted, provenance):
        reason = suspicious_headword_reason(e["word"], e, known_words, russian_lexicon)
        if reason:
            findings["suspicious_headword"].append(
                {"word": e["word"], "page": p.get("page"), "reason": reason}
            )

    # --- oversized spans ---
    for e, p in zip(accepted, provenance):
        length = p.get("raw_text_length")
        if length and length > LONG_SPAN_CHARS:
            findings["oversized_span"].append(
                {"word": e["word"], "page": p.get("page"), "length": length}
            )

    # --- provenance completeness ---
    for e, p in zip(accepted, provenance):
        if p.get("page") is None or p.get("word") != e["word"]:
            findings["missing_provenance"].append({"word": e["word"]})

    # --- see_also link targets, split by both origin (accepted/review)
    # and destination (accepted/review/missing/ocr-invalid) — batch-3 P1
    # "Разделить links для accepted и полного draft" ---
    link_categories = {
        "accepted_to_accepted": 0,
        "accepted_to_review": 0,
        "accepted_to_missing": 0,
        "accepted_to_ocr_invalid": 0,
        "review_to_accepted": 0,
        "review_to_review": 0,
        "review_to_missing": 0,
        "review_to_ocr_invalid": 0,
    }

    def _categorize(origin: str, source_word: str, target: str) -> None:
        if _looks_ocr_invalid_target(target):
            link_categories[f"{origin}_to_ocr_invalid"] += 1
            return
        if target in accepted_words:
            link_categories[f"{origin}_to_accepted"] += 1
        elif target in review_words:
            link_categories[f"{origin}_to_review"] += 1
        else:
            link_categories[f"{origin}_to_missing"] += 1
            if origin == "accepted":
                findings["link_to_missing"].append({"word": source_word, "target": target})

    for e in accepted:
        for ref in e.get("see_also", []):
            target = ref.get("target")
            if target:
                _categorize("accepted", e["word"], target)
    for source_word, ref in review_see_also:
        target = ref.get("target")
        if target:
            _categorize("review", source_word, target)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for kind, rows in findings.items():
            for row in rows:
                fh.write(json.dumps({"kind": kind, **row}, ensure_ascii=False) + "\n")

    print(f"{len(accepted)} accepted entries checked")
    print(f"  order regressions: {len(findings['order_regression'])}")
    print(f"  suspicious headwords: {len(findings['suspicious_headword'])}")
    print(f"  oversized spans (> {LONG_SPAN_CHARS} chars): {len(findings['oversized_span'])}")
    print(f"  entries missing provenance: {len(findings['missing_provenance'])}")
    print(
        f"  see_also links (accepted origin): {link_categories['accepted_to_accepted']} accepted, "
        f"{link_categories['accepted_to_review']} review, {link_categories['accepted_to_missing']} missing, "
        f"{link_categories['accepted_to_ocr_invalid']} ocr-invalid"
    )
    print(
        f"  see_also links (review origin): {link_categories['review_to_accepted']} accepted, "
        f"{link_categories['review_to_review']} review, {link_categories['review_to_missing']} missing, "
        f"{link_categories['review_to_ocr_invalid']} ocr-invalid"
    )
    print(f"wrote {out_path}")

    baselines = load_baselines()
    ok = True
    ok &= check_metric("check_accepted.order_regressions", len(findings["order_regression"]), baselines)
    ok &= check_metric("check_accepted.suspicious_headwords", len(findings["suspicious_headword"]), baselines)
    ok &= check_metric("check_accepted.oversized_spans", len(findings["oversized_span"]), baselines)
    # Hard zero, not a baseline: every accepted entry MUST have a
    # provenance row by construction (build_dataset.py writes them 1:1) —
    # any drift here is a pipeline bug, not a content-quality backlog item.
    if findings["missing_provenance"]:
        print(f"HARD GATE FAILED: {len(findings['missing_provenance'])} accepted entries without provenance")
        ok = False
    ok &= check_metric("check_accepted.links_missing", link_categories["accepted_to_missing"], baselines)
    ok &= check_metric("check_accepted.review_links_missing", link_categories["review_to_missing"], baselines)
    ok &= check_metric("check_accepted.accepted_links_ocr_invalid", link_categories["accepted_to_ocr_invalid"], baselines)
    ok &= check_metric("check_accepted.review_links_ocr_invalid", link_categories["review_to_ocr_invalid"], baselines)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
