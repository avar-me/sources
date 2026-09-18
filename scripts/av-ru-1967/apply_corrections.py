#!/usr/bin/env python3
"""Apply automated-agent-proposed data corrections from
data/av-ru.1967.corrections.jsonl to build_dataset.py's automated output.

av-ru-1967-review-batch-4-2026-09-17.md, "4. Исправить конкретные известные
accepted errors": some accepted-file bugs are one-off, non-generalizable
mistakes (a mid-paragraph headword missed, an OCR "!"/palochka confusion
inherited from a removed segmentation heuristic, a false headword absorbed
from a neighboring gloss) that the automated pipeline can never safely fix
with a general rule without risking new regressions elsewhere. This is the
ONE place those specific, individually-authored corrections are applied.

av-ru-1967-review-batch-5-2026-09-18.md, P1 "Не называть automated
corrections hand-verified": every row here was proposed AND applied by an
automated agent, with full evidence (page, bbox, raw snippet,
`before_entries`/`expected_entry`) but with **no human review** -
`decision: "pending_human_signoff"` says exactly that, honestly, instead
of the earlier `"corrected"` (which this file's own docstring used to
call "hand-verified"/"individually-verified" - neither was true). Each
row also carries a `risk_class` (`glyph-only-rename` /
`punctuation-markup-repair` / `headword-removal-merge` /
`sense-example-reconstruction`) so a human reviewer can triage the
riskiest classes (semantic merges/reconstructions) first, and a
`human_signoff` field (`null` until an actual human reviews it - see
README.md for the intended review workflow).

Each correction is a decision_ledger-shaped row with a `source_hash`
tying it to the EXACT accepted content it was based on (`target_word` +
every `remove_words` entry, sorted and hashed) — if build_dataset.py's
output changes upstream (a real pipeline fix altering the same words),
the correction's hash no longer matches and it is NOT applied (reported
as a conflict) rather than silently reapplying a stale patch on top of
new content.

Runs as the LAST step of build_all.sh, after build_dataset.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from decision_ledger import source_hash  # noqa: E402


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _content_hash(words: list[str], entries_by_word: dict[str, list[dict]]) -> str:
    """Hash covering EVERY entry matching each word (not just one) — this
    dataset has 142 headwords with more than one entry (homonyms), so a
    naive one-entry-per-word lookup would silently ignore duplicates."""
    bits = []
    for w in sorted(set(words)):
        matches = entries_by_word.get(w)
        if matches:
            for e in sorted((json.dumps(m, ensure_ascii=False, sort_keys=True) for m in matches)):
                bits.append(e)
        else:
            bits.append(f"MISSING:{w}")
    return source_hash(*bits)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted", default="data/av-ru.1967.jsonl")
    parser.add_argument("--provenance", default="data/av-ru.1967.provenance.jsonl")
    parser.add_argument("--corrections", default="data/av-ru.1967.corrections.jsonl")
    args = parser.parse_args()

    accepted_path = Path(args.accepted)
    provenance_path = Path(args.provenance)
    accepted = _load_jsonl(accepted_path)
    provenance = _load_jsonl(provenance_path)
    # "corrected" is accepted too for backward compatibility with any
    # pre-batch-5 tooling/history that still uses the old name; new rows
    # should use "pending_human_signoff" (not yet reviewed by a human) or
    # "human_verified" (a real person has actually checked it) - both mean
    # "apply this", the distinction is about honesty, not whether it runs.
    APPLICABLE = {"pending_human_signoff", "human_verified", "corrected"}
    corrections = [c for c in _load_jsonl(Path(args.corrections)) if c.get("decision") in APPLICABLE]

    if len(accepted) != len(provenance):
        print(f"FATAL: {len(accepted)} accepted entries but {len(provenance)} provenance rows")
        return 1

    # Positional list, NOT a word-keyed dict — this dataset has 142
    # headwords with more than one entry (homonyms); collapsing by word
    # would silently drop 149 unrelated entries.
    pairs: list[tuple[dict[str, Any], dict[str, Any]] | None] = list(zip(accepted, provenance))
    entries_by_word: dict[str, list[dict[str, Any]]] = {}
    for e, _p in pairs:
        entries_by_word.setdefault(e["word"], []).append(e)

    applied = 0
    conflicts = 0
    insertions: list[tuple[int, dict[str, Any], dict[str, Any]]] = []  # (after_index, entry, prov)
    for corr in corrections:
        remove_words = corr.get("remove_words", [])
        target_word = corr["target_word"]
        expected_entry = corr.get("expected_entry")
        check_words = remove_words + [target_word]

        current_hash = _content_hash(check_words, entries_by_word)
        if current_hash != corr["source_hash"]:
            print(f"CORRECTION CONFLICT: {corr['id']} — accepted content no longer matches, NOT applied")
            conflicts += 1
            continue

        remove_set = set(remove_words)
        target_homonym = corr.get("target_homonym")
        target_content_hint = corr.get("target_content_hint")
        target_index = None
        removed_provenance: dict[str, dict[str, Any]] = {}
        for i, pair in enumerate(pairs):
            if pair is None:
                continue
            e, p = pair
            if e["word"] in remove_set:
                removed_provenance.setdefault(e["word"], p)
                pairs[i] = None
            elif e["word"] == target_word and target_index is None:
                if target_homonym is not None and e.get("homonym") != target_homonym:
                    continue
                if target_content_hint is not None and target_content_hint not in json.dumps(e, ensure_ascii=False):
                    continue
                target_index = i

        if expected_entry is None:
            if target_index is not None:
                pairs[target_index] = None
        elif target_index is not None:
            pairs[target_index] = (expected_entry, pairs[target_index][1])
        else:
            # Brand-new split-off entry (e.g. рёхи split from рехсей) —
            # queue an insertion right after its anchor; synthesize
            # provenance from the correction's own evidence since there's
            # no real segmentation position for it.
            #
            # A pure rename/OCR-fix (e.g. богбгӏуж -> богогӏуж) is NOT a
            # new entry, though — it's the SAME physical headword under a
            # corrected spelling, so it should inherit the removed
            # article's own real geometry (page/column/top/bbox) rather
            # than getting synthesized "manual-correction" provenance with
            # no bbox. `inherit_provenance_from` names which removed word's
            # provenance to reuse for this case.
            inherit_from = corr.get("inherit_provenance_from")
            inherited_prov = removed_provenance.get(inherit_from) if inherit_from else None
            anchor_word = corr.get("insert_after")
            anchor_index = len(pairs) - 1
            anchor_prov: dict[str, Any] = {}
            if anchor_word:
                for i, pair in enumerate(pairs):
                    if pair is not None and pair[0]["word"] == anchor_word:
                        anchor_index = i
                        anchor_prov = pair[1]
                        break
            if inherited_prov is not None:
                new_prov = {
                    **inherited_prov,
                    "word": target_word,
                    "confidence": "manual-correction",
                    "reasons": ["manual-correction"],
                    "selection_rule": "manual-correction",
                    "duplicate_group_spans_differ": False,
                    "duplicate_group": [],
                }
            else:
                new_prov = {
                    "word": target_word,
                    "page": corr.get("evidence", {}).get("page", anchor_prov.get("page")),
                    "column": anchor_prov.get("column"),
                    "top": anchor_prov.get("top"),
                    "confidence": "manual-correction",
                    "reasons": ["manual-correction"],
                    "raw_text_length": None,
                    "bbox": corr.get("evidence", {}).get("bbox", anchor_prov.get("bbox")),
                    "selection_rule": "manual-correction",
                    "duplicate_group_spans_differ": False,
                    "duplicate_group": [],
                }
            insertions.append((anchor_index, expected_entry, new_prov))
        applied += 1

    out_entries: list[dict[str, Any]] = []
    out_provenance: list[dict[str, Any]] = []
    inserts_by_index: dict[int, list[tuple[dict, dict]]] = {}
    for after_index, entry, prov in insertions:
        inserts_by_index.setdefault(after_index, []).append((entry, prov))

    for i, pair in enumerate(pairs):
        if pair is not None:
            out_entries.append(pair[0])
            out_provenance.append(pair[1])
        for entry, prov in inserts_by_index.get(i, []):
            out_entries.append(entry)
            out_provenance.append(prov)

    with accepted_path.open("w", encoding="utf-8") as fh:
        for e in out_entries:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    with provenance_path.open("w", encoding="utf-8") as fh:
        for p in out_provenance:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"applied {applied} correction(s), {conflicts} conflict(s)")
    print(f"accepted: {len(accepted)} -> {len(out_entries)} entries")
    if conflicts:
        print("HARD GATE FAILED: correction(s) could not be applied (stale source_hash)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
