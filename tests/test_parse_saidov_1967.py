import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parse_saidov_1967 import (
    articles,
    build_entry,
    derive_gender_forms,
    extract_idiom,
    extract_see_also,
    headword_stress,
    parse_headword_bracket,
    split_senses,
    try_stub,
    ROOT,
    SOURCE,
)


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


class NoWordNumberLeakTests(unittest.TestCase):
    """Regression for a real bug: the first sense number ("1)") is
    sometimes bolded together with the headword in the source
    (<b>хъали́къаб 1)</b>), which used to leak into `word`."""

    def setUp(self):
        self.articles = articles(load_html())

    def test_no_digits_in_word(self):
        import re

        offenders = [a["word"] for a in self.articles if re.search(r"\d", a["word"])]
        self.assertEqual(offenders, [])

    def test_known_offender_is_clean(self):
        article = next(a for a in self.articles if a["text"].startswith("*хъали́къаб"))
        self.assertEqual(article["word"], "хъаликъаб")


class HomonymMarkerTests(unittest.TestCase):
    def setUp(self):
        self.by_prefix = {}
        for a in articles(load_html()):
            self.by_prefix.setdefault(a["word"], []).append(a)

    def test_roman_numeral_inside_bold_becomes_homonym_field(self):
        # <b>авал</b> I / <b>авал</b> II -- both inside the bold heading.
        avals = self.by_prefix["авал"]
        self.assertEqual({a.get("homonym") for a in avals}, {1, 2})

    def test_roman_numeral_outside_bold_is_still_caught_at_build_time(self):
        # <b>бай</b> II <i>повел. от</i> <b>базе</b>. -- "II" sits just
        # outside the bold span, so articles() cannot see it; build_entry
        # must still recover it from the remainder.
        article = next(a for a in self.by_prefix["бай"] if "повел" in a["text"])
        entry = build_entry(article)
        self.assertEqual(entry["homonym"], 2)


class GenderFormsTests(unittest.TestCase):
    def test_adjective_shaped_word_gets_bvy_triple(self):
        self.assertEqual(derive_gender_forms("абадияб"), ["абадияб", "абадияв", "абадияй"])

    def test_non_b_ending_word_has_no_regular_triple(self):
        self.assertIsNone(derive_gender_forms("абазинав"))


class HeadwordBracketTests(unittest.TestCase):
    def test_single_form_with_case_label(self):
        self.assertEqual(parse_headword_bracket("род. п. алъу́л"), {"kind": "forms", "forms": ["алъул"]})

    def test_multiple_forms_across_semicolon(self):
        result = parse_headword_bracket("род. п. бурти́надул; мн. бурта́би")
        self.assertEqual(result, {"kind": "forms", "forms": ["буртинадул", "буртаби"]})

    def test_relation_to_another_word(self):
        self.assertEqual(
            parse_headword_bracket("прич. прош. вр. от ине"),
            {"kind": "relation", "label": "прич. прош. вр.", "target": "ине"},
        )

    def test_unlabeled_content_is_unknown_not_guessed(self):
        # Seen once, from an OCR-mangled page-wrap entry ("аб [у носовое]
        # действи-ьный..."): no case/form label present, so this must not
        # be silently misfiled as a word form.
        self.assertEqual(parse_headword_bracket("у носовое"), {"kind": "unknown"})


class SenseSplittingTests(unittest.TestCase):
    def test_splits_on_numbered_sub_senses(self):
        text = "1) быть; 2) находиться; 3) находить."
        self.assertEqual(split_senses(text), ["быть;", "находиться;", "находить."])

    def test_major_and_sub_senses_combine(self):
        text = "1. 1) висеть; 2) строиться; 2. находить."
        self.assertEqual(split_senses(text), ["висеть;", "строиться;", "находить."])

    def test_no_markers_is_a_single_sense(self):
        self.assertEqual(split_senses("вечный."), ["вечный."])


class SeeAlsoAndIdiomTests(unittest.TestCase):
    def test_trailing_sravni_clause_extracted(self):
        text, see_also = extract_see_also("находиться, найтись; ср. батизе, ватизе.")
        self.assertEqual(text, "находиться, найтись")
        self.assertEqual(see_also, [{"target": "батизе", "kind": "compare"}, {"target": "ватизе", "kind": "compare"}])

    def test_bare_number_continuation_reattaches_base_word(self):
        # "см. гӀадил 2, 3" -- both numbers are homonyms of гӀадил.
        _, see_also = extract_see_also("см. гӀадил 2, 3.")
        self.assertEqual(see_also, [{"target": "гӀадил 2", "kind": "see"}, {"target": "гӀадил 3", "kind": "see"}])

    def test_idiom_marker_splits_off_the_rest(self):
        main, idiom = extract_idiom("этот же; ◇ абго щиб жо дуца гьабулеб? что же это ты делаешь?")
        self.assertEqual(main, "этот же")
        self.assertTrue(idiom.startswith("абго"))


