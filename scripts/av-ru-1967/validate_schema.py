#!/usr/bin/env python3
"""Validate every line of a JSONL file against schemas/av-ru.schema.json.

Exits non-zero if any line fails validation, is not valid JSON, or the file
contains duplicate lines (byte-identical repeats — a red flag for a
build/dedup bug, not a legitimate homonym pair, which always differs by at
least `homonym`). Also flags a handful of other checks the manual review
process (av-ru-1967-review-2026-09-17.md, "P0. Committed JSONL...") relied
on being run ad hoc: stray soft hyphens (U+00AD), examples with an empty
`av`/`ru`, and `see_also` self-loops (`target == word`).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/av-ru.1967.jsonl")
    parser.add_argument("--schema", default="schemas/av-ru.schema.json")
    args = parser.parse_args()

    schema = json.load(open(args.schema, encoding="utf-8"))
    validator = Draft202012Validator(schema)

    total = 0
    schema_violations = 0
    soft_hyphens = 0
    empty_examples = 0
    self_loops = 0
    seen_lines: dict[str, int] = {}
    duplicate_lines = 0

    for lineno, line in enumerate(open(args.input, encoding="utf-8"), start=1):
        total += 1
        if line in seen_lines:
            duplicate_lines += 1
        else:
            seen_lines[line] = lineno

        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            schema_violations += 1
            print(f"line {lineno}: invalid JSON: {exc}")
            continue

        errors = list(validator.iter_errors(obj))
        if errors:
            schema_violations += 1
            print(f"line {lineno} ({obj.get('word')!r}): {errors[0].message}")

        if "\u00ad" in line:
            soft_hyphens += 1
            print(f"line {lineno} ({obj.get('word')!r}): stray U+00AD soft hyphen")

        for sense in obj.get("senses", []):
            for ex in sense.get("examples", []):
                if not (ex.get("av") or "").strip() or not (ex.get("ru") or "").strip():
                    empty_examples += 1
                    print(f"line {lineno} ({obj.get('word')!r}): empty av/ru example")

        for sa in obj.get("see_also", []):
            if sa.get("target") == obj.get("word"):
                self_loops += 1
                print(f"line {lineno} ({obj.get('word')!r}): see_also self-loop")

    print(
        f"{total} lines checked: {schema_violations} schema violations, "
        f"{duplicate_lines} duplicate lines, {soft_hyphens} soft hyphens, "
        f"{empty_examples} empty av/ru examples, {self_loops} self-loops"
    )

    failed = schema_violations or duplicate_lines or soft_hyphens or empty_examples or self_loops
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
