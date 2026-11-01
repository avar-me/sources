import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parse_saidov_1967 import (
    articles,
    build_entry,
    derive_gender_forms,
    extract_bold_examples,
    extract_known_examples,
    extract_see_also,
    headword_stress,
    parse_headword_bracket,
    split_leaf_runs,
    split_senses,
    tag_runs,
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

    def test_roman_numeral_in_its_own_bold_span_after_a_bracket(self):
        # <b>*ба́зе</b> [<i>повел.</i> <b>бай</b>] <b>I</b> <b>1)</b> ...
        # -- the homonym marker is only reachable after the headword's own
        # bracket note has already been stripped.
        article = next(a for a in self.by_prefix["базе"] if "повел" in a["text"])
        entry = build_entry(article)
        self.assertEqual(entry["homonym"], 1)


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
    """`split_senses`/`split_markers` (plain-text numbering split) still
    exist as simple, independently correct and tested utilities, but the
    real pipeline now splits on the run-level equivalent (`split_leaf_runs`,
    see TagRunTests/LeafRunSplittingTests below), since a sub-sense number
    is not always printed bold."""

    def test_splits_on_numbered_sub_senses(self):
        text = "1) быть; 2) находиться; 3) находить."
        self.assertEqual(split_senses(text), ["быть;", "находиться;", "находить."])

    def test_major_and_sub_senses_combine(self):
        text = "1. 1) висеть; 2) строиться; 2. находить."
        self.assertEqual(split_senses(text), ["висеть;", "строиться;", "находить."])

    def test_no_markers_is_a_single_sense(self):
        self.assertEqual(split_senses("вечный."), ["вечный."])


class TagRunTests(unittest.TestCase):
    def test_bold_italic_and_plain_runs(self):
        self.assertEqual(
            tag_runs("<b>гудур гъезе</b> поста́вить капка́н; <i>ср.</i> <b>ав</b>."),
            [("b", "гудур гъезе"), ("t", "поста́вить капка́н;"), ("i", "ср."), ("b", "ав"), ("t", ".")],
        )

    def test_stray_unmatched_closing_tag_is_dropped_not_leaked(self):
        # Regression: a bold span hyphen-split across a page boundary the
        # OCR pipeline did not rejoin leaves a lone "</b>" with no opening
        # tag in this fragment; it must not leak as literal "/b>" text.
        runs = tag_runs("тӀире гъезе</b> гнать теля́т")
        self.assertEqual(runs, [("t", "тӀире гъезе гнать теля́т")])

    def test_adjacent_same_kind_runs_merge(self):
        self.assertEqual(tag_runs("<b>а</b><b>б</b>"), [("b", "а б")])


class LeafRunSplittingTests(unittest.TestCase):
    def test_splits_on_bold_sub_sense_numbers(self):
        runs = tag_runs("<b>1)</b> быть; <b>2)</b> находиться; <b>3)</b> находить.")
        leaves = split_leaf_runs(runs)
        self.assertEqual([tag_runs("")[:0] or r for r in leaves], leaves)  # no-op, keeps runs typed
        self.assertEqual(len(leaves), 3)

    def test_plain_text_sub_marker_glued_to_following_prose(self):
        # Regression ("ратизе"): only the major marker is bold, and the
        # sub-markers are plain text immediately after it.
        runs = tag_runs("<b>1.</b> 1) быть; 2) находиться; <b>2.</b> находить.")
        self.assertEqual(len(split_leaf_runs(runs)), 3)

    def test_major_and_sub_marker_glued_into_one_bold_span(self):
        # Regression ("рагьизе"): "<b>1. 1)</b> открываться ...".
        runs = tag_runs("<b>1. 1)</b> открыва́ться; <b>2)</b> обнару́живаться; <b>2. 1)</b> открыва́ть.")
        self.assertEqual(len(split_leaf_runs(runs)), 3)

    def test_out_of_sequence_number_is_not_treated_as_a_marker(self):
        # Regression ("базе", a different homonym): the first two
        # sub-markers were OCR'd as letters ("а)", "б)"), so "3)" can
        # never validly be the *first* accepted marker.
        runs = tag_runs("а) бодать; б) подать рог; <b>3)</b> рожок; <b>4)</b> рожок для крови.")
        self.assertEqual(len(split_leaf_runs(runs)), 1)


class BoldExampleExtractionTests(unittest.TestCase):
    """The book's own typesetting (bold = Avar, italic = label/comment,
    plain = Russian translation) is the primary signal for splitting an
    example out of a sense, used before any text-based heuristic."""

    def test_bold_then_plain_is_an_example(self):
        runs = tag_runs("<b>гудур гъезе</b> поста́вить капка́н;")
        leftover, examples, idiom_leftover, idiom_examples = extract_bold_examples(runs)
        self.assertEqual(examples, [{"av": "гудур гъезе", "ru": "поста́вить капка́н"}])
        self.assertEqual(leftover, [])
        self.assertEqual((idiom_leftover, idiom_examples), ([], []))

    def test_bold_not_followed_by_substantial_text_is_left_as_leftover(self):
        # "ав", "ай II", "ал" are cross-reference targets (<i>ср.</i> ...),
        # not examples: nothing but punctuation follows each of them.
        runs = tag_runs("<i>ср.</i> <b>ав</b>, <b>ай II</b>, <b>ал</b>.")
        leftover, examples, _, _ = extract_bold_examples(runs)
        self.assertEqual(examples, [])
        self.assertEqual([c for _, c in leftover], ["ср.", "ав", ",", "ай II", ",", "ал", "."])

    def test_connector_word_between_two_bold_alternatives_is_not_an_example(self):
        # "<b>адаб тезе</b> или <b>адаб рехизе</b> преступить границы
        # приличия" -- "или" alone must not count as "адаб тезе"'s
        # translation (it belongs to "адаб рехизе" instead).
        runs = tag_runs("<b>адаб тезе</b> или <b>адаб рехизе</b> преступи́ть грани́цы прили́чия;")
        leftover, examples, _, _ = extract_bold_examples(runs)
        self.assertEqual(examples, [{"av": "адаб рехизе", "ru": "преступи́ть грани́цы прили́чия"}])
        self.assertIn(("b", "адаб тезе"), leftover)

    def test_inline_italic_aside_folds_into_the_translation(self):
        # The book also uses italic for a parenthetical wording
        # alternative *inside* a translation, not only for labels.
        runs = tag_runs("<b>гьаб нух Гъунибе уна</b> эта доро́га идёт (<i>или</i> ведёт) в Гуни́б;")
        _, examples, _, _ = extract_bold_examples(runs)
        self.assertEqual(examples, [{"av": "гьаб нух Гъунибе уна", "ru": "эта доро́га идёт (или ведёт) в Гуни́б"}])

    def test_leading_label_classifies_the_example_not_the_translation(self):
        runs = tag_runs("<b>къватӀахъ лъугьун жо ккеларо</b> <i>погов.</i> от шата́ния по у́лицам ума́ не приба́вится;")
        _, examples, _, _ = extract_bold_examples(runs)
        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["labels"], ["поговорка"])
        self.assertNotIn("погов", examples[0]["ru"])

    def test_bukv_introduces_a_literal_translation_comment(self):
        runs = tag_runs("<b>бакрулав гӀадин вакизе</b> отлупи́ть как бакри́нца; <i>букв.</i> представи́тель мекка́нского пле́мени.")
        _, examples, _, _ = extract_bold_examples(runs)
        self.assertEqual(examples[0]["ru"], "отлупи́ть как бакри́нца")
        self.assertEqual(examples[0]["comment"], "букв. представи́тель мекка́нского пле́мени")

    def test_idiom_marker_moves_subsequent_content_to_the_idiom_bucket(self):
        runs = tag_runs("э́тот же; ◇ <b>абго щиб жо дуца гьабулеб?</b> что́ же э́то ты де́лаешь?")
        leftover, examples, idiom_leftover, idiom_examples = extract_bold_examples(runs)
        self.assertEqual(examples, [])
        self.assertEqual(idiom_examples, [{"av": "абго щиб жо дуца гьабулеб?", "ru": "что́ же э́то ты де́лаешь?"}])

    def test_see_also_marker_ends_an_examples_translation_mid_group(self):
        # Regression ("абго"): "ср." must not be folded into the preceding
        # example's `ru`, even though it sits in the same run group.
        runs = tag_runs("<b>абго щиб жо дуца гьабулеб?</b> что́ же э́то ты де́лаешь?; <i>ср.</i> <b>авго</b>.")
        leftover, examples, _, _ = extract_bold_examples(runs)
        self.assertEqual(examples, [{"av": "абго щиб жо дуца гьабулеб?", "ru": "что́ же э́то ты де́лаешь?"}])
        self.assertTrue(any(k == "i" and c == "ср." for k, c in leftover))

    def test_stray_bold_sense_number_is_never_an_example(self):
        # No Avar word is just digits; a marker `split_leaf_runs` could not
        # place (see LeafRunSplittingTests.test_out_of_sequence...) must
        # stay inert rather than pair with the following prose.
        runs = tag_runs("а) бодать; б) подать рог; <b>3)</b> рожок для пороха.")
        _, examples, _, _ = extract_bold_examples(runs)
        self.assertEqual(examples, [])

    def test_stub_target_right_after_a_from_label_is_not_an_example(self):
        # "<i>повел. от</i> <b>ине</b> иди (отсюда), уходи." -- "ине" is the
        # grammatical target `try_stub` needs intact in the leftover text,
        # not an example of this headword ("а").
        runs = tag_runs("<i>повел. от</i> <b>ине</b> иди́ (отсю́да), уходи́.")
        leftover, examples, _, _ = extract_bold_examples(runs)
        self.assertEqual(examples, [])
        self.assertIn(("b", "ине"), leftover)


