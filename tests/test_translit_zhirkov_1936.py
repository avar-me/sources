import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from translit_zhirkov_1936 import (
    translit_word,
    translit_stress,
    transliterate_entry,
    has_untranslated_latin,
)


class TranslitWordTests(unittest.TestCase):
    def test_base_letters(self):
        self.assertEqual(translit_word("cul"), "чул")

    def test_digraphs(self):
        self.assertEqual(translit_word("ƣalbac"), "гъалбач")
        self.assertEqual(translit_word("ħalal"), "хӏалал")
        self.assertEqual(translit_word("ḩalturu"), "гӏалтуру")
        self.assertEqual(translit_word("ķarkara"), "кӏаркара")
        self.assertEqual(translit_word("ꞩo"), "цо")
        self.assertEqual(translit_word("şamal"), "шамал")
        self.assertEqual(translit_word("ţuxub"), "тӏухуб")
        self.assertEqual(translit_word("ƶo"), "жо")
        self.assertEqual(translit_word("ⱬul"), "цӏул")
        self.assertEqual(translit_word("çara"), "чӏара")
        self.assertEqual(translit_word("ꝗul"), "кьул")
        self.assertEqual(translit_word("x̨aze"), "хьазе")
        self.assertEqual(translit_word("x̵izan"), "хъизан")

    def test_geminate_shsh_becomes_shcha(self):
        # Confirmed against modern av-ru.jsonl cognates: bişşize == бищизе
        # "выбирать", başşad == бащад "равный" -- geminate şş is one
        # phoneme (щ), not two ш in a row.
        self.assertEqual(translit_word("bişşize"), "бищизе")
        self.assertEqual(translit_word("başşad"), "бащад")
        self.assertEqual(translit_word("başşdab"), "бащдаб")

    def test_single_sh_stays_sh(self):
        self.assertEqual(translit_word("kurak-barş"), "курак-барш")

    def test_apostrophe_is_glottal_stop(self):
        self.assertEqual(translit_word("qur'an"), "къуръан")
        self.assertEqual(translit_word("mas'alat"), "масъалат")

    def test_capitalization_preserved_on_first_letter_only(self):
        self.assertEqual(translit_word("Burtina"), "Буртина")

    def test_precomposed_latin_accent_becomes_cyrillic_plus_combining_acute(self):
        # burtína "бурка" vs Búrtina "Буртунай" -- minimal pair by stress
        # alone, per the book's own preface (scan 7649); dropping the
        # accent would silently merge two different words.
        self.assertEqual(translit_word("burtína"), "бурти́на")

    def test_hyphen_and_digits_pass_through(self):
        self.assertEqual(translit_word("adres-ustul"), "адрес-устул")

    def test_no_untranslated_latin_remains(self):
        samples = ["ƣaldiber", "ħalal", "bişşize", "qur'an", "x̨aze", "x̵izan"]
        for word in samples:
            self.assertFalse(has_untranslated_latin(translit_word(word)), word)


class TranslitStressTests(unittest.TestCase):
    def test_stress_shifts_by_digraph_expansion(self):
        # ƣalmaqalci, stress on 10th Latin codepoint (final i) -> 12th
        # Cyrillic codepoint, since ƣ->гъ and q->къ each add one char.
        self.assertEqual(translit_stress("ƣalmaqalci", 10), 12)

    def test_stress_unaffected_by_single_letter_mapping(self):
        self.assertEqual(translit_stress("naduxan", 4), 4)

    def test_stress_on_letter_inside_two_codepoint_grapheme(self):
        self.assertEqual(translit_stress("x̨aze", 3), 3)


class TransliterateEntryTests(unittest.TestCase):
    def test_full_entry_round_trip(self):
        raw = {
            "word": "burtabi",
            "stress": 2,
            "forms": ["burtabi"],
            "form_stresses": {"0": 2},
            "senses": [{"text": "неизменный русский перевод",
                        "examples": [{"av": "ⱬa bakize", "ru": "разводить огонь"}]}],
            "see_also": [{"target": "Burtina", "kind": "compare"}],
            "source": "av-ru.1936",
        }
        out = transliterate_entry(raw)
        self.assertEqual(out["word"], "буртаби")
        self.assertEqual(out["stress"], 2)
        self.assertEqual(out["forms"], ["буртаби"])
        self.assertEqual(out["form_stresses"], {"0": 2})
        self.assertEqual(out["senses"][0]["text"], "неизменный русский перевод")
        self.assertEqual(out["senses"][0]["examples"][0]["av"], "цӏа бакизе")
        self.assertEqual(out["senses"][0]["examples"][0]["ru"], "разводить огонь")
        self.assertEqual(out["see_also"][0]["target"], "Буртина")
        self.assertEqual(out["source"], "av-ru.1936")

    def test_does_not_mutate_input(self):
        raw = {"word": "ⱬul", "forms": ["ⱬul"]}
        transliterate_entry(raw)
        self.assertEqual(raw["word"], "ⱬul")


if __name__ == "__main__":
    unittest.main()
