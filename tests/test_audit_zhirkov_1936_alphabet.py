import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from audit_zhirkov_1936_alphabet import anomalies, audit, latin_fields


class AlphabetAuditTests(unittest.TestCase):
    def test_indexed_stress_is_reported_but_example_stress_is_allowed(self):
        found = audit([{'word': 'bá', 'spelling_forms': ['bá', 'bú'],
                        'senses': [{'forms': ['bà'], 'examples': [{'av': 'bá', 'ru': 'сло́во'}]}]}])
        self.assertEqual({x['field'] for x in found},
                         {'word', 'spelling_forms[0]', 'spelling_forms[1]', 'senses[0].forms[0]'})
        self.assertTrue(all(x['indexed_stress'] for x in found))

    def test_punctuation_and_interior_case_are_audited(self):
        entries = [{'word': 'ab...', 'forms': ['kana¹', 'okruI'],
                    'senses': [{'examples': [{'av': "foo* ķib·ķib", 'ru': 'текст'}]}]}]
        found = audit(entries)
        self.assertEqual(len(found), 4)
        self.assertTrue(any(x['unexpected_symbols'] == ['...'] for x in found))
        self.assertTrue(any(x['internal_capitals'] == ['okruI'] for x in found))
        self.assertFalse(audit([{'word': "ab-c'd", 'spelling_forms': ['Ab', 'ODN'],
                                 'senses': [{'examples': [{'av': 'á h. (?)', 'ru': 'русский'}]}]}]))

    def test_only_latin_language_fields_are_checked(self):
        entry = {'word': 'ab', 'forms': ['ab', 'aх'],
                 'senses': [{'text': 'русский перевод', 'labels': ['метка'],
                             'comment': 'русское пояснение',
                             'forms': ['baс'], 'examples': [{'av': 'ab', 'ru': 'этот'}]}],
                 'see_also': [{'target': 'рe', 'kind': 'see'}]}
        found = audit([entry])
        self.assertEqual({x['field'] for x in found}, {'forms[1]', 'senses[0].forms[0]', 'see_also[0].target'})
        self.assertEqual({c for x in found for c in x['cyrillic']}, {'х', 'с', 'р'})

    def test_historical_graphs_stress_and_uncertain_ocr(self):
        self.assertEqual(anomalies('Ƣ ƣ Ḩ ḩ ļ ł ꞩ ƶ ⱬ x̨ x̵ á à ţ ķ ç ş'), ([], []))
        self.assertEqual(anomalies('ɫ ṣ q̇'), ([], ['ɫ', 'ṣ', 'q̇']))
        self.assertTrue(anomalies('aх')[0])
        self.assertTrue(anomalies('q́')[1])


if __name__ == '__main__':
    unittest.main()