class SeeAlsoTests(unittest.TestCase):
    def test_trailing_sravni_clause_extracted(self):
        text, see_also = extract_see_also("находиться, найтись; ср. батизе, ватизе.")
        self.assertEqual(text, "находиться, найтись")
        self.assertEqual(see_also, [{"target": "батизе", "kind": "compare"}, {"target": "ватизе", "kind": "compare"}])

    def test_bare_number_continuation_reattaches_base_word(self):
        # "см. гӀадил 2, 3" -- both numbers are homonyms of гӀадил.
        _, see_also = extract_see_also("см. гӀадил 2, 3.")
        self.assertEqual(see_also, [{"target": "гӀадил 2", "kind": "see"}, {"target": "гӀадил 3", "kind": "see"}])


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
        self.assertEqual(sense, {"labels": ["родительный падеж"], "comment": "от 'аб', 'ай II'"})
        self.assertEqual(see_also, [{"target": "аб", "kind": "from"}, {"target": "ай II", "kind": "from"}])

    def test_causative_with_trailing_examples_keeps_them_as_text(self):
        sense, see_also = try_stub("понуд. от ахӀизе; данделъи ахӀизабизе заставить созвать собрание.")
        self.assertEqual(sense["labels"], ["понудительная форма"])
        self.assertEqual(sense["comment"], "от 'ахӀизе'")
        self.assertEqual(sense["text"], "данделъи ахӀизабизе заставить созвать собрание.")
        self.assertEqual(see_also, [{"target": "ахӀизе", "kind": "from"}])

    def test_imperative_uses_a_dedicated_label_not_a_crammed_comment(self):
        # Regression: a lazy `\S+?` target capture used to stop after a
        # single character ("ине" -> "и") once everything following it in
        # the pattern was optional; and "повел." belongs in `labels`, like
        # any other grammatical note, not appended into `comment` text.
        sense, see_also = try_stub("повел. от ине иди (отсюда), уходи.")
        self.assertEqual(sense["labels"], ["повелительное"])
        self.assertEqual(sense["comment"], "от 'ине'")
        self.assertEqual(sense["text"], "иди (отсюда), уходи.")
        self.assertEqual(see_also, [{"target": "ине", "kind": "from"}])

    def test_past_tense_uses_a_dedicated_label(self):
        sense, see_also = try_stub("прош. вр. от ине шёл, шла, шло, шли.")
        self.assertEqual(sense["labels"], ["прошедшее время"])
        self.assertEqual(sense["comment"], "от 'ине'")
        self.assertEqual(see_also, [{"target": "ине", "kind": "from"}])

    def test_plain_text_is_not_a_stub(self):
        self.assertIsNone(try_stub("вечный; навсегда, навеки."))