class StubPatternTests(unittest.TestCase):
    def test_masdar_of_verb(self):
        sense, see_also = try_stub("масд. глагола абизабизе.")
        self.assertEqual(sense, {"labels": ["масдар"], "masdarfrom": "абизабизе"})
        self.assertEqual(see_also, [{"target": "абизабизе", "kind": "from"}])

    def test_plural_stub_with_gloss(self):
        sense, see_also = try_stub("мн. от огоб, рожь.")
        self.assertEqual(sense, {"labels": ["множественное число"], "pluralfor": "огоб", "text": "рожь."})
        self.assertEqual(see_also, [{"target": "огоб", "kind": "from"}])

    def test_genitive_single_target(self):
        sense, see_also = try_stub("род. п. от огоб, рожь.")
        self.assertEqual(sense, {"text": "рожь.", "genitivefrom": "огоб", "comment": "родительный падеж"})
        self.assertEqual(see_also, [{"target": "огоб", "kind": "from"}])

    def test_genitive_multiple_targets_has_no_single_field(self):
        sense, see_also = try_stub("род. п. от аб и ай II.")
        self.assertEqual(sense, {"labels": ["родительный падеж"], "comment": "от \'аб\', \'ай II\'"})
        self.assertEqual(see_also, [{"target": "аб", "kind": "from"}, {"target": "ай II", "kind": "from"}])

    def test_causative_with_trailing_examples_keeps_them_as_text(self):
        sense, see_also = try_stub("понуд. от ахӀизе; данделъи ахӀизабизе заставить созвать собрание.")
        self.assertEqual(sense["labels"], ["понудительная форма"])
        self.assertEqual(sense["comment"], "от 'ахӀизе'")
        self.assertEqual(sense["text"], "данделъи ахӀизабизе заставить созвать собрание.")
        self.assertEqual(see_also, [{"target": "ахӀизе", "kind": "from"}])

    def test_imperative_target_is_not_truncated(self):
        # Regression: a lazy `\S+?` target capture used to stop after a
        # single character ("ине" -> "и") once everything following it in
        # the pattern was optional.
        sense, see_also = try_stub("повел. от ине иди (отсюда), уходи.")
        self.assertEqual(sense["comment"], "от 'ине'; повел.")
        self.assertEqual(sense["text"], "иди (отсюда), уходи.")
        self.assertEqual(see_also, [{"target": "ине", "kind": "from"}])

    def test_plain_text_is_not_a_stub(self):
        self.assertIsNone(try_stub("вечный; навсегда, навеки."))


class FullEntryIntegrationTests(unittest.TestCase):
    """End-to-end checks against the real book HTML for a representative
    spread of structures: plain senses, a bracket of inflected forms, an
    idiom, a cross-reference, and a class-marker word."""

    def setUp(self):
        self.entries = {}
        for a in articles(load_html()):
            self.entries.setdefault(a["word"], []).append(build_entry(a))

    def test_buртина_forms_from_headword_bracket(self):
        entry = self.entries["буртина"][0]
        self.assertEqual(entry["forms"], ["буртина", "буртинадул", "буртаби"])
        self.assertEqual(len(entry["senses"]), 2)

    def test_abgo_idiom_becomes_its_own_sense(self):
        entry = self.entries["абго"][0]
        idiom_senses = [s for s in entry["senses"] if s.get("labels") == ["поговорка"]]
        self.assertEqual(len(idiom_senses), 1)
        self.assertIn("абго щиб жо", idiom_senses[0]["text"])

    def test_ratize_class_marker_without_b_ending_stays_boolean(self):
        entry = self.entries["ратизе"][0]
        self.assertTrue(entry["class_marker"])
        self.assertNotIn("gender_forms", entry)

    def test_abadiyab_class_marker_becomes_gender_forms(self):
        entry = self.entries["абадияб"][0]
        self.assertEqual(entry["gender_forms"], ["абадияб", "абадияв", "абадияй"])

    def test_phraseological_nest_still_has_senses(self):
        entry = self.entries["диб чӀвазе"][0]
        self.assertIn("senses", entry)
        joined = " ".join(s.get("text", "") for s in entry["senses"])
        self.assertIn("хинкӀ чӀвазе", joined)


if __name__ == "__main__":
    unittest.main()
