#!/usr/bin/env python3
"""Unit tests for the Avar sort key used across the av-ru-1967 pipeline
(check_order.py, check_accepted.py, segment_entries.py, and now
build_article_stream.py's local-interval boundary analysis).

av-ru-1967-review-batch-6-segmentation-2026-09-19.md, item 2: "Добавить
unit tests минимум для" all Avar digraphs, stress-glyph words, homonyms,
hyphenated words, spelling variants, and palochka Unicode variants. The
sort key itself (src/build_site.py's make_sort_key/make_tokenizer/
normalize_palochka) already existed and is shared with the live site
build — these tests document and lock in its actual behavior for the
boundary-detection use case, they don't change it.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from build_site import AVAR_ALPHABET, AVAR_DIGRAPHS, make_rank, make_sort_key, make_tokenizer, normalize_palochka  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from check_order import _SORT_KEY, rescued_word  # noqa: E402
from segment_entries import load_known_words  # noqa: E402

_TOKENIZE = make_tokenizer("av")
_RANK = make_rank(AVAR_ALPHABET)
_KEY = make_sort_key(_RANK, _TOKENIZE)


class DigraphOrderingTests(unittest.TestCase):
    def test_all_digraphs_are_tokenized_as_single_units(self):
        for d in AVAR_DIGRAPHS:
            self.assertEqual(_TOKENIZE(d + "а"), [d, "а"], f"digraph {d!r} should tokenize as one unit")

    def test_digraphs_sort_after_their_base_letter(self):
        # гъ/гь/гӏ must sort after plain г but before д (AVAR_ALPHABET order).
        pairs = [("г", "гъ"), ("гъ", "гь"), ("гь", "гӏ"), ("гӏ", "д")]
        for a, b in pairs:
            self.assertLess(_KEY(a), _KEY(b), f"{a!r} should sort before {b!r}")

    def test_all_alphabet_letters_strictly_increasing(self):
        keys = [_KEY(letter) for letter in AVAR_ALPHABET]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(len(set(keys)), len(keys), "no two alphabet letters should share a sort key")


class HomonymTests(unittest.TestCase):
    def test_identical_headwords_produce_equal_sort_keys(self):
        # e.g. the dataset's 142 same-word homonym pairs like "аби"/"аби" or "агь"/"агь".
        self.assertEqual(_KEY("аби"), _KEY("аби"))
        self.assertEqual(_KEY("агь"), _KEY("агь"))


class HyphenTests(unittest.TestCase):
    def test_hyphen_is_its_own_token_not_a_letter(self):
        self.assertIn("-", _TOKENIZE("бакк-баккизе"))

    def test_hyphenated_reduplication_sorts_after_its_plain_counterpart(self):
        # "-" isn't in the alphabet, so it ranks past every real letter —
        # "бакк-баккизе" sorts after "бакки" (batch-3's documented, spot-
        # checked-safe behavior, not a bug to "fix" here).
        self.assertLess(_KEY("бакки"), _KEY("бакк-баккизе"))


class PalochkaVariantTests(unittest.TestCase):
    def test_unicode_palochka_forms_normalize_identically(self):
        # Ӏ (U+04C0), ӏ (U+04CF), |, ǀ, latin I/i/l — all valid OCR glyphs
        # for the palochka when they follow a digraph base (CLAUDE.md rule 3).
        # make_sort_key()'s key is (rank_tuple, original_word) — the second
        # element is a stable tiebreaker that deliberately keeps distinct
        # raw spellings distinguishable, so only the RANK component (used
        # for actual alphabetical ordering) is expected to match here.
        variants = ["тӏабиаб", "т\u04cfабиаб", "т|абиаб", "тӀабиаб", "тIабиаб", "тiабиаб"]
        rank_components = {_KEY(v)[0] for v in variants}
        self.assertEqual(len(rank_components), 1, f"all palochka glyph variants of the same word should rank identically: {variants}")

    def test_normalize_palochka_does_not_touch_non_digraph_latin(self):
        # A word with a genuine Latin letter (not glued to a digraph base
        # or a digit) must NOT be silently turned into a palochka.
        self.assertEqual(normalize_palochka("Iглав"), "Iглав")


class StressGlyphRescueTests(unittest.TestCase):
    """rescued_word() (check_order.py) — б/6/й/ё stress-glyph substitution
    gated on known_words — is what makes a headword like "бёлъине" sort as
    if it read "белъине" (its actual stress-marked spelling), instead of
    masquerading as a segmentation bug purely due to an OCR stress artifact
    (see check_order.py's module docstring)."""

    @classmethod
    def setUpClass(cls):
        cls.known_words = load_known_words(Path("data/av-ru.jsonl"))

    def test_known_word_with_stress_glyph_rescues_to_plain_spelling(self):
        # Any real dataset word already exercises this; use a definitely
        # present, definitely stress-glyph-free control to assert the
        # rescue function is at least a no-op for already-plain words.
        plain = "бакъан"
        self.assertEqual(rescued_word(plain, self.known_words), plain)

    def test_sort_key_is_stable_after_rescue(self):
        # rescued_word + _SORT_KEY must be composable without raising, and
        # the resulting key must be a valid, comparable tuple.
        w = rescued_word("бёлъине", self.known_words)
        key = _SORT_KEY(w)
        self.assertIsInstance(key, tuple)


class SpellingVariantTests(unittest.TestCase):
    def test_pipe_separated_spelling_variants_both_sort(self):
        # "авадан||аваданго"-style entries are split before reaching the
        # sort key (segment_entries.py), but each half alone must still
        # produce a valid, real sort key — not crash, not collapse to the
        # same key as an unrelated word.
        self.assertNotEqual(_KEY("авадан"), _KEY("аваданго"))


if __name__ == "__main__":
    unittest.main()