class FullEntryIntegrationTests(unittest.TestCase):
    """End-to-end checks against the real book HTML for a representative
    spread of structures: plain senses, a bracket of inflected forms, an
    idiom, a cross-reference, a class-marker word, and bold-tag-based
    example extraction."""

    def setUp(self):
        self.entries = {}
        for a in articles(load_html()):
            self.entries.setdefault(a["word"], []).append(build_entry(a))

    def test_buртина_forms_and_examples_from_bold_tags(self):
        entry = self.entries["буртина"][0]
        self.assertEqual(entry["forms"], ["буртина", "буртинадул", "буртаби"])
        self.assertEqual(len(entry["senses"]), 2)
        self.assertEqual(entry["senses"][0]["examples"][0]["av"], "буртинадул тӀагъур")

    def test_abgo_idiom_is_its_own_sense_with_an_example(self):
        entry = self.entries["абго"][0]
        idiom_senses = [s for s in entry["senses"] if s.get("labels") == ["поговорка"]]
        self.assertEqual(len(idiom_senses), 1)
        self.assertIn("абго щиб жо", idiom_senses[0]["examples"][0]["av"])
        self.assertEqual(
            entry["see_also"],
            [{"target": "авго", "kind": "compare"}, {"target": "айго", "kind": "compare"}, {"target": "алго", "kind": "compare"}],
        )

    def test_a_imperative_stub_matches_user_requested_shape(self):
        entry = self.entries["а"][0]
        sense = entry["senses"][0]
        self.assertEqual(sense["labels"], ["повелительное"])
        self.assertEqual(sense["comment"], "от 'ине'")
        self.assertEqual(sense["text"], "иди́ (отсю́да), уходи́.")
        self.assertEqual(entry["see_also"], [{"target": "ине", "kind": "from"}])

    def test_ratize_gets_three_senses_despite_plain_text_sub_markers(self):
        entry = self.entries["ратизе"][0]
        self.assertEqual(len(entry["senses"]), 3)
        self.assertTrue(entry["class_marker"])
        self.assertNotIn("gender_forms", entry)

    def test_abadiyab_class_marker_becomes_gender_forms(self):
        entry = self.entries["абадияб"][0]
        self.assertEqual(entry["gender_forms"], ["абадияб", "абадияв", "абадияй"])

    def test_phraseological_nest_still_has_senses(self):
        entry = self.entries["диб чӀвазе"][0]
        self.assertIn("senses", entry)
        examples = [ex for s in entry["senses"] for ex in s.get("examples", []) or []]
        self.assertTrue(any("хинкӀ чӀвазе" in ex["av"] for ex in examples))

    def test_no_stray_html_tag_leaks_into_any_example(self):
        # Regression: a bold span hyphen-split across a page boundary used
        # to leak a literal "</b>"-shaped fragment into an example's text.
        import re

        for entries in self.entries.values():
            for entry in entries:
                for sense in entry.get("senses", []):
                    for ex in sense.get("examples", []) or []:
                        self.assertNotRegex(ex.get("av", ""), r"</?[a-zA-Z]+>")
                        self.assertNotRegex(ex.get("ru", ""), r"</?[a-zA-Z]+>")


