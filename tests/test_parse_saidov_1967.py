import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parse_saidov_1967 import articles, build_entry, headword_stress, ROOT, SOURCE


def load_html():
    return (ROOT / "books" / SOURCE / f"{SOURCE}.html").read_text(encoding="utf-8")


class HeadwordStressTests(unittest.TestCase):
    def test_no_accent(self):
        self.assertEqual(headword_stress("ракӀ"), ("ракӀ", None))

    def test_single_accent(self):
        self.assertEqual(headword_stress("ба́гъаб"), ("багъаб", 2))

    def test_multiple_accents_leaves_stress_unset(self):
        word, stress = headword_stress("а́ба́ди")
        self.assertIsNone(stress)
        self.assertEqual(word, "абади")


class ArticleBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.html = load_html()
        self.articles = articles(self.html)

    def test_parses_without_raising(self):
        self.assertGreater(len(self.articles), 15000)

    def test_no_empty_words(self):
        self.assertTrue(all(a["word"].strip() for a in self.articles))

    def test_star_before_or_inside_bold_both_set_class_marker(self):
        # *<b>вагъа-вакари</b> -- star outside the bold span
        self.assertTrue(next(a for a in self.articles if a["word"] == "вагъа-вакари")["class_marker"])
        # <b>*аб</b> -- star inside the bold span (first "аб" homonym)
        self.assertTrue(next(a for a in self.articles if a["word"] == "аб")["class_marker"])

    def test_phraseological_nest_stays_one_article(self):
        # A single printed article gathering many idioms under "чӀвазе";
        # a boundary-detection regression would split or merge this badly.
        article = next(a for a in self.articles if a["word"] == "диб чӀвазе")
        self.assertIn("хинкӀ чӀвазе", article["text"])

    def test_page_wrap_continuation_is_not_orphaned(self):
        by_word = {a["word"]: a for a in self.articles}
        self.assertIn("шевеле́ние", by_word["вагъа-вачари"]["text"])

    def test_double_bar_variant_spelling(self):
        article = next((a for a in self.articles if "spelling_forms" in a), None)
        self.assertIsNotNone(article)
        self.assertIn(article["word"], article["spelling_forms"][0])


class BuildEntryTests(unittest.TestCase):
    def test_class_marker_becomes_comment(self):
        entry = build_entry({"word": "аб", "text": "*аб текст", "page": 23, "class_marker": True})
        self.assertIn("классный показатель", entry["comment"])

    def test_no_comment_without_marker(self):
        entry = build_entry({"word": "а", "text": "а текст", "page": 23})
        self.assertNotIn("comment", entry)


if __name__ == "__main__":
    unittest.main()
