import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from parse_zhirkov_1936 import (
    GRAMMAR, ORIGINS, ORIGIN_GLYPHS, RUSSIAN_LABELS,
    articles, parse, structure, unaccent,
)


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
        self.assertIn({'labels': ['направительный падеж'], 'forms': ['aħude', 'aħud', 'aħuṭe']}, e['senses'])
        self.assertIn({'labels': ['эргативный падеж'], 'forms': ['aħusa']}, e['senses'])

    def test_origin_abbreviations(self):
        for code, label in ORIGINS.items():
            with self.subTest(code=code):
                e = entry(f'<b>x</b> [xal] <i>{code}</i> сло́во.')
                self.assertEqual(e['senses'][0]['labels'], [label])
                self.assertEqual(e['senses'][0]['text'], 'сло́во.')

    def test_references_and_example_scope(self):
        e = entry('<b>x</b> = y; <i>см.</i> z; x h. де́лать (<i>ср.</i> a, b).')
        self.assertIn({'target': 'y', 'kind': 'syn'}, e['see_also'])
        self.assertIn({'target': 'z', 'kind': 'see'}, e['see_also'])
        self.assertIn({'target': 'a', 'kind': 'see'}, e['see_also'])
        self.assertEqual(e['senses'][0]['examples'][0], {'av': 'x h.', 'ru': 'де́лать.'})
        e = entry('<b>x</b> сло́во; x y = z.')
        self.assertEqual(e['senses'][0]['examples'], [{'av': 'x y', 'comment': '= z.'}])
        self.assertNotIn('see_also', e)
        e = entry('<b>aħahize</b> = aħize <i>frequ.</i>')
        self.assertEqual(e['see_also'], [{'target': 'aħize', 'kind': 'from'}])
        self.assertEqual(e['senses'][0]['labels'], ['учащательная форма'])

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
        self.assertEqual(e['forms'], ['dal(l)ak', 'dal(l)akal', 'ṭorṣṣ(al)isa'])
        self.assertEqual([x['av'] for x in e['senses'][0]['examples']], ['mix(al)çaħa', 'qu(l)tux', 'ħam(m)ab'])

    def test_missing_separator_before_related_examples(self):
        e = entry('<b>banderol</b> бандеро́ль zakaz-banderol заказна́я бандеро́ль banderol habun bitize отправля́ть бандеро́лью.')
        self.assertEqual(e['senses'][0]['text'], 'бандеро́ль')
        self.assertEqual([x['av'] for x in e['senses'][0]['examples']], ['zakaz-banderol', 'banderol habun bitize'])

    def test_unknown_case_code_is_not_an_example_and_optional_russian_prefix(self):
        e = entry('<b>labda</b> (11) на косого́ре; labda h. (за)пуска́ть волчо́к.')
        self.assertEqual(e['senses'][0]['text'], 'на косого́ре')
        self.assertIn('(11)', e['senses'][0]['comment'])
        self.assertEqual(e['senses'][0]['examples'][0], {'av': 'labda h.', 'ru': '(за)пуска́ть волчо́к.'})

    def test_variant_qualifier_does_not_apply_to_whole_entry(self):
        e = entry('<b>buḳine</b>, buḳinze (ре́дко), buḳize (ре́дко) быть.')
        self.assertNotIn('labels', e['senses'][0])
        self.assertIn({'labels': ['редко'], 'forms': ['buḳinze', 'buḳize']}, e['senses'])

    def test_uncertain_ocr_is_preserved(self):
        e = entry('<b>ceх̣</b> [ceх̣al, 15 coх̣onib] l живо́т.')
        self.assertIn('ceх̣al', e['forms'])
        self.assertIn('15 coх̣onib', e['senses'][0]['comment'])
        self.assertIn('Неоднозначная помета источника: l', e['senses'][0]['comment'])
        self.assertNotIn('интернациональный термин', e['senses'][0].get('labels', []))

    def test_scan_order_and_continuations(self):
        html = '<!-- p007 --><p><b>x</b> нача́ло</p><!-- p008 --><p>введе́ние</p><!-- p010 --><p>продолже́ние.</p><!-- p143 --><p><b>y</b> грамма́тика.</p>'
        es = parse(html)
        self.assertEqual(len(es), 1)
        self.assertEqual(es[0]['senses'][0]['text'], 'нача́ло продолже́ние.')

    def test_whole_source_keeps_boundaries_and_lexical_tokens(self):
        raw = articles((ROOT / 'books/av-ru.1936/av-ru.1936.html').read_text())
        self.assertEqual(len(raw), 7023)
        allowed = set(GRAMMAR) | set(ORIGINS) | set(ORIGIN_GLYPHS) | {'см', 'ср', 'cp'}
        allowed |= set(' '.join(RUSSIAN_LABELS).split())
        for article in raw:
            e = structure(article)
            self.assertEqual(e['word'], article['word'])
            original = set(re.findall(r'\w+', unaccent(article['text'])))
            result = set(re.findall(r'\w+', unaccent(' '.join(strings(e)))))
            missing = {t for t in original - result if t not in allowed and not re.fullmatch(r'(?:al|el|l)[1-5]', t)}
            self.assertFalse(missing, (article['word'], missing))
            self.assertEqual(e['forms'][0], e['word'])
            self.assertEqual(e['source'], 'av-ru.1936')


if __name__ == '__main__':
    unittest.main()
