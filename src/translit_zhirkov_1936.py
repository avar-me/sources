#!/usr/bin/env python3
"""Transliterate the Zhirkov 1936 dictionary from its Latin orthography
(`data/av-ru.1936.latin.jsonl`) into modern Avar Cyrillic (`data/av-ru.1936.jsonl`).

Canonical letter table: `../dev/transliteration-ambiguity-report.md`
(vetted against a native speaker, 2026-10-28), cross-checked here against
modern av-ru.jsonl headwords where a cognate exists (e.g. bişşize ==
бищизе "выбирать", confirming the şş -> щ geminate rule).

Only the Avar-language fields are converted: word, forms, spelling_forms,
gender_forms, senses[].forms, senses[].examples[].av, see_also[].target.
Russian prose (text, labels, comment, precomment, examples[].ru,
see_also[].comment) is left untouched, including rare Latin-script
citations of the original spelling inside Russian comments -- those still
reference the book's own typography and are a separate, follow-up concern.

The source data has already been normalized to the clean 39-letter
alphabet (see `audit_zhirkov_1936_alphabet.py`, 0 anomalies) and to
integer stress positions (`stress`, `form_stresses`,
`spelling_form_stresses`, `gender_form_stresses`) with no inline
accents left in any Avar field -- so this module does not need to
handle OCR-variant glyphs or combining accents inline; it only
remaps those integer stress positions across the change in character
count caused by digraphs (x -> х is 1:1, but q -> къ is 1:2, etc).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "av-ru.1936"

# Longest-key-first greedy matching; order in the dict does not matter,
# see _keys(). Geminate "şş" must win over two separate "ş" matches.
MAPPING: dict[str, str] = {
    "a": "а", "b": "б", "c": "ч", "d": "д", "e": "е", "f": "ф", "g": "г",
    "h": "гь", "i": "и", "j": "й", "k": "к", "l": "л", "m": "м", "n": "н",
    "o": "о", "p": "п", "q": "къ", "r": "р", "s": "с", "t": "т", "u": "у",
    "v": "в", "x": "х", "z": "з",
    "ƣ": "гъ",
    "ħ": "хӏ",
    "ḩ": "гӏ",
    "ķ": "кӏ",
    "ļ": "лъ",
    # Confirmed by the user directly against the 1936 print: ł is л with
    # palochka (лӀ) everywhere, including in nił/niłer/nełer -- do not
    # special-case grammatical forms by cross-referencing av-ru.jsonl
    # cognates, that produces invented exceptions (2026-11-01 correction).
    "ł": "лӏ",
    "ꝗ": "кь",
    "ꞩ": "ц",
    "ş": "ш",
    "şş": "щ",
    "ţ": "тӏ",
    "x̨": "хь",
    "x̵": "хъ",
    "ƶ": "ж",
    "ⱬ": "цӏ",
    "ç": "чӏ",
    "'": "ъ",
    "’": "ъ",
    # Precomposed Latin accented vowels: Zhirkov marks stress on Avar words
    # with an acute, same as in Russian prose (see the 2026-11-01 Latin/
    # Cyrillic script audit). Two words distinguished only by stress
    # placement -- burtína "бурка" vs Búrtina "Буртунай" (aul), per the
    # book's own preface, scan 7649 -- make dropping the accent unsafe.
    "á": "а́", "é": "е́", "í": "и́", "ó": "о́",
    "ú": "у́", "ý": "у́",
}

VOWELS = set("aeiou")

_sorted_keys: list[str] | None = None


def _keys() -> list[str]:
    global _sorted_keys
    if _sorted_keys is None:
        _sorted_keys = sorted(MAPPING.keys(), key=len, reverse=True)
    return _sorted_keys


def _units(lower: str) -> list[tuple[int, int, str]]:
    """Split into (start, end, cyrillic_output) spans, greedy longest match.

    Unmapped characters (hyphen, digits, space) pass through unchanged as
    their own unit, so stress-position remapping still has a span to find.
    """
    keys = _keys()
    out: list[tuple[int, int, str]] = []
    i = 0
    n = len(lower)
    while i < n:
        matched = False
        for key in keys:
            if lower.startswith(key, i):
                out.append((i, i + len(key), MAPPING[key]))
                i += len(key)
                matched = True
                break
        if not matched:
            out.append((i, i + 1, lower[i]))
            i += 1
    return out


def translit_word(text: str) -> str:
    """Transliterate one word/form. Capitalization: Zhirkov writes proper
    nouns with a single leading capital (confirmed: 0 internal-capital
    findings in the alphabet audit), so only the first letter is checked."""
    if not text:
        return text
    capitalize = text[:1].isupper()
    result = "".join(u[2] for u in _units(text.lower()))
    if capitalize and result:
        result = result[0].upper() + result[1:]
    return result


def translit_stress(text: str, position: int) -> int:
    """Remap a 1-indexed Unicode-codepoint stress position in the Latin
    `text` to the equivalent 1-indexed position in its transliteration.

    Stress always falls on a vowel, and every vowel is a 1-codepoint key
    mapping to exactly one Cyrillic letter, so the target unit's start
    always equals position - 1 exactly (no vowel is swallowed inside a
    multi-codepoint key)."""
    lower = text.lower()
    assert lower[position - 1] in VOWELS, (text, position)
    prefix = 0
    for start, end, out in _units(lower):
        if start == position - 1:
            return prefix + 1
        prefix += len(out)
    raise AssertionError((text, position))


def _translit_list(values: list[str]) -> list[str]:
    return [translit_word(v) for v in values]


def _translit_stress_map(forms: list[str], stresses: dict) -> dict:
    return {k: translit_stress(forms[int(k)], v) for k, v in stresses.items()}


def transliterate_entry(raw: dict) -> dict:
    entry = dict(raw)
    if entry.get("word"):
        latin_word = entry["word"]
        entry["word"] = translit_word(latin_word)
        if "stress" in entry:
            entry["stress"] = translit_stress(latin_word, entry["stress"])
    for key in ("forms", "spelling_forms", "gender_forms"):
        if entry.get(key):
            latin_forms = entry[key]
            entry[key] = _translit_list(latin_forms)
            stress_key = f"{key[:-1]}_stresses" if key != "forms" else "form_stresses"
            if entry.get(stress_key):
                entry[stress_key] = _translit_stress_map(latin_forms, entry[stress_key])
    senses = entry.get("senses")
    if senses:
        new_senses = []
        for sense in senses:
            if not isinstance(sense, dict):
                new_senses.append(sense)
                continue
            sense = dict(sense)
            if sense.get("forms"):
                latin_forms = sense["forms"]
                sense["forms"] = _translit_list(latin_forms)
                if sense.get("form_stresses"):
                    sense["form_stresses"] = _translit_stress_map(latin_forms, sense["form_stresses"])
            examples = sense.get("examples")
            if examples:
                new_examples = []
                for ex in examples:
                    ex = dict(ex)
                    if ex.get("av"):
                        ex["av"] = translit_word(ex["av"])
                    new_examples.append(ex)
                sense["examples"] = new_examples
            new_senses.append(sense)
        entry["senses"] = new_senses
    see_also = entry.get("see_also")
    if see_also:
        new_see = []
        for item in see_also:
            if isinstance(item, dict) and item.get("target"):
                item = dict(item)
                item["target"] = translit_word(item["target"])
            new_see.append(item)
        entry["see_also"] = new_see
    return entry


def has_untranslated_latin(text: str) -> bool:
    return any("a" <= ch.lower() <= "z" for ch in text)


if __name__ == "__main__":
    latin_path = ROOT / "data" / f"{SOURCE}.latin.jsonl"
    cyrillic_path = ROOT / "data" / f"{SOURCE}.jsonl"
    entries = [json.loads(line) for line in latin_path.read_text(encoding="utf-8").splitlines()]
    converted = [transliterate_entry(e) for e in entries]
    cyrillic_path.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in converted) + "\n",
        encoding="utf-8",
    )
    print(f"{cyrillic_path}: {len(converted)} entries")
