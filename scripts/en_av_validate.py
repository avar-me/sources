#!/usr/bin/env python3
"""Structural checks for the English–Avar dictionary, not linguistic certification."""

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path


CYRILLIC = re.compile(r"[А-Яа-яЁёӀӏ]")
BAD_PALOCHKA = re.compile(r"(?<![тгкхцчТГКХЦЧ])[ӏӀ]")
RUSSIAN_LABELS = {
    "masculine gender", "feminine gender", "neuter gender",
    "perfective aspect", "imperfective aspect", "biaspectual", "semelfactive aspect",
}


def validate(path):
    errors = []
    counts = collections.Counter()
    seen = set()
    raw = path.read_bytes()
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        def error(message):
            errors.append(f"line {number}: {message}")

        try:
            article = json.loads(line)
        except ValueError as exc:
            error(str(exc))
            continue
        if not isinstance(article, dict):
            error("article must be an object")
            continue
        counts["entries"] += 1
        word = article.get("word")
        if not isinstance(word, str) or not word.strip() or CYRILLIC.search(word):
            error("word must be a non-empty English headword")
        if line != json.dumps(article, ensure_ascii=False):
            error("non-canonical spaced JSON serialization")
        fingerprint = json.dumps(article, sort_keys=True, ensure_ascii=False)
        if fingerprint in seen:
            error("exact duplicate article")
        seen.add(fingerprint)
        if article.get("stem") and CYRILLIC.search(str(article["stem"])):
            error("Russian stem")
        forms = article.get("forms", [])
        if not isinstance(forms, list) or any(not isinstance(x, str) or CYRILLIC.search(x) for x in forms):
            error("invalid or Russian forms")
        for link in article.get("see_also", []):
            if not isinstance(link, dict) or CYRILLIC.search(str(link.get("target", ""))):
                error("invalid or Russian link target")

        def inspect_labels(obj):
            labels = obj.get("labels", [])
            if not isinstance(labels, list) or any(not isinstance(x, str) for x in labels):
                error("labels must be strings")
            elif RUSSIAN_LABELS.intersection(labels):
                error("inherited Russian gender/aspect labels")

        inspect_labels(article)
        senses = article.get("senses", [])
        if not isinstance(senses, list) or not senses:
            error("missing senses")
            continue
        for sense in senses:
            counts["senses"] += 1
            if not isinstance(sense, dict) or not sense:
                error("empty or invalid sense")
                continue
            inspect_labels(sense)
            if "comment_lang" in sense:
                if sense["comment_lang"] not in {"en", "av", "ru"} or not sense.get("comment"):
                    error("invalid comment language or missing comment")
            examples = sense.get("examples", [])
            if not isinstance(examples, list):
                error("examples must be an array")
                continue
            for example in examples:
                counts["examples"] += 1
                if not isinstance(example, dict):
                    error("example must be an object")
                    continue
                en, av = example.get("en"), example.get("av")
                if not isinstance(en, str) or not en.strip() or not isinstance(av, str) or not av.strip():
                    error("example needs English and Avar sides")
                    continue
                if CYRILLIC.search(en):
                    error("Cyrillic in English example")
                if BAD_PALOCHKA.search(av):
                    error("palochka outside an allowed digraph")
                inspect_labels(example)
    return counts, errors, hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/en-av.jsonl"))
    args = parser.parse_args()
    counts, errors, sha256 = validate(args.path)
    for message in errors:
        print(message)
    print("INVALID" if errors else "VALID", args.path)
    print(json.dumps({**counts, "errors": len(errors), "sha256": sha256}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
