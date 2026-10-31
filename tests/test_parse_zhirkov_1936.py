import json
import re
import sys
import unittest
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from parse_zhirkov_1936 import (
    GRAMMAR, ORIGINS, ORIGIN_GLYPHS, RUSSIAN_LABELS,
    articles, parse, structure, unaccent, headword_spellings, headword_stress,
)
from normalize_zhirkov_1936 import CODE_ALIASES


def entry(body):
    return parse("<!-- p010-L,p010-R · printed p.12 --><p>" + body + "</p>")[0]


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


class ZhirkovParserTests(unittest.TestCase):
    def test_bare_numbered_case_codes_after_starred_examples(self):
        e = entry('<b>ƣoba*</b> l5 там; ƣobe* al5 туда (вниз); gobasa* el5 оттуда (снизу).')
        examples = e['senses'][0]['examples']
        self.assertEqual([x['av'] for x in examples], ['ƣobe', 'gobasa'])
        self.assertEqual(examples[0]['labels'], ['направительный падеж', '5-я серия'])
        self.assertEqual(examples[1]['labels'], ['исходный падеж', '5-я серия'])
        self.assertIn('Знак *', examples[0]['comment'])
        self.assertIn('вниз', examples[0]['comment'])
        self.assertEqual(examples[1]['ru'], 'оттуда.')

    def test_case_mark_between_headword_and_variant(self):
        e = entry('<b>Ƣoloda</b> (l1), <b>Ƣoloda-bak</b> Голода (область).')
        self.assertEqual(e['forms'], ['Ƣoloda', 'Ƣoloda-bak'])
        self.assertEqual(e['senses'][0]['text'], 'Голода.')
        self.assertIn('местный падеж', e['senses'][0]['labels'])
        self.assertNotIn('examples', e['senses'][0])

    def test_comma_separated_origin_and_grammar_codes_are_not_examples(self):
        e = entry('<b>pessok-cakar</b> r, p са́харный песо́к.')
        self.assertEqual(e['senses'][0]['text'], 'са́харный песо́к.')
        self.assertEqual(e['senses'][0]['labels'], ['русское происхождение', 'персидское происхождение'])
        self.assertNotIn('examples', e['senses'][0])
        e = entry('<b>azar</b> p, azargo ты́сяча.')
        self.assertEqual(e['forms'], ['azar', 'azargo'])
        self.assertEqual(e['senses'][0]['labels'], ['персидское происхождение'])
        e = entry('<b>dozul</b> pos pl, dozulab их.')
        self.assertEqual(e['senses'][0]['labels'], ['родительный падеж', 'множественное число'])
        self.assertEqual(e['senses'][0]['examples'][0]['av'], 'dozulab')

    def test_shared_translation_keeps_expression_variants(self):
        e = entry('<b>nux</b> доро́га; maşinadul nux, maxxul nux желе́зная доро́га.')
        self.assertEqual(e['senses'][0]['examples'][0]['av'], 'maşinadul nux, maxxul nux')
        e = entry('<b>x</b> reķarab (part perf), верхово́й.')
        self.assertEqual(e['senses'][0]['examples'][0]['av'], 'reķarab')
        e = entry('<b>azar</b> ты́сяча; azar-alda (l1) = azar (с со́тнями).')
        self.assertIn({'target': 'azar', 'kind': 'spelling',
                       'comment': 'Отсылка при выражении: azar-alda; с со́тнями'}, e['see_also'])
        self.assertNotIn('examples', e['senses'][0])

    def test_parenthetical_russian_prefix_is_part_of_word(self):
        for prefix, base in [('на', 'про́тив'), ('воз', 'обновля́ться'), ('пере', 'ме́на')]:
            e = entry('<b>x</b> (' + prefix + ')' + base + '.')
            self.assertEqual(e['senses'][0]['text'], '(' + prefix + ')' + base + '.')
            self.assertNotIn('precomment', e['senses'][0])
        e = entry('<b>x</b> сло́во; (раз)мо́лотый.')
        self.assertEqual(e['senses'][1]['text'], '(раз)мо́лотый.')

    def test_comma_before_phrase_does_not_consume_its_first_word(self):
        e = entry('<b>kari</b> [act karusa], karul ƣveţ ту́товое де́рево.')
        self.assertEqual(e['forms'], ['kari', 'karusa'])
        self.assertEqual(e['senses'][0]['examples'][0]['av'], 'karul ƣveţ')
        e = entry('<b>x</b>, y (l5) сло́во.')
        self.assertEqual(e['forms'], ['x', 'y'])
        self.assertEqual(e['senses'][0]['text'], 'сло́во.')
        e = entry('<b>x</b>, y = z (ср. q).')
        self.assertEqual(e['forms'], ['x', 'y'])
        self.assertIn({'target': 'z', 'kind': 'spelling'}, e['see_also'])

    def test_example_paradigm_is_comment_and_headword_h_is_restored(self):
        e = entry('<b>ƶib</b> сам; ƶib-ƶib [act ƶinsa-ƶinsa] ка́ждый.')
        ex = e['senses'][0]['examples'][0]
        self.assertEqual(ex['av'], 'ƶib-ƶib')
        self.assertIn('[act ƶinsa-ƶinsa]', ex['comment'])
        self.assertEqual(entry('<b>been</b> h. удобря́ть.')['senses'][0]['examples'][0]['av'], 'been h.')

    def test_separated_ending_is_not_a_search_form(self):
        e = entry('<b>ixx</b> [pos ixxdal (-il); oxxol(il)] весна́.')
        self.assertEqual(e['forms'], ['ixx', 'ixxdal', 'oxxol(il)'])
        self.assertIn({'labels': ['родительный падеж'], 'forms': ['ixxdal'],
                       'comment': 'Вариант окончания в источнике: -il'}, e['senses'])

    def test_subject_number_alternative_stays_in_example_translation(self):
        e = entry('<b>çaxad!</b> [çaxadal!]; beţer çaxad! да бу́дет он (бу́дут они́) здоро́в(ы)! (ср. çaxa).')
        self.assertEqual(e['forms'], ['çaxad!', 'çaxadal!'])
        ex = e['senses'][0]['examples'][0]
        self.assertEqual(ex['av'], 'beţer çaxad!')
        self.assertEqual(ex['ru'], 'да бу́дет он (бу́дут они́) здоро́в(ы)!')
        self.assertNotIn('comment', ex)
        self.assertEqual(entry('<b>x</b> x y куда́? (ср. z).')['senses'][0]['examples'][0]['ru'], 'куда́?')

    def test_origin_only_heading_survives_page_break_without_swallowing_footers(self):
        es = parse('<!-- p079-L --><p><b>maħo</b> нога́.</p>'
                   '<p><b>maħrum, maħrun</b> <i>a</i></p>'
                   '<p><b>M</b></p><!-- p080-L --><p>лишённый.</p>')
        self.assertEqual([e['word'] for e in es], ['maħo', 'maħrum'])
        self.assertEqual(es[0]['senses'][0]['text'], 'нога́.')
        self.assertEqual(es[1]['senses'][0]['text'], 'лишённый.')
        self.assertIn('арабское происхождение', es[1]['senses'][0]['labels'])

    def test_form_stresses_use_local_indices_without_merging_stress_variants(self):
        e = entry('<b>meḩer</b> [múḩrul, act moḩrosa, pos muḩrúl] гора́.')
        self.assertEqual(e['forms'], ['meḩer', 'muḩrul', 'moḩrosa', 'muḩrul'])
        self.assertEqual(e['form_stresses'], {'1': 2, '3': 5})
        genitive = next(s for s in e['senses'] if s.get('labels') == ['родительный падеж'])
        self.assertEqual(genitive['forms'], ['muḩrul'])
        self.assertEqual(genitive['form_stresses'], {'0': 5})
        self.assertNotIn('form_stresses', e['senses'][0])
        self.assertNotIn('form_stresses', entry('<b>x</b> [xal] сло́во.'))
        marked = entry('<b>búrtabi</b> сло́во.')
        self.assertEqual(marked['form_stresses'], {'0': 2})

    def test_headword_stress_is_separate_and_uses_output_character_position(self):
        for marked in ('búrtabi', 'bu\u0301rtabi'):
            e = entry('<b>' + marked + '</b> сло́во.')
            self.assertEqual(e['word'], 'burtabi')
            self.assertEqual(e['stress'], 2)
            self.assertEqual(e['forms'], ['burtabi'])
        self.assertEqual(headword_stress('x̨áze'), ('x̨aze', 3))
        self.assertEqual(headword_stress('hèressici'), ('heressici', 2))
        e = entry('<b>meḩer</b> [múḩrul, muḩrúl] гора́.')
        self.assertEqual(e['forms'], ['meḩer', 'muḩrul', 'muḩrul'])
        self.assertEqual(e['form_stresses'], {'1': 2, '2': 5})
        self.assertNotIn('stress', e)
        with self.assertRaises(ValueError):
            headword_stress('á-á')

    def test_stress_variants_remain_separate_articles_and_references_follow(self):
        es = parse('<!-- p010-L --><p><b>búrtabi</b> см. burtábi.</p>'
                   '<p><b>burtábi</b> сло́во.</p>')
        self.assertEqual([e['word'] for e in es], ['burtabi', 'burtabi'])
        self.assertEqual([e['stress'] for e in es], [2, 5])
        self.assertEqual(es[0]['see_also'], [{'target': 'burtabi', 'kind': 'see', 'comment': 'Ударение цели в источнике: burtábi'}])

    def test_canonical_unicode_is_applied_only_to_latin_fields(self):
        e = entry('<b>ḳa</b> [ķal, ḳal] сло́во; x̌a ру́сский.')
        self.assertEqual(e['word'], 'ķa')
        self.assertEqual(e['forms'], ['ķa', 'ķal'])
        self.assertEqual(e['senses'][0]['text'], 'сло́во')
        self.assertEqual(e['senses'][0]['examples'][0]['av'], 'x̵a')
        self.assertEqual(e['senses'][0]['examples'][0]['ru'], 'ру́сский.')
        self.assertEqual(entry('<b>x̨a</b> сло́во.')['word'], 'x̨a')
        self.assertNotEqual(entry('<b>x̨a</b> сло́во.')['word'], e['senses'][0]['examples'][0]['av'])

    def test_optional_headword_letters_become_spelling_forms(self):
        e = entry('<b>ş(v)anţixx</b> [şvanţixxal] сло́во; şvanţixx x приме́р.')
        self.assertEqual(e['word'], 'şvanţixx')
        self.assertEqual(e['spelling_forms'], ['şvanţixx', 'şanţixx'])
        self.assertEqual(e['forms'], ['şvanţixx', 'şanţixx', 'şvanţixxal'])
        self.assertEqual(headword_spellings('bar(a)jka(t)'), ['barajkat', 'barajka', 'barjkat', 'barjka'])
        self.assertEqual(headword_spellings('(b)iline'), ['biline', 'iline'])
        self.assertEqual(headword_spellings('funtal (-sterling)'), ['funtal-sterling', 'funtal'])
        self.assertEqual(headword_spellings('x̵adur(-qo)'), ['x̵adur-qo', 'x̵adur'])
        self.assertEqual(headword_spellings('ļ(ļ)ada...'), ['ļļada...', 'ļada...'])

    def test_parenthetical_abbreviation_and_damaged_heading(self):
        e = entry('<b>Odeen (ODN)</b> r о́бщество.')
        self.assertEqual(e['word'], 'Odeen')
        self.assertEqual(e['spelling_forms'], ['Odeen', 'ODN'])
        self.assertEqual(headword_spellings('piruzia)'), ['piruzia)'])
        self.assertEqual(headword_spellings('piruz(a)'), ['piruza', 'piruz'])
        self.assertEqual(headword_spellings('x((y))'), ['x((y))'])
        self.assertNotIn('spelling_forms', entry('<b>x</b> (редко) сло́во.'))

    def test_reference_to_expanded_heading_uses_canonical_word(self):
        entries = parse('<!-- p010-L -->' +
                        '<p><b>x</b> см. dal(l)ak.</p>' +
                        '<p><b>dal(l)ak</b> сло́во.</p>')
        self.assertEqual(entries[0]['see_also'], [{'target': 'dallak', 'kind': 'see'}])
        self.assertEqual(entries[1]['spelling_forms'], ['dallak', 'dalak'])

    def test_unmarked_forms_and_explicit_case_number_gender(self):
        e = entry('<b>ab</b> [aɫ, <i>act</i> aɫ, <i>act m</i> as, <i>act pl</i> az], <b>abab*</b> э́тот.')
        self.assertEqual(e['forms'], ['ab', 'aɫ', 'as', 'az', 'abab'])
        self.assertIn({'labels': ['эргативный падеж', 'множественное число'], 'forms': ['az']}, e['senses'])
        self.assertIn({'labels': ['эргативный падеж', 'мужской род'], 'forms': ['as']}, e['senses'])
        self.assertEqual(e['senses'][0]['text'], 'э́тот.')
        # Unlabelled bracket contents can contain several grammatical categories.
        self.assertNotIn('множественное число', entry('<b>x</b> [xal] сло́во.')['senses'][0].get('labels', []))

    def test_missing_comma_and_inherited_case(self):
        e = entry('<b>aħi</b> [aħabi, act aħusa all aħude, aħud, aħuṭe] крик.')
        self.assertIn({'labels': ['направительный падеж'], 'forms': ['aħude', 'aħud', 'aħuţe']}, e['senses'])
        self.assertIn({'labels': ['эргативный падеж'], 'forms': ['aħusa']}, e['senses'])

    def test_origin_abbreviations(self):
        for code, label in ORIGINS.items():
            with self.subTest(code=code):
                e = entry(f'<b>x</b> [xal] <i>{code}</i> сло́во.')
                self.assertEqual(e['senses'][0]['labels'], [label])
                self.assertEqual(e['senses'][0]['text'], 'сло́во.')

    def test_references_and_example_scope(self):
        e = entry('<b>x</b> = y; <i>см.</i> z; x h. де́лать (<i>ср.</i> a, b).')
        self.assertIn({'target': 'y', 'kind': 'spelling'}, e['see_also'])
        self.assertIn({'target': 'z', 'kind': 'see'}, e['see_also'])
        self.assertIn({'target': 'a', 'kind': 'compare'}, e['see_also'])
        self.assertEqual(e['senses'][0]['examples'][0], {'av': 'x h.', 'ru': 'де́лать.'})
        e = entry('<b>x</b> сло́во; x y = z.')
        self.assertNotIn('examples', e['senses'][0])
        self.assertEqual(e['see_also'], [{'target': 'z', 'kind': 'spelling', 'comment': 'Отсылка при выражении: x y'}])
        e = entry('<b>aħahize</b> = aħize <i>frequ.</i>')
        self.assertEqual(e['see_also'], [{'target': 'aħize', 'kind': 'spelling'}])
        self.assertEqual(e['senses'][0]['labels'], ['учащательная форма'])

    def test_russian_word_across_paragraph_and_page_break(self):
        es = parse('<!-- p054 --><p><b>ħeleko</b> пе-</p><!-- p055 --><p>ту́х.</p>')
        self.assertEqual(es[0]['senses'][0]['text'], 'пету́х.')
        e = entry('<b>x</b> пу́говица (в игре),; x h. делать.')
        self.assertEqual(e['senses'][0]['text'], 'пу́говица')

    def test_reference_chains_and_nested_optional_letters(self):
        e = entry('<b>x</b> = ab(in), см. a; ср. b, c.')
        self.assertEqual(e['see_also'], [
            {'target': 'ab(in)', 'kind': 'spelling'},
            {'target': 'a', 'kind': 'see'},
            {'target': 'b', 'kind': 'compare'},
            {'target': 'c', 'kind': 'compare'}])
        self.assertNotIn('senses', e)
        e = entry('<b>x</b> (ср. y) сло́во (= пояснение).')
        self.assertEqual(e['see_also'], [{'target': 'y', 'kind': 'compare'}])
        self.assertIn('пояснение', e['senses'][0]['comment'])
        e = entry('<b>x</b> [ср. y] = z frequ.')
        self.assertEqual(e['see_also'][0]['kind'], 'compare')
        self.assertEqual(e['see_also'][1]['kind'], 'spelling')
        self.assertIn('учащательная форма', e['senses'][0]['labels'])

    def test_equal_before_russian_gloss_is_a_real_example(self):
        e = entry('<b>x</b> сло́во; x h. = делать.')
        self.assertEqual(e['senses'][0]['examples'], [{'av': 'x h.', 'ru': 'делать.'}])
        e = entry('<b>x</b> = неразобранное.')
        self.assertFalse(any(not e.get('av') for s in e.get('senses', []) for e in s.get('examples', [])))

    def test_examples_and_local_case_labels(self):
        e = entry('<b>badib</b> (l5) на лице́; badibe* (al5) на лицо́; badisa (el5) с лица́.')
        sense = e['senses'][0]
        self.assertEqual(sense['labels'], ['местный падеж', '5-я серия'])
        self.assertEqual(sense['examples'][0]['labels'], ['направительный падеж', '5-я серия'])
        self.assertEqual(sense['examples'][1]['labels'], ['исходный падеж', '5-я серия'])

    def test_qualifiers_stay_with_their_meanings(self):
        e = entry('<b>x</b> i подпи́ска (на газе́ту); абонеме́нт (на телефо́н); x h. подписа́ться.')
        self.assertEqual(e['senses'][0]['comment'], 'на газе́ту')
        self.assertEqual(e['senses'][1]['comment'], 'на телефо́н')
        self.assertEqual(e['senses'][1]['examples'][0]['av'], 'x h.')
        e = entry('<b>x</b> (то, что) ну́жно сказа́ть.')
        self.assertEqual(e['senses'][0]['precomment'], 'то, что')

    def test_optional_letters_are_not_grammatical_annotations(self):
        e = entry('<b>dal(l)ak</b> [dal(l)akal, act ṭorṣṣ(al)isa] сло́во; mix(al)çaħa длинноу́сый; qu(l)tux табаке́рка; ħam(m)ab о́бщий.')
        self.assertEqual(e['forms'], ['dallak', 'dalak', 'dal(l)akal', 'ţorṣṣ(al)isa'])
        self.assertEqual([x['av'] for x in e['senses'][0]['examples']], ['mix(al)çaħa', 'qu(l)tux', 'ħam(m)ab'])

    def test_missing_separator_before_related_examples(self):
        e = entry('<b>banderol</b> бандеро́ль zakaz-banderol заказна́я бандеро́ль banderol habun bitize отправля́ть бандеро́лью.')
        self.assertEqual(e['senses'][0]['text'], 'бандеро́ль')
        self.assertEqual([x['av'] for x in e['senses'][0]['examples']], ['zakaz-banderol', 'banderol habun bitize'])

    def test_ocr_case_code_and_optional_russian_prefix(self):
        e = entry('<b>labda</b> (11) на косого́ре; labda h. (за)пуска́ть волчо́к.')
        self.assertEqual(e['senses'][0]['text'], 'на косого́ре')
        self.assertEqual(e['senses'][0]['labels'], ['местный падеж', '1-я серия'])
        self.assertEqual(e['senses'][0]['examples'][0], {'av': 'labda h.', 'ru': '(за)пуска́ть волчо́к.'})

    def test_variant_qualifier_does_not_apply_to_whole_entry(self):
        e = entry('<b>buḳine</b>, buḳinze (ре́дко), buḳize (ре́дко) быть.')
        self.assertNotIn('labels', e['senses'][0])
        self.assertIn({'labels': ['редко'], 'forms': ['buķinze', 'buķize']}, e['senses'])

    def test_ocr_case_and_origin_labels_keep_the_actual_forms(self):
        e = entry('<b>ceх̣</b> [ceх̣al, 15 coх̣onib] l живо́т.')
        self.assertIn('ceх̣al', e['forms'])
        self.assertIn({'labels': ['местный падеж', '5-я серия'], 'forms': ['coх̣onib']}, e['senses'])
        self.assertIn('интернациональный термин', e['senses'][0]['labels'])
        e = entry('<b>x</b> [unknown 99] сло́во.')
        self.assertIn('unknown 99', e['senses'][0]['comment'])

    def test_form_qualifiers_and_bracketed_reference(self):
        e = entry('<b>emen</b> [act imssusa (ре́дко) emenas (в го́воре Чирке́я)] оте́ц.')
        self.assertIn({'labels': ['эргативный падеж', 'редко'], 'forms': ['imssusa']}, e['senses'])
        self.assertIn({'labels': ['эргативный падеж'], 'forms': ['emenas'], 'comment': 'в го́воре Чирке́я'}, e['senses'])
        e = entry('<b>x</b> [cp. y] сло́во.')
        self.assertEqual(e['see_also'], [{'target': 'y', 'kind': 'compare'}])

    def test_confirmed_da_plural(self):
        es = parse((ROOT / 'books/av-ru.1936/av-ru.1936.html').read_text())
        e = next(e for e in es if e['word'] == 'da' and 'dabal' in e['forms'])
        self.assertIn({'labels': ['множественное число'], 'forms': ['dabi', 'dabal']}, e['senses'])

    def test_verified_ocr_distinctions_survive_rebuild(self):
        es = parse((ROOT / 'books/av-ru.1936/av-ru.1936.html').read_text())
        words = {e['word'] for e in es}
        self.assertTrue({'ƣumuq', 'qvarid', 'ƣvarid', 'ƣocax', 'ḩabdal-maħab', 'ħil', 'ⱬil'} <= words)
        self.assertNotIn('ƣumuƣ', words)
        field = next(e for e in es if e['word'] == 'ḩalax')
        self.assertIn('ħajvan', json.dumps(field, ensure_ascii=False))
        for word in ('ḩureţ', 'ḩvereţ'):
            e = next(e for e in es if e['word'] == word)
            self.assertTrue(any({'местный падеж', '5-я серия'} <= set(s.get('labels', [])) for s in e.get('senses', [])))

    def test_equality_inside_russian_explanation_is_not_example_delimiter(self):
        e = entry('<b>anⱬ</b> де́сять; anⱬilla де́сять (с едини́цами, напр. anⱬilla-kigo = 12).')
        example = e['senses'][0]['examples'][0]
        self.assertEqual(example['av'], 'anⱬilla')
        self.assertIn('anⱬilla-kigo = 12', example['comment'])
        e = entry('<b>qoloni-lab</b> 1/8 кали́ (ме́ра ёмкости).')
        self.assertNotIn('examples', e['senses'][0])
        self.assertIn('1/8 кали́', e['senses'][0]['text'])

    def test_latin_heading_paradigm_can_precede_russian_continuation(self):
        es = parse('<!-- p040 --><p><b>fotograf</b> [fotografal, fotografzabi]</p><p>i фото́граф.</p>')
        self.assertEqual(len(es), 1)
        self.assertEqual(es[0]['word'], 'fotograf')
        self.assertIn('fotografzabi', es[0]['forms'])
        self.assertIn('интернациональный термин', es[0]['senses'][0]['labels'])

    def test_no_cyrillic_in_latin_fields_and_restored_headings(self):
        from audit_zhirkov_1936_alphabet import audit
        es = parse((ROOT / 'books/av-ru.1936/av-ru.1936.html').read_text())
        self.assertFalse([f for f in audit(es) if f['cyrillic']])
        by_word = {e['word']: e for e in es}
        self.assertTrue({'fotograf', 'majdan', 'ⱬⱬomor', 'eb', 'Bolƣarija', 'uborşşissa'} <= by_word.keys())
        self.assertIn('ebab', by_word['eb']['forms'])
        self.assertNotIn('фото́граф', json.dumps(by_word['fosfor'], ensure_ascii=False))

    def test_paradigm_can_close_on_next_page(self):
        es = parse('<!-- p138 --><p><b>ƶerƣen</b> бу́бен.</p>'
                   '<p><b>ƶib</b> [ƶal, <i>act</i> ƶinsa, <i>dat</i></p>'
                   '<!-- p139 --><p>ƶindij(e)] сам, он.</p>')
        self.assertEqual([e['word'] for e in es], ['ƶerƣen', 'ƶib'])
        self.assertEqual(es[0]['senses'][0]['text'], 'бу́бен.')
        self.assertIn('ƶal', es[1]['forms'])
        self.assertIn('ƶindij(e)', es[1]['forms'])

    def test_paradigm_word_hyphenated_across_column(self):
        es = parse('<!-- p050 --><p><b>hobo</b> [habal, <i>pos</i> ha-</p>'
                   '<p>bil] жёрнов.</p>')
        self.assertEqual(es[0]['word'], 'hobo')
        self.assertIn('habil', es[0]['forms'])
        self.assertNotIn('ha- bil', es[0]['forms'])

    def test_headword_combining_mark_outside_bold_span(self):
        e = entry('<b>ƣajix</b>̵ [ƣajix̵al] t ло́дка.')
        self.assertEqual(e['word'], 'ƣajix̵')
        self.assertIn('ƣajix̵al', e['forms'])
        self.assertNotIn('examples', e['senses'][0])

    def test_scan_order_and_continuations(self):
        html = '<!-- p007 --><p><b>x</b> нача́ло</p><!-- p008 --><p>введе́ние</p><!-- p010 --><p>продолже́ние.</p><!-- p143 --><p><b>y</b> грамма́тика.</p>'
        es = parse(html)
        self.assertEqual(len(es), 1)
        self.assertEqual(es[0]['senses'][0]['text'], 'нача́ло продолже́ние.')

    def test_whole_source_keeps_boundaries_and_lexical_tokens(self):
        raw = articles((ROOT / 'books/av-ru.1936/av-ru.1936.html').read_text())
        self.assertEqual(len(raw), 7027)
        allowed = set(GRAMMAR) | set(ORIGINS) | set(ORIGIN_GLYPHS) | set(CODE_ALIASES) | {'см', 'ср', 'cp'}
        allowed |= set(' '.join(RUSSIAN_LABELS).split())
        for article in raw:
            e = structure(article)
            spellings = headword_spellings(article['word'])
            self.assertEqual(e['word'], headword_stress(spellings[0])[0])
            # Optional pieces are joined into words, not lost lexical tokens.
            normalized_source = re.sub(r'(?<!\w)' + re.escape(article['word']) + r'(?!\w)', lambda _: ' '.join(spellings), article['text'])
            original = set(re.findall(r'\w+', unaccent(unicodedata.normalize('NFD', normalized_source))))
            result = set(re.findall(r'\w+', unaccent(unicodedata.normalize('NFD', ' '.join(strings(e))))))
            missing = {t for t in original - result if t not in allowed and not re.fullmatch(r'(?:al|el|l)[1-5]', t)}
            self.assertFalse(missing, (article['word'], missing))
            self.assertFalse([ex for sense in e.get('senses', []) for ex in sense.get('examples', []) if not ex.get('av')])
            self.assertFalse([sense for sense in e.get('senses', []) if 'text' in sense and not sense['text']])
            self.assertEqual(e['forms'][0], e['word'])
            self.assertEqual(e['source'], 'av-ru.1936')
            for block in [e] + e.get('senses', []):
                for form in block.get('forms', []):
                    self.assertFalse(any(mark in unicodedata.normalize('NFD', form) for mark in '\u0301\u0300'))
                for index, position in block.get('form_stresses', {}).items():
                    self.assertRegex(index, r'^(0|[1-9][0-9]*)$')
                    self.assertLess(int(index), len(block['forms']))
                    form = block['forms'][int(index)]
                    self.assertGreaterEqual(position, 1)
                    self.assertLessEqual(position, len(form))
                    self.assertIn(form[position - 1].lower(), 'aeiou')


if __name__ == '__main__':
    unittest.main()
