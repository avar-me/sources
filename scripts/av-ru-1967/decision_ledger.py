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
      "decision": "accepted | rejected | corrected | allowlisted",
      "category": "short machine-checkable label",
      "reason": "human-readable justification",
      "reviewer": "who/what made the decision",
      "reviewed_at": "ISO date",
      "evidence": {...freeform, e.g. {"page": 551, "pages": [550, 551, 552]}},
      "expected_entry": {...} | null
    }

`source_hash` is deliberately a hash of a handful of plain strings (not a
whole entry blob) — cheap to recompute anywhere, and stable across runs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_LEDGER_PATH = Path("data/av-ru.1967.decisions.jsonl")


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