class KnownExampleExtractionTests(unittest.TestCase):
    """Secondary, high-confidence example extraction cross-referenced
    against av-ru.jsonl (av-ru.2006), run on whatever text the primary
    bold-tag-based extraction (see BoldExampleExtractionTests) did not
    already turn into an example -- e.g. when the 1967 typesetting itself
    is not bold at that point. A clause is only split when it starts with
    an exact (accent-insensitive) match of one of that headword's own
    av-ru.jsonl examples -- the match anchors the boundary, but the
    Russian translation kept is still 1967's own wording, never borrowed
    from av-ru.jsonl."""

    def test_known_example_is_extracted_and_removed_from_text(self):
        leftover, examples = extract_known_examples(
            "авал", "в разн. знач. нача́ло; ихдалил авал нача́ло весны́"
        )
        self.assertEqual(leftover, "в разн. знач. нача́ло")
        self.assertEqual(examples, [{"av": "ихдалил авал", "ru": "нача́ло весны́"}])

    def test_unknown_word_is_left_untouched(self):
        text = "совершенно unrelated content; абго щиб жо дуца гьабулеб? что же это ты делаешь?"
        self.assertEqual(extract_known_examples("несуществующее-слово-xyz", text), (text, []))

    def test_clause_without_trailing_translation_is_not_split(self):
        # A clause that exactly equals a known av-ru.jsonl example, with
        # nothing left over for `ru`, must not produce an empty-ru example.
        leftover, examples = extract_known_examples("абго", "абго щиб жо дуца гьабулеб?")
        self.assertEqual(leftover, "абго щиб жо дуца гьабулеб?")
        self.assertEqual(examples, [])

    def test_all_clauses_extracted_leaves_no_leftover_text(self):
        leftover, examples = extract_known_examples(
            "абго", "абго щиб жо дуца гьабулеб? что же это ты делаешь?"
        )
        self.assertIsNone(leftover)
        self.assertEqual(len(examples), 1)


if __name__ == "__main__":
    unittest.main()
