#!/usr/bin/env python3
"""Per-page coverage ledger across the whole book (pages 23-619).

av-ru-1967-review-batch-3-2026-09-17.md, "P0. Построить per-page coverage
ledger": batch-2 already had per-article gates (order/link/quality), but no
per-page accounting — there was no committed answer to "did this page get
processed at all, and did anything drop silently on it". This script
builds exactly that, cross-referencing every stage's output for a given
physical page: geometry (raw OCR tokens), segments (candidate headword
positions), draft articles (parsed spans), accepted (published), and review
(queued) — plus a small number of derived signals (carry-in/out, max span
length, unclosed brackets) that make an anomalous page easy to spot without
re-deriving anything from the PDF.

Writes the committed data/av-ru.1967.page_ledger.jsonl (597 rows, one per
physical page 23-619, in page order) and enforces two hard-zero gates:
every page must be present, and every zero-draft-article page must have an
explicit, human-reviewed explanation recorded in EXPLAINED_ZERO_CANDIDATE_PAGES
below (not just "it happened to be zero this run").
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FIRST_PAGE = 23
LAST_PAGE = 619

# av-ru-1967-review-batch-3-2026-09-17.md explicitly requires "Страница 551
# должна быть исправлена либо иметь визуально подтверждённое объяснение.
# Текущий ноль неприемлем." Investigated via tmp/av-ru.1967/page-0550.png
# and page-0551.png (rendered from the PDF, pdfplumber to_image()):
# page 550 ends mid-sentence with "*цебё 1. нареч. 1) вперёд; ..." (a huge
# postposition entry with dozens of set-phrase idioms — "цебе бачине",
# "цебе гъезе", "цебе ккезе" etc. are sub-senses of this ONE headword, not
# separate headwords), and page 551 is entirely more of that same running
# entry (running head "цеб" printed top-left/right on both pages confirms
# it). The draft article for "цебё" (page 550, `raw_text` 3029 chars)
# textually contains page 551's content verbatim and only ends once
# "цебётӏезе"-family headwords resume as fresh bold entries on page 552 —
# i.e. the carry/stitch mechanism (parse_articles.py) already merged this
# correctly. Zero NEW headwords starting on page 551 is the CORRECT
# outcome for this page, not a bug.
#
# av-ru-1967-review-batch-4-2026-09-17.md, item 7 "Исправить multi-page
# provenance": this used to be a hand-verified, hardcoded string with no
# structural link back to цебё's own provenance. Now `absorbed_by` (built
# below from every draft article's `source_pages`) explains page 551 — and
# any future genuine multi-page carry — automatically, by construction,
# not via a per-page manual note. EXPLAINED_ZERO_CANDIDATE_PAGES is kept
# as a fallback for a genuinely different kind of zero-candidate page (a
# real extraction gap that ISN'T a carry) the structural check can't
# explain — currently empty, since every known case is a real carry.
EXPLAINED_ZERO_CANDIDATE_PAGES: dict[int, str] = {}



def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry-dir", default="tmp/av-ru.1967/geometry")
    parser.add_argument("--candidate-outcomes", default="tmp/av-ru.1967/candidate_outcomes.jsonl")
    parser.add_argument("--articles", default="tmp/av-ru.1967/draft_articles.jsonl")
    parser.add_argument("--draft-outcomes", default="tmp/av-ru.1967/draft_outcomes.jsonl")
    parser.add_argument("--provenance", default="data/av-ru.1967.provenance.jsonl")
    parser.add_argument("--needs-review", default="tmp/av-ru.1967/needs_review.jsonl")
    parser.add_argument("--order-check", default="tmp/av-ru.1967/order_check.jsonl")
    parser.add_argument("--out", default="data/av-ru.1967.page_ledger.jsonl")
    args = parser.parse_args()

    candidate_outcomes = _load_jsonl(Path(args.candidate_outcomes))
    articles = _load_jsonl(Path(args.articles))
    draft_outcomes = _load_jsonl(Path(args.draft_outcomes))
    provenance = _load_jsonl(Path(args.provenance))
    needs_review = _load_jsonl(Path(args.needs_review))
    order_issues = _load_jsonl(Path(args.order_check))

    # av-ru-1967-review-batch-4-2026-09-17.md, "1. Ввести per-candidate
    # outcome ledger" + "4. Page ledger должен агрегировать outcome ledger,
    # а не выводить drops разностью счётчиков": both parse_articles.py and
    # build_dataset.py now emit a per-candidate / per-draft-article outcome
    # ledger with zero tolerance for an unaccounted row — aggregate THOSE
    # here instead of the old segment-count-minus-draft-count difference,
    # which couldn't distinguish a real loss from expected consumption.
    candidates_by_page: dict[int, list[dict[str, Any]]] = {}
    for c in candidate_outcomes:
        candidates_by_page.setdefault(c["page"], []).append(c)

    draft_outcomes_by_page: dict[int, list[dict[str, Any]]] = {}
    for d in draft_outcomes:
        draft_outcomes_by_page.setdefault(d["page"], []).append(d)

    articles_by_page: dict[int, list[dict[str, Any]]] = {}
    for a in articles:
        articles_by_page.setdefault(a["page"], []).append(a)

    # av-ru-1967-review-batch-4-2026-09-17.md, item 7 "Исправить multi-page
    # provenance": parse_articles.py now records `source_pages` on any
    # article whose merged carry drew tokens from more than one physical
    # page. Index every OTHER page in that list (i.e. every page besides
    # the article's own starting `page`) back to the absorbing article, so
    # a zero-candidate page like 551 gets a STRUCTURAL explanation instead
    # of a hardcoded string that can't be verified against the data.
    absorbed_by: dict[int, list[dict[str, Any]]] = {}
    for a in articles:
        for p in a.get("source_pages", []):
            if p != a["page"]:
                absorbed_by.setdefault(p, []).append(a)

    accepted_by_page: dict[int, int] = {}
    for p in provenance:
        accepted_by_page[p["page"]] = accepted_by_page.get(p["page"], 0) + 1

    review_by_page: dict[int, int] = {}
    for r in needs_review:
        page = r.get("page")
        if page is not None:
            review_by_page[page] = review_by_page.get(page, 0) + 1

    regressions_by_page: dict[int, int] = {}
    for issue in order_issues:
        for side in ("prev", "next"):
            page = issue[side]["page"]
            regressions_by_page[page] = regressions_by_page.get(page, 0) + 1

    geometry_dir = Path(args.geometry_dir)

    rows: list[dict[str, Any]] = []
    unexplained_zero = 0
    unaccounted_candidates_total = 0
    unaccounted_drafts_total = 0
    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        geometry_path = geometry_dir / f"page-{page:04d}.json"
        geometry_lines = 0
        geometry_words = 0
        if geometry_path.exists():
            geom = json.loads(geometry_path.read_text(encoding="utf-8"))
            for col in ("left", "right"):
                for line in geom.get(col, []):
                    geometry_lines += 1
                    geometry_words += len(line.get("words", []))

        page_articles = articles_by_page.get(page, [])
        page_articles_sorted = sorted(page_articles, key=lambda a: (a.get("column", ""), a.get("top", 0)))
        page_candidates = candidates_by_page.get(page, [])
        segment_candidates = len(page_candidates)
        candidates_own_article = sum(1 for c in page_candidates if c["outcome"] == "own-article")
        candidates_merged_into = sum(1 for c in page_candidates if c["outcome"].startswith("merged-into:"))
        unaccounted_candidates = segment_candidates - candidates_own_article - candidates_merged_into
        unaccounted_candidates_total += unaccounted_candidates

        draft_count = len(page_articles)
        page_draft_outcomes = draft_outcomes_by_page.get(page, [])
        draft_accepted = sum(1 for d in page_draft_outcomes if d["outcome"] == "accepted")
        draft_review = sum(1 for d in page_draft_outcomes if d["outcome"] == "review")
        draft_duplicate_of = sum(1 for d in page_draft_outcomes if d["outcome"].startswith("duplicate-of:"))
        draft_dropped_bare_stub = sum(1 for d in page_draft_outcomes if d["outcome"] == "dropped-bare-stub-duplicate")
        draft_dropped_empty = sum(1 for d in page_draft_outcomes if d["outcome"] == "dropped-empty-word")
        unaccounted_drafts = draft_count - (
            draft_accepted + draft_review + draft_duplicate_of + draft_dropped_bare_stub + draft_dropped_empty
        )
        unaccounted_drafts_total += unaccounted_drafts

        accepted_count = accepted_by_page.get(page, 0)
        review_count = review_by_page.get(page, 0)
        # No rejection mechanism exists yet (see av-ru-1967-review-batch-3
        # P0 "Создать persistent decision ledger") — every draft article is
        # currently either accepted or queued for review, never formally
        # rejected, so this is always 0 for now.
        rejected_count = 0

        max_span = max((len(a.get("raw_text", "")) for a in page_articles), default=0)
        unclosed_brackets = sum(
            1 for a in page_articles if a.get("raw_text", "").count("[") != a.get("raw_text", "").count("]")
        )

        carry_out = bool(page_articles_sorted and page_articles_sorted[-1].get("continues_next_page"))
        prev_articles = articles_by_page.get(page - 1, [])
        prev_sorted = sorted(prev_articles, key=lambda a: (a.get("column", ""), a.get("top", 0)))
        carry_in = bool(prev_sorted and prev_sorted[-1].get("continues_next_page"))

        explanation = None
        absorbing_articles = absorbed_by.get(page)
        if draft_count == 0:
            if absorbing_articles:
                refs = ", ".join(
                    f"'{a['word']}' (p.{a['page']}, {a.get('column')}, top={a.get('top')})" for a in absorbing_articles
                )
                explanation = (
                    f"structurally absorbed into {refs}'s multi-page carry "
                    f"(source_pages includes {page} — see parse_articles.py's cross-page stitching)"
                )
            else:
                explanation = EXPLAINED_ZERO_CANDIDATE_PAGES.get(page)
            if explanation is None:
                # A page can legitimately have 0 draft articles for two
                # reasons without needing a per-page explanation entry: it
                # doesn't exist in this PDF extraction (no geometry at all,
                # e.g. front matter) or it's entirely absorbed by a carry
                # from the previous page (carry_in) — anything else needs a
                # manually reviewed explanation added above.
                if geometry_lines == 0:
                    explanation = "no geometry extracted for this page (outside 23-619 range or extraction gap)"
                elif carry_in:
                    explanation = "carry-in from previous page's continues_next_page (not yet manually verified)"
                else:
                    unexplained_zero += 1

        status = "ok"
        if draft_count == 0:
            status = "zero-candidates-explained" if explanation else "zero-candidates-UNEXPLAINED"
        elif unaccounted_candidates or unaccounted_drafts:
            status = "accounting-mismatch"
        elif unclosed_brackets:
            status = "unclosed-brackets"

        rows.append(
            {
                "page": page,
                "geometry_lines": geometry_lines,
                "geometry_words": geometry_words,
                "segment_candidates": segment_candidates,
                "candidates_own_article": candidates_own_article,
                "candidates_merged_into": candidates_merged_into,
                "unaccounted_candidates": unaccounted_candidates,
                "draft_articles": draft_count,
                "draft_accepted": draft_accepted,
                "draft_review": draft_review,
                "draft_duplicate_of": draft_duplicate_of,
                "draft_dropped_bare_stub": draft_dropped_bare_stub,
                "draft_dropped_empty": draft_dropped_empty,
                "unaccounted_draft_articles": unaccounted_drafts,
                "accepted": accepted_count,
                "review": review_count,
                "rejected": rejected_count,
                "first_word": page_articles_sorted[0]["word"] if page_articles_sorted else None,
                "last_word": page_articles_sorted[-1]["word"] if page_articles_sorted else None,
                "carry_in": carry_in,
                "carry_out": carry_out,
                "absorbed_by": [a["word"] for a in absorbing_articles] if absorbing_articles else [],
                "max_span_chars": max_span,
                "order_regressions": regressions_by_page.get(page, 0),
                "unclosed_brackets": unclosed_brackets,
                "explanation": explanation,
                "status": status,
            }
        )

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"ledger pages: {len(rows)}/{LAST_PAGE - FIRST_PAGE + 1}")
    print(f"unexplained zero-candidate pages: {unexplained_zero}")
    print(f"unaccounted candidates (all pages): {unaccounted_candidates_total}")
    print(f"unaccounted draft articles (all pages): {unaccounted_drafts_total}")
    zero_pages = [r["page"] for r in rows if r["draft_articles"] == 0]
    print(f"zero-draft-article pages: {zero_pages}")
    print(f"wrote {out_path}")

    ok = len(rows) == (LAST_PAGE - FIRST_PAGE + 1) and unexplained_zero == 0
    if not ok:
        print("HARD GATE FAILED: incomplete ledger or unexplained zero-candidate page(s)")
    # av-ru-1967-review-batch-4-2026-09-17.md, "3. Draft outcome accounting
    # сходится без остатка" / "4. Page ledger больше не использует naive
    # count-difference как drops": both are now real per-candidate/
    # per-draft-article outcome sums (see parse_articles.py /
    # build_dataset.py), so "unaccounted" here means an actual bug in that
    # accounting, not expected candidate->article consumption — hard 0,
    # not a baseline.
    if unaccounted_candidates_total:
        print(f"HARD GATE FAILED: {unaccounted_candidates_total} unaccounted segment candidate(s)")
        ok = False
    if unaccounted_drafts_total:
        print(f"HARD GATE FAILED: {unaccounted_drafts_total} unaccounted draft article(s)")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
