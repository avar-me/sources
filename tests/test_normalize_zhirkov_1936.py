import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from normalize_zhirkov_1936 import normalize_text, normalize_fragment, normalize_unicode
from audit_zhirkov_1936_order import sort_key, inversion


class NormalizationTests(unittest.TestCase):
    def test_graphic_aliases_and_case(self):
        self.assertEqual(normalize_unicode("Ṭ ṭ ţ ț ṯ ṭ ṫ"), "Ţ ţ ţ ţ ţ ţ ţ")
        self.assertEqual(normalize_unicode("ḳ ķ ƙ ⱪ k̦"), "ķ ķ ķ ķ ķ")
        self.assertEqual(normalize_unicode("ḥ Ḥ ḩ ɫ ɬ ɭ ḷ ļ ł"), "ḩ Ḩ ḩ ɫ ļ ļ ļ ļ ł")

    def test_distinct_historical_letters_do_not_merge(self):
        self.assertEqual(normalize_unicode("ħ ḥ x̨ x̌ χ z̵ z̧ q q̵"), "ħ ḩ x̨ x̵ x̵ ƶ ⱬ q ꝗ")
        self.assertNotEqual(normalize_unicode("ħ"), normalize_unicode("ḥ"))
        self.assertNotEqual(normalize_unicode("x̨"), normalize_unicode("χ"))

    def test_stress_unknown_marks_and_doubled_consonants_survive(self):
        self.assertEqual(normalize_unicode("ṭá русски́й h̃ ç̧"), "ţá русски́й h̃ ç̧")
        self.assertEqual(normalize_unicode("z̧z̧ad"), "ⱬⱬad")
        self.assertEqual(normalize_unicode("ṣ q̇ x̣"), "ṣ q̇ x̣")

    def test_codes_only_in_grammatical_positions(self):
        self.assertEqual(normalize_text("word [11 a, I5 b, pcs c, adu d] (15) перевод 11"), "word [l1 a, l5 b, pos c, adv d] (l5) перевод 11")
        self.assertEqual(normalize_text("word [l a] l перево́д"), "word [l a] i перево́д")
        self.assertEqual(normalize_text("word (l) перево́д"), "word (l) перево́д")

    def test_markup_and_split_runs(self):
        fragment, before, after = normalize_fragment('<b>k</b>̣á [<i>15</i> x]; <i>l</i> сло́во')
        self.assertEqual(after, "ķá [l5 x]; i сло́во")
        self.assertIn('<b>ķ</b>', fragment)
        self.assertIn('<i>l5</i>', fragment)
        self.assertEqual(normalize_fragment(fragment)[0], fragment)

    def test_combining_insertion_stays_with_bold_base(self):
        from normalize_zhirkov_1936 import patch_parts
        parts = [['ƣajix', 'ƣajix'], [' перевод', ' перевод']]
        patch_parts(parts, 'ƣajix перевод', 'ƣajix̵ перевод')
        self.assertEqual(parts[0][0], 'ƣajix̵')
        self.assertEqual(parts[1][0], ' перевод')
        self.assertEqual(normalize_unicode('ɫ ɩ ɪ ɡ h̦'), 'ɫ i i g ḩ')

    def test_idempotence(self):
        value = "Ṭ ḥ ɫ z̨z̨ x̦ χ [11 word] l сло́во"
        self.assertEqual(normalize_text(normalize_text(value)), normalize_text(value))

    def test_historical_sort_order_and_optional_letters(self):
        self.assertLess(sort_key('aƣ'), sort_key('ah'))
        self.assertLess(sort_key('kj'), sort_key('kk'))
        self.assertLess(sort_key('kk'), sort_key('kķ'))
        self.assertEqual(sort_key('ba-ri'), sort_key('bari'))
        self.assertLess(sort_key("ba-'ri"), sort_key('bari'))
        self.assertFalse(inversion('bar', 'ba(r)i'))


if __name__ == '__main__':
    unittest.main()
