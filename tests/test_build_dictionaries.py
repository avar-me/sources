import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from build_dictionaries import build_dictionaries, merge_entries


class DictionaryMergeTests(unittest.TestCase):
    def test_priority_keeps_all_articles_of_winning_word(self):
        first = [{'word': 'а', 'homonym': 1}, {'word': 'а', 'homonym': 2}, {'word': 'б'}]
        second = [{'word': 'а', 'homonym': 3}, {'word': 'в'}, {'word': 'в'}]
        self.assertEqual(merge_entries([first, second]), first + second[1:])
        self.assertEqual(merge_entries([second, first]), second[:1] + [first[2]] + second[1:])

    def test_avar_sort_keeps_digraphs_and_identical_headwords(self):
        entries = [{'word': 'гьан'}, {'word': 'ган'}, {'word': 'гъан'},
                   {'word': 'гӏан'}, {'word': 'данд'},
                   {'word': 'ган', 'homonym': 2}]
        self.assertEqual(merge_entries([entries]),
                         [entries[i] for i in [1, 5, 2, 0, 3, 4]])

    def test_third_source_and_repeat_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs = []
            for index, words in enumerate([['а', 'а'], ['а', 'б'], ['а', 'б', 'в']]):
                name = f'{index}.jsonl'
                inputs.append(name)
                (root / name).write_text(''.join(json.dumps({'word': w, 'source': str(index)}, ensure_ascii=False) + '\n' for w in words), encoding='utf-8')
            (root / 'dictionary-build.json').write_text(json.dumps({'dictionaries': [{'inputs': inputs, 'output': 'combined.jsonl'}]}))
            build_dictionaries(root)
            output = root / 'combined.jsonl'
            before = output.read_bytes()
            timestamp = output.stat().st_mtime_ns
            self.assertEqual([json.loads(l)['word'] for l in before.decode().splitlines()], ['а', 'а', 'б', 'в'])
            build_dictionaries(root)
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual(output.stat().st_mtime_ns, timestamp)


if __name__ == '__main__':
    unittest.main()
