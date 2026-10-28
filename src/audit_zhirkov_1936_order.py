#!/usr/bin/env python3
"""Report adjacent order inversions in the 1936 OCR, without sorting or editing it.

The 39-letter order follows the book's alphabet (scan 5 and scan 147).
Collation aliases accommodate OCR renderings of historical letters; they do
not change source spelling. A warning is a candidate, not a proposed correction:
OCR often collapses distinct letters to q/s/z, and the print has exceptions.
"""

import argparse
import json
from collections import Counter
from pathlib import Path
import re
import unicodedata

try:
    from .parse_zhirkov_1936 import ROOT, articles
except ImportError:
    from parse_zhirkov_1936 import ROOT, articles

ALPHABET = "a b c ç d e f g ƣ h ħ ḩ i j k ķ l ļ ł m n o p q ꝗ r s ꞩ ş t ţ u v x x̨ x̵ z ƶ ⱬ".split()
ALIASES = {
    "ơ": "ƣ", "ḳ": "ķ", "ⱪ": "ķ", "ƙ": "ķ", "k̇": "ķ",
    "ḥ": "ḩ", "ḥ": "ḩ", "ḷ": "ļ", "ɫ": "ļ", "ɬ": "ļ",
    "ț": "ţ", "ṭ": "ţ", "ṯ": "ţ", "ț": "ţ",
    "x̌": "x̵", "x̦": "x̨", "χ": "x̵",
    "z̦": "ⱬ", "z̧": "ⱬ", "z̨": "ⱬ", "ʐ": "ⱬ",
    "q̵": "ꝗ", "s̵": "ꞩ", "z̵": "ƶ",
    "а": "a", "с": "c", "х": "x", "і": "i", "ј": "j",
}
RANK = {unicodedata.normalize("NFD", c): i for i, c in enumerate(ALPHABET)}
ALIASES = {unicodedata.normalize("NFD", a): unicodedata.normalize("NFD", b) for a, b in ALIASES.items()}


def units(word):
    result = []
    for c in unicodedata.normalize("NFD", word.lower()):
        if unicodedata.combining(c):
            if c not in ("\u0301", "\u0300") and result:
                result[-1] += c
        elif c.isalpha() or c.isdigit():
            result.append(c)
    return [ALIASES.get(c, c) for c in result]


def sort_key(word):
    # Unknown letters have deterministic keys but also appear in the report.
    return tuple((RANK[c], "") if c in RANK else (1000, c) for c in units(word))


def variants(word):
    """Both readings of optional letters can explain a printed placement."""
    match = re.search(r"\(([^()]*)\)", word)
    if not match:
        return [word]
    prefix, suffix = word[:match.start()], word[match.end():]
    return [v for replacement in ("", match[1]) for v in variants(prefix + replacement + suffix)]


def inversion(previous, current):
    return all(sort_key(a) > sort_key(b) for a in variants(previous) for b in variants(current))


def audit(source_articles):
    return [i for i in range(1, len(source_articles))
            if inversion(source_articles[i - 1]["word"], source_articles[i]["word"])]


def report(source_articles, indices):
    decisions_path = ROOT / "review/av-ru.1936-order-reviewed.json"
    decisions = json.loads(decisions_path.read_text(encoding="utf-8")) if decisions_path.exists() else []
    printed = {(d["scan"], d["previous"], d["current"]) for d in decisions if d["status"] == "printed_order"}
    def checked(i):
        return (source_articles[i]["page"], source_articles[i - 1]["word"], source_articles[i]["word"]) in printed
    checked_count = sum(checked(i) for i in indices)
    unknown = Counter(c for a in source_articles for c in units(a["word"]) if c not in RANK)
    lines = ["# av-ru.1936: проверка алфавитного порядка", "",
             f"Статей: {len(source_articles)}. Подозрительных соседних пар: {len(indices)}.", "",
             f"У {checked_count} пар порядок подтверждён по печати; остальные {len(indices) - checked_count} требуют сверки. "
             "Решения хранятся в `review/av-ru.1936-order-reviewed.json`; совпадение проверяется по скану и обоим заголовкам.", "",
             "Порядок 39 букв взят со сканов 5 и 147. Апострофы, дефисы, регистр и ударения игнорируются; "
             "удвоенные согласные сортируются как две буквы. Для внутрисловных скобок проверяются обе формы.", "",
             "Это кандидаты для сверки, а не список готовых замен. Разные исторические буквы нередко "
             "распознаны одинаково (q, s, z); встречаются печатные перестановки, отсылки и повреждённые "
             "границы статей. Пересортировывать исходник для устранения предупреждений нельзя.", "",
             "Воспроизведение: `python3 src/audit_zhirkov_1936_order.py --report review/av-ru.1936-order.md`.", "",
             "## Графемы вне алфавита и диагностических эквивалентов", "",
             ", ".join(f"`{unicodedata.normalize('NFC', c)}` × {n}" for c, n in unknown.most_common()) or "Нет.", "",
             "## Соседние пары", "",
             "Номер — текущая строка JSONL; скан — физическая страница PDF.", "",
             "| Строка | Скан | Предыдущее слово | Текущее слово | Следующее слово | Проверка |",
             "|---:|---:|---|---|---|---|"]
    for i in indices:
        previous, current = source_articles[i - 1], source_articles[i]
        following = source_articles[i + 1]["word"] if i + 1 < len(source_articles) else ""
        values = [previous["word"], current["word"], following]
        values = [v.replace("|", "\\|") for v in values]
        status = 'Печатный порядок подтверждён' if checked(i) else 'Требует сверки'
        lines.append(f"| {i + 1} | {current['page']} | {' | '.join(values)} | {status} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    source_articles = articles((ROOT / "books/av-ru.1936/av-ru.1936.html").read_text(encoding="utf-8"))
    indices = audit(source_articles)
    if args.report:
        args.report.write_text(report(source_articles, indices), encoding="utf-8")
    print(f"{len(source_articles)} articles; {len(indices)} candidate inversions")
