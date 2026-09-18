#!/usr/bin/env python3
"""Persistent, committed decision ledger.

av-ru-1967-review-batch-3-2026-09-17.md, "P0. Создать persistent decision
ledger": review/triage decisions (which order-regression pairs are known
lexicographic artifacts, which oversized spans are legitimate big entries,
which zero-candidate pages are confirmed carries, etc.) must live in a
committed, reproducible repository artifact — not in `/memories`, `tmp/`,
or chat history, where no other contributor, CI run, or future session can
see or verify them.

Row schema (one JSON object per line, `data/av-ru.1967.decisions.jsonl`):

    {
      "id": "stable string identifying the reviewed thing",
      "source_hash": "short hash of the exact source facts the decision
          was based on — if those facts change, the hash won't match
          anymore and the decision is a CONFLICT, not silently reused",
      "decision": "allowlisted | corrected | rejected | needs_manual_fix |
          accepted_after_human_review",
      "category": "short machine-checkable label",
      "reason": "human-readable justification",
      "reviewer": "who/what made the decision",
      "reviewed_at": "ISO date",
      "evidence": {...freeform, e.g. {"page": 551, "pages": [550, 551, 552]}},
      "expected_entry": {...} | null
    }

av-ru-1967-review-batch-4-2026-09-17.md, "2. Исправить семантику decision
ledger": `decision` values are NOT interchangeable —
- `allowlisted`: the data IS correct; only a diagnostic heuristic fires on
  it (a genuine sort-key/tokenizer artifact, a source formatting choice, a
  verified-correct large entry or carry). Never use this for something
  that's actually wrong.
- `corrected`: the parser/data has ALREADY been fixed and `expected_entry`
  records what changed.
- `rejected`: the candidate isn't a real article at all (should not be
  accepted/published).
- `needs_manual_fix`: a real error is CONFIRMED but not yet fixed — this
  must NOT be treated as a closed/resolved finding by any consumer (see
  check_order.py's `confirmed_category` logic — a `needs_manual_fix` match
  still counts as an open regression, just with the root cause already
  diagnosed).
- `accepted_after_human_review`: a genuine human (not this agent) reviewed
  the scan and the resulting entry and signed off.

Every row's `reviewer` must honestly reflect whether it was an automated
agent or a real person — this project's decisions so far are all
"automated-agent-review", never fabricated as human sign-off.

`source_hash` is deliberately a hash of a handful of plain strings (not a
whole entry blob) — cheap to recompute anywhere, and stable across runs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_LEDGER_PATH = Path("data/av-ru.1967.decisions.jsonl")

DECISION_VALUES = {
    "allowlisted",
    "corrected",
    "rejected",
    "needs_manual_fix",
    "accepted_after_human_review",
}
# Decisions that mean "this is genuinely fine, treat the diagnostic finding
# as resolved" — anything else (needs_manual_fix, rejected pending removal)
# must stay visible as an open item, not silently subtracted from a count.
RESOLVED_DECISIONS = {"allowlisted", "corrected", "accepted_after_human_review"}


def source_hash(*parts: str) -> str:
    """Stable short hash of the facts a decision was based on. Any change
    to these facts (e.g. a word gets re-parsed differently, a page gets
    reprocessed) changes the hash, which invalidates the decision instead
    of silently carrying it forward."""
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def load_decisions(path: Path = DEFAULT_LEDGER_PATH) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    decisions: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            decisions[row["id"]] = row
    return decisions


def check_decision(
    decisions: dict[str, dict[str, Any]], id_: str, current_hash: str
) -> tuple[str, dict[str, Any] | None]:
    """Returns (status, row):
    - "missing": no decision recorded for this id yet.
    - "valid": a decision exists and its source_hash matches — safe to use.
    - "conflict": a decision exists but the underlying facts changed since
      it was recorded (source_hash mismatch) — must NOT be silently
      reused; report it so a human re-reviews.
    """
    row = decisions.get(id_)
    if row is None:
        return "missing", None
    if row.get("source_hash") != current_hash:
        return "conflict", row
    return "valid", row


def order_regression_id(prev_word: str, next_word: str) -> str:
    return f"order-regression:{prev_word}->{next_word}"


def order_regression_hash(prev_word: str, next_word: str, prev_page: int, next_page: int) -> str:
    return source_hash(prev_word, next_word, str(prev_page), str(next_page))


def review_item_id(word: str, page: int, column: str, top: float) -> str:
    return f"review-item:{word}:{page}:{column}:{top}"


def review_item_hash(word: str, page: int, column: str, top: float, raw_text: str) -> str:
    return source_hash(word, str(page), str(column), str(top), raw_text)
