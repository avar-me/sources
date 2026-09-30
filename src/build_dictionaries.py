#!/usr/bin/env python3
"""Merge dictionary sources, with the first input taking priority per word."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def merge_entries(inputs: list[list[dict]]) -> list[dict]:
    """Keep all articles of each word from its highest-priority source.

    Sort by the same Avar alphabet as the site. Python's stable sort preserves
    the original order of articles with identical headwords, including homonyms.
    """
    from build_site import AVAR_ALPHABET, make_rank, make_sort_key, make_tokenizer

    owners: dict[str, int] = {}
    selected: list[dict] = []
    for index, entries in enumerate(inputs):
        for entry in entries:
            word = entry['word']
            if owners.setdefault(word, index) == index:
                selected.append(entry)
    sort_key = make_sort_key(make_rank(AVAR_ALPHABET), make_tokenizer('av'))
    return sorted(selected, key=lambda entry: sort_key(entry['word']))


def build_dictionaries(root: Path = ROOT) -> None:
    config = json.loads((root / 'dictionary-build.json').read_text(encoding='utf-8'))
    for dictionary in config['dictionaries']:
        inputs = []
        for name in dictionary['inputs']:
            entries = [json.loads(line) for line in (root / name).read_text(encoding='utf-8').splitlines() if line.strip()]
            if any(not entry.get('source') for entry in entries):
                raise ValueError(f'{name}: every article must have source')
            inputs.append(entries)
        entries = merge_entries(inputs)
        output = root / dictionary['output']
        content = ''.join(json.dumps(entry, ensure_ascii=False) + '\n' for entry in entries)
        if not output.exists() or output.read_text(encoding='utf-8') != content:
            temporary = output.with_suffix(output.suffix + '.tmp')
            temporary.write_text(content, encoding='utf-8')
            temporary.replace(output)
        print(f'{dictionary["output"]}: {len(entries)} articles')


if __name__ == '__main__':
    build_dictionaries()
