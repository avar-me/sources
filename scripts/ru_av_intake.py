#!/usr/bin/env python3
"""Validate and compare ru-av JSONL revisions using only the standard library."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable


ENTRY_KEYS = {
    "word", "stress", "homonym", "stem", "forms", "labels", "precomment",
    "exclamation", "senses", "see_also",
}
SENSE_KEYS = {
    "text", "precomment", "labels", "forms", "genitivefrom", "dativefrom",
    "locativefrom", "pluralfor", "refwordnum", "comment", "comment_lang", "examples",
}
EXAMPLE_KEYS = {"av", "ru", "labels", "comment", "comment_lang"}
SEE_ALSO_KEYS = {"target", "kind", "refwordnum", "comment", "comment_lang"}
STRING_ARRAY_KEYS = {"forms", "labels"}
REFERENCE_KEYS = {"genitivefrom", "dativefrom", "locativefrom", "pluralfor"}
RUSSIAN_VOWELS = set("аеёиоуыэюяАЕЁИОУЫЭЮЯ")


class IntakeError(Exception):
    pass


def canonical(entry: dict[str, Any]) -> str:
    return json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        source = path.open("r", encoding="utf-8")
    except OSError as exc:
        raise IntakeError(f"cannot open {path}: {exc}") from exc
    with source:
        for line_number, raw in enumerate(source, 1):
            if not raw.strip():
                errors.append(f"line {line_number}: blank JSONL line")
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc.msg} at column {exc.colno}")
                continue
            if not isinstance(value, dict):
                errors.append(f"line {line_number}: entry must be an object")
                continue
            rows.append(value)
    return rows, errors


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def validate_string_array(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: expected a non-empty array")
        return
    for index, item in enumerate(value):
        if not nonempty_string(item):
            errors.append(f"{path}[{index}]: expected a non-empty string")


def reject_unknown(obj: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in sorted(set(obj) - allowed):
        errors.append(f"{path}.{key}: unknown field")


def validate_example(example: Any, path: str, errors: list[str]) -> None:
    if not isinstance(example, dict) or not example:
        errors.append(f"{path}: expected a non-empty object")
        return
    reject_unknown(example, EXAMPLE_KEYS, path, errors)
    if "av" not in example and "ru" not in example:
        errors.append(f"{path}: at least one of av or ru is required")
    for key in ("av", "ru", "comment"):
        if key in example and not nonempty_string(example[key]):
            errors.append(f"{path}.{key}: expected a non-empty string")
    if "labels" in example:
        validate_string_array(example["labels"], f"{path}.labels", errors)
    validate_comment_language(example, path, errors)


def validate_sense(sense: Any, path: str, errors: list[str]) -> None:
    if not isinstance(sense, dict) or not sense:
        errors.append(f"{path}: expected a non-empty object")
        return
    reject_unknown(sense, SENSE_KEYS, path, errors)
    for key in ("text", "precomment", "comment", "refwordnum", *REFERENCE_KEYS):
        if key in sense and not nonempty_string(sense[key]):
            errors.append(f"{path}.{key}: expected a non-empty string")
    for key in STRING_ARRAY_KEYS:
        if key in sense:
            validate_string_array(sense[key], f"{path}.{key}", errors)
    if "examples" in sense:
        examples = sense["examples"]
        if not isinstance(examples, list) or not examples:
            errors.append(f"{path}.examples: expected a non-empty array")
        elif isinstance(examples, list):
            for index, example in enumerate(examples):
                validate_example(example, f"{path}.examples[{index}]", errors)
    validate_comment_language(sense, path, errors)


def validate_see_also(link: Any, path: str, errors: list[str]) -> None:
    if not isinstance(link, dict) or not link:
        errors.append(f"{path}: expected a non-empty object")
        return
    reject_unknown(link, SEE_ALSO_KEYS, path, errors)
    for key in ("target", "kind"):
        if key not in link:
            errors.append(f"{path}.{key}: required field is missing")
    for key in ("target", "refwordnum", "comment"):
        if key in link and not nonempty_string(link[key]):
            errors.append(f"{path}.{key}: expected a non-empty string")
    if link.get("kind") not in {"see", "from"}:
        errors.append(f"{path}.kind: expected see or from")
    validate_comment_language(link, path, errors)


def validate_comment_language(obj: dict[str, Any], path: str, errors: list[str]) -> None:
    if "comment_lang" not in obj:
        return
    if "comment" not in obj:
        errors.append(f"{path}.comment_lang: comment is required")
    if obj["comment_lang"] != "ru":
        errors.append(f"{path}.comment_lang: expected ru")


def validate_entry(entry: dict[str, Any], line_number: int, errors: list[str], warnings: list[str]) -> None:
    path = f"line {line_number}"
    reject_unknown(entry, ENTRY_KEYS, path, errors)
    for key in ("word", "forms"):
        if key not in entry:
            errors.append(f"{path}.{key}: required field is missing")
    if "word" in entry and not nonempty_string(entry["word"]):
        errors.append(f"{path}.word: expected a non-empty string")
    for key in ("stem", "precomment", "exclamation"):
        if key in entry and not nonempty_string(entry[key]):
            errors.append(f"{path}.{key}: expected a non-empty string")
    for key in STRING_ARRAY_KEYS:
        if key in entry:
            validate_string_array(entry[key], f"{path}.{key}", errors)
    for key in ("stress", "homonym"):
        if key in entry and (not isinstance(entry[key], int) or isinstance(entry[key], bool) or entry[key] < 1):
            errors.append(f"{path}.{key}: expected an integer >= 1")
    if "stress" in entry and nonempty_string(entry.get("word")):
        position = entry["stress"]
        word = entry["word"]
        if isinstance(position, int) and not isinstance(position, bool):
            if position > len(word):
                warnings.append(f"{path}.stress: {position} is outside word of length {len(word)}")
            elif word[position - 1] not in RUSSIAN_VOWELS:
                warnings.append(f"{path}.stress: position {position} points to {word[position - 1]!r}, not a Russian vowel")
    if "forms" in entry and isinstance(entry["forms"], list) and nonempty_string(entry.get("word")):
        if entry["word"] not in entry["forms"]:
            errors.append(f"{path}.forms: word is not present in forms")
    for key, validator in (("senses", validate_sense), ("see_also", validate_see_also)):
        if key not in entry:
            continue
        values = entry[key]
        if not isinstance(values, list) or not values:
            errors.append(f"{path}.{key}: expected a non-empty array")
            continue
        for index, value in enumerate(values):
            validator(value, f"{path}.{key}[{index}]", errors)


def validate_rows(rows: list[dict[str, Any]], parse_errors: Iterable[str] = ()) -> tuple[list[str], list[str]]:
    errors = list(parse_errors)
    warnings: list[str] = []
    for line_number, entry in enumerate(rows, 1):
        validate_entry(entry, line_number, errors, warnings)
    return errors, warnings


def count_nested(rows: list[dict[str, Any]], key: str) -> int:
    if key == "senses":
        return sum(len(entry.get("senses", [])) for entry in rows)
    if key == "examples":
        return sum(len(sense.get("examples", [])) for entry in rows for sense in entry.get("senses", []))
    if key == "see_also":
        return sum(len(entry.get("see_also", [])) for entry in rows)
    raise ValueError(key)


def metrics(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    key_counts = collections.Counter((entry["word"], entry.get("homonym")) for entry in rows)
    example_rows = [example for entry in rows for sense in entry.get("senses", []) for example in sense.get("examples", [])]
    invalid_stress = 0
    for entry in rows:
        if "stress" not in entry:
            continue
        position, word = entry["stress"], entry["word"]
        if position > len(word) or word[position - 1] not in RUSSIAN_VOWELS:
            invalid_stress += 1
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "entries": len(rows),
        "senses": count_nested(rows, "senses"),
        "examples": len(example_rows),
        "examples_without_av": sum("av" not in example for example in example_rows),
        "examples_without_ru": sum("ru" not in example for example in example_rows),
        "invalid_stress": invalid_stress,
        "see_also": count_nested(rows, "see_also"),
        "entries_without_senses_or_links": sum(not entry.get("senses") and not entry.get("see_also") for entry in rows),
        "duplicate_identity_groups": sum(count > 1 for count in key_counts.values()),
        "duplicate_identity_extra_rows": sum(count - 1 for count in key_counts.values() if count > 1),
        "top_level_fields": dict(sorted(collections.Counter(key for entry in rows for key in entry).items())),
    }


def match_revisions(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> dict[str, Any]:
    old_groups: dict[tuple[str, Any], list[dict[str, Any]]] = collections.defaultdict(list)
    new_groups: dict[tuple[str, Any], list[dict[str, Any]]] = collections.defaultdict(list)
    for entry in old:
        old_groups[(entry["word"], entry.get("homonym"))].append(entry)
    for entry in new:
        new_groups[(entry["word"], entry.get("homonym"))].append(entry)

    unchanged = changed = added = removed = 0
    changed_fields: collections.Counter[str] = collections.Counter()
    changed_samples: list[dict[str, Any]] = []
    added_samples: list[str] = []
    removed_samples: list[str] = []

    for identity in sorted(set(old_groups) | set(new_groups), key=lambda item: (item[0], item[1] or 0)):
        old_entries = old_groups.get(identity, [])
        new_entries = new_groups.get(identity, [])
        old_by_hash: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
        new_by_hash: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
        for entry in old_entries:
            old_by_hash[canonical(entry)].append(entry)
        for entry in new_entries:
            new_by_hash[canonical(entry)].append(entry)
        for fingerprint in set(old_by_hash) & set(new_by_hash):
            same = min(len(old_by_hash[fingerprint]), len(new_by_hash[fingerprint]))
            unchanged += same
            del old_by_hash[fingerprint][:same]
            del new_by_hash[fingerprint][:same]
        old_left = [entry for values in old_by_hash.values() for entry in values]
        new_left = [entry for values in new_by_hash.values() for entry in values]
        paired = min(len(old_left), len(new_left))
        changed += paired
        for old_entry, new_entry in zip(old_left[:paired], new_left[:paired]):
            fields = sorted({key for key in set(old_entry) | set(new_entry) if old_entry.get(key) != new_entry.get(key)})
            changed_fields.update(fields)
            if len(changed_samples) < 30:
                changed_samples.append({"word": identity[0], "homonym": identity[1], "fields": fields})
        remaining_old = old_left[paired:]
        remaining_new = new_left[paired:]
        removed += len(remaining_old)
        added += len(remaining_new)
        if len(removed_samples) < 30:
            removed_samples.extend(identity[0] for _ in remaining_old[:30 - len(removed_samples)])
        if len(added_samples) < 30:
            added_samples.extend(identity[0] for _ in remaining_new[:30 - len(added_samples)])
    return {
        "unchanged": unchanged,
        "changed": changed,
        "added": added,
        "removed": removed,
        "changed_top_level_fields": dict(sorted(changed_fields.items())),
        "changed_samples": changed_samples,
        "added_samples": added_samples,
        "removed_samples": removed_samples,
    }


def print_errors(errors: list[str], limit: int) -> None:
    for error in errors[:limit]:
        print(f"ERROR: {error}", file=sys.stderr)
    if len(errors) > limit:
        print(f"ERROR: ... and {len(errors) - limit} more", file=sys.stderr)


def print_warnings(warnings: list[str], limit: int) -> None:
    for warning in warnings[:limit]:
        print(f"WARNING: {warning}", file=sys.stderr)
    if len(warnings) > limit:
        print(f"WARNING: ... and {len(warnings) - limit} more", file=sys.stderr)


def validate_command(args: argparse.Namespace) -> int:
    path = Path(args.path)
    rows, parse_errors = load_jsonl(path)
    errors, warnings = validate_rows(rows, parse_errors)
    if errors:
        print_errors(errors, args.max_errors)
        print(f"INVALID: {path} ({len(errors)} errors)", file=sys.stderr)
        return 1
    if warnings:
        print_warnings(warnings, args.max_errors)
        if args.strict_content:
            print(f"INVALID CONTENT: {path} ({len(warnings)} warnings)", file=sys.stderr)
            return 1
    report = metrics(rows, path)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"VALID: {path}")
        for key in ("entries", "senses", "examples", "examples_without_av", "examples_without_ru", "invalid_stress", "see_also", "entries_without_senses_or_links", "duplicate_identity_groups"):
            print(f"{key}: {report[key]}")
        print(f"sha256: {report['sha256']}")
    return 0


def compare_command(args: argparse.Namespace) -> int:
    old_path, new_path = Path(args.old), Path(args.new)
    old_rows, old_parse = load_jsonl(old_path)
    new_rows, new_parse = load_jsonl(new_path)
    old_errors, old_warnings = validate_rows(old_rows, old_parse)
    new_errors, new_warnings = validate_rows(new_rows, new_parse)
    if old_errors or new_errors:
        if old_errors:
            print(f"Validation errors in {old_path}:", file=sys.stderr)
            print_errors(old_errors, args.max_errors)
        if new_errors:
            print(f"Validation errors in {new_path}:", file=sys.stderr)
            print_errors(new_errors, args.max_errors)
        return 1
    if old_warnings:
        print(f"Content warnings in {old_path}: {len(old_warnings)}", file=sys.stderr)
    if new_warnings:
        print(f"Content warnings in {new_path}: {len(new_warnings)}", file=sys.stderr)
    if args.strict_content and (old_warnings or new_warnings):
        return 1
    report = {
        "old": metrics(old_rows, old_path),
        "new": metrics(new_rows, new_path),
        "comparison": match_revisions(old_rows, new_rows),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"OLD: {old_path} ({report['old']['sha256']})")
        print(f"NEW: {new_path} ({report['new']['sha256']})")
        for key in ("entries", "senses", "examples", "examples_without_av", "examples_without_ru", "invalid_stress", "see_also", "duplicate_identity_groups"):
            old_value, new_value = report["old"][key], report["new"][key]
            print(f"{key}: {old_value} -> {new_value} ({new_value - old_value:+d})")
        comparison = report["comparison"]
        print(f"unchanged: {comparison['unchanged']}")
        print(f"changed: {comparison['changed']}")
        print(f"added: {comparison['added']}")
        print(f"removed: {comparison['removed']}")
        if comparison["changed_top_level_fields"]:
            fields = ", ".join(f"{key}={value}" for key, value in comparison["changed_top_level_fields"].items())
            print(f"changed_top_level_fields: {fields}")
        if comparison["added_samples"]:
            print("added_samples: " + ", ".join(comparison["added_samples"]))
        if comparison["removed_samples"]:
            print("removed_samples: " + ", ".join(comparison["removed_samples"]))
    return 2 if args.fail_on_removals and report["comparison"]["removed"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate one ru-av JSONL file")
    validate.add_argument("path")
    validate.add_argument("--json", action="store_true", help="print metrics as JSON")
    validate.add_argument("--strict-content", action="store_true", help="treat content warnings such as invalid stress as errors")
    validate.add_argument("--max-errors", type=int, default=50)
    validate.set_defaults(func=validate_command)

    compare = subparsers.add_parser("compare", help="validate and compare two ru-av JSONL revisions")
    compare.add_argument("old")
    compare.add_argument("new")
    compare.add_argument("--json", action="store_true", help="print the complete report as JSON")
    compare.add_argument("--strict-content", action="store_true", help="fail when either revision has content warnings")
    compare.add_argument("--fail-on-removals", action="store_true", help="exit 2 when entries were removed")
    compare.add_argument("--max-errors", type=int, default=50)
    compare.set_defaults(func=compare_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except IntakeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
