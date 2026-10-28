#!/usr/bin/env python3
"""Audit Latin dictionary fields without transliterating Russian prose or editing data."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata as ud

try:
    from .audit_zhirkov_1936_order import ALPHABET
    from .parse_zhirkov_1936 import ROOT, articles
except ImportError:
    from audit_zhirkov_1936_order import ALPHABET
    from parse_zhirkov_1936 import ROOT, articles

LETTERS = {ud.normalize('NFD', c) for c in ALPHABET}
LATIN_KEYS = {'word', 'forms', 'spelling_forms', 'gender_forms', 'av', 'target'}


def latin_fields(value, path=''):
    if isinstance(value, dict):
        for key, item in value.items():
            location = f'{path}.{key}' if path else key
            if key in LATIN_KEYS:
                if isinstance(item, str):
                    yield location, item
                elif isinstance(item, list):
                    for i, text in enumerate(item):
                        if isinstance(text, str):
                            yield f'{location}[{i}]', text
                elif isinstance(item, dict):
                    for label, text in item.items():
                        if isinstance(text, str):
                            yield f'{location}.{label}', text
            elif isinstance(item, (dict, list)):
                yield from latin_fields(item, location)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from latin_fields(item, f'{path}[{i}]')


def anomalies(text):
    """Keep original code points in diagnostics; allow punctuation and vowel stress."""
    cyrillic = sorted({c for c in text if 'CYRILLIC' in ud.name(c, '')})
    foreign = []
    for cluster in re.findall(r'[^\u0300-\u036f][\u0300-\u036f]*|[\u0300-\u036f]+', ud.normalize('NFD', text.lower())):
        if cluster[0].isalpha():
            tested = cluster
            if cluster[0] in 'aeiou':
                tested = tested.replace('\u0301', '').replace('\u0300', '')
            if tested not in LETTERS:
                foreign.append(ud.normalize('NFC', cluster))
        elif any(ud.combining(c) for c in cluster):
            foreign.append(ud.normalize('NFC', cluster))
    return cyrillic, list(dict.fromkeys(foreign))


def audit(entries):
    result = []
    for line, entry in enumerate(entries, 1):
        for path, value in latin_fields(entry):
            cyrillic, foreign = anomalies(value)
            if cyrillic or foreign:
                result.append(dict(line=line, word=entry['word'], field=path, value=value,
                                   cyrillic=cyrillic, outside_alphabet=foreign))
    return result


def report(entries, findings, pages):
    cy = [r for r in findings if r['cyrillic']]
    lines = ['# av-ru.1936: проверка алфавита аварских полей', '',
             f'Статей: {len(entries)}. Полей с кириллицей: {len(cy)}. '
             f'Полей с графемами вне алфавита: {len(findings)} '
             f'в {len({r["line"] for r in findings})} статьях.', '',
             'Проверяются word, forms, spelling_forms, gender_forms, examples[].av и see_also[].target. '
             'Русские переводы, labels и комментарии не транслитерируются. '
             'Разрешены 39 исторических букв, регистр, пунктуация и ударение на гласной. '
             'Цифры допустимы в обозначениях; предупреждение не служит командой удаления.', '',
             'Каноническая запись не доказывает правильность чтения: подмена одной допустимой буквы '
             'другой здесь не обнаруживается. Особенно важны контекстная проверка ɫ и различение x/x̨/x̵.', '',
             'Воспроизведение: `python3 src/audit_zhirkov_1936_alphabet.py '
             '--report review/av-ru.1936-alphabet.md --json review/av-ru.1936-alphabet.json`.', '',
             '| Строка | Скан | Слово | Поле | Значение | Кириллица | Вне алфавита |',
             '|---:|---:|---|---|---|---|---|']
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    for r in findings:
        lines.append('| ' + ' | '.join(map(cell, [r['line'], pages.get(r['line'], ''), r['word'],
                     r['field'], r['value'], ' '.join(r['cyrillic']), ' '.join(r['outside_alphabet'])])) + ' |')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    entries = [json.loads(s) for s in (ROOT / 'data/av-ru.1936.jsonl').read_text(encoding='utf-8').splitlines()]
    findings = audit(entries)
    source = articles((ROOT / 'books/av-ru.1936/av-ru.1936.html').read_text(encoding='utf-8'))
    assert len(source) == len(entries)
    pages = {i: a['page'] for i, a in enumerate(source, 1)}
    if args.report:
        args.report.write_text(report(entries, findings, pages), encoding='utf-8')
    if args.json:
        args.json.write_text(json.dumps(findings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(findings)} fields outside alphabet; {sum(bool(r["cyrillic"]) for r in findings)} with Cyrillic')
