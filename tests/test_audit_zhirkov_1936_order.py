import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from audit_zhirkov_1936_order import audit, sort_key


class OrderAuditTests(unittest.TestCase):
    def test_original_asso_is_an_inversion(self):
        for apostrophe in "'’‘ʼʿ":
            with self.subTest(apostrophe=apostrophe):
                entries = [{'word': w} for w in ['assķo', f'ass{apostrophe}o', 'assosiasija']]
                self.assertEqual(audit(entries), [1])

    def test_corrected_asslo_is_in_order(self):
        entries = [{'word': w} for w in ['assķo', 'asslo', 'assosiasija']]
        self.assertEqual(audit(entries), [])

    def test_apostrophe_is_preserved_in_key_without_replacing_borrowing(self):
        entry = {'word': "qur'an"}
        self.assertNotEqual(sort_key(entry['word']), sort_key('quran'))
        self.assertEqual(sort_key("qur'an"), sort_key('qur’an'))
        self.assertEqual(entry['word'], "qur'an")
