#!/usr/bin/env python3
"""Structural + sense-level import of the Saidov 1967 Avar-Russian dictionary.

Source: `books/av-ru.1967/av-ru.1967.html` (OCR, already modern Avar
Cyrillic -- no transliteration needed, unlike av-ru.1936).

Second pass (01.11.2026): breaks the single raw `text` string from the
first pass into `senses`/`labels`/`see_also`, following the same field
names already used by `data/av-ru.jsonl` (av-ru.2006) for this exact
grammatical vocabulary -- `masdarfrom`, `pluralfor`, `genitivefrom`,
`participlefrom`, labels like "понудительная форма"/"учащательная
форма", `comment: "от 'X'"` -- since Saidov 1967 and the 2006 dictionary
share the same lexicographic convention for marking derived forms.

Not attempted (known limitation, see books/av-ru.1967/README.md):
splitting an Avar example phrase from its Russian translation within a
sense. Unlike av-ru.1936 (Latin Avar vs Cyrillic Russian, trivially
distinguishable), both are Cyrillic here, so this would need a lexical
Avar/Russian classifier rather than a structural rule; a sense's `text`
may still contain multiple ';'-joined examples and glosses together.

Scope: only the main alphabetic dictionary (printed pages 23-632, "а"
through "япон ралъад"). The toponymic appendix (633-704, re-alphabetized
per village, with visibly column-scrambled OCR in its own front matter)
and the appended grammar sketch (705 onward) are out of scope for this
import; see the README for why.
"""

import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "av-ru.1967"
FIRST_PAGE, LAST_PAGE = 23, 632


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append(" ")


def plain(fragment):
    parser = PlainText()
    parser.feed(fragment)
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()


def unaccent(text):
    return text.replace("́", "").replace("̀", "")


def headword_stress(word):
    """Return NFC spelling and a one-based code-point position of its
    single stress accent, or None if the word carries no accent."""
    nfd = unicodedata.normalize("NFD", word)
    if "́" not in nfd and "̀" not in nfd:
        return unicodedata.normalize("NFC", word), None
    clusters = re.findall(r"[^̀-ͯ][̀-ͯ]*", nfd)
    output, positions = "", []
    for cluster in clusters:
        accented = "́" in cluster or "̀" in cluster
        clean = unicodedata.normalize("NFC", unaccent(cluster))
        if accented:
            positions.append(len(output) + 1)
        output += clean
    stress = positions[0] if len(positions) == 1 else None
    return output, stress


# --- Headword extraction -----------------------------------------------

# A sense number is sometimes typeset bold together with the headword
# itself (<b>хъали́къаб 1)</b>), which would otherwise leak into `word`.
TRAILING_NUMBERING_RE = re.compile(r"(?:\s+\d+[.)])+$")
# Roman-numeral homonym marker printed right after the headword
# (авал I / авал II) -- a real, distinct-word marker, unlike the above.
HOMONYM_RE = re.compile(r"^(.*\S)\s+(I{1,3})$")


def articles(html):
    """Keep article boundaries from the source order; page range limits
    this to the main alphabetic dictionary, not the appendices."""
    result, page = [], 0
    for match in re.finditer(r'<p class="page-num" id="p(\d+)">|<p>(.*?)</p>', html, re.S):
        if match[1]:
            page = int(match[1])
            continue
        if not (FIRST_PAGE <= page <= LAST_PAGE):
            continue
        fragment = match[2]
        text = plain(fragment)
        if not text:
            continue
        # The class-marker asterisk is typeset inconsistently: sometimes
        # before the bold span (*<b>word</b>), sometimes inside it
        # (<b>*word</b>).
        bold = re.match(r"\s*(\*?)\s*<b>(.*?)</b>", fragment, re.S)
        # A long article is occasionally split across two <p> tags in the
        # source with no page break between them, and the second <p> opens
        # with a bare sub-sense number in bold ("<p><b>3)</b> перен. дать
        # ...</p>") -- not a new headword, just that number continuing the
        # previous article's numbering.
        is_bare_sense_number = bool(bold) and re.fullmatch(r"\d+[.)]", plain(bold[2]))
        if bold and not is_bare_sense_number and re.search(r"[А-Яа-яЁё]", text):
            raw_heading = plain(bold[2])
            star = bool(bold[1]) or raw_heading.startswith("*")
            raw_heading = raw_heading.lstrip("*")
            heading = TRAILING_NUMBERING_RE.sub("", raw_heading).strip()
            heading = heading.split(",", 1)[0].split("||", 1)[0].strip()
            homonym = None
            hmatch = HOMONYM_RE.match(heading)
            if hmatch:
                heading, homonym = hmatch[1], len(hmatch[2])
            word, stress = headword_stress(heading)
            spelling_forms = None
            if "||" in raw_heading:
                variant_source = TRAILING_NUMBERING_RE.sub("", raw_heading).strip()
                variants = [unaccent(v).strip() for v in variant_source.split("||")]
                spelling_forms = [unaccent(word)] + [v for v in variants[1:] if v]
            # `text` (the whole flattened paragraph) always starts with this
            # exact prefix, since PlainText() emits the bold span's own text
            # first; used later to recover everything *after* the headword.
            heading_prefix = ("*" if bold[1] else "") + plain(bold[2])
            # Raw (unflattened) HTML after the headword -- preserves the
            # <b>/<i> markup the book itself uses to distinguish Avar text
            # from Russian prose and grammatical labels (bold = Avar,
            # italic = label/comment, plain = Russian translation).
            body_html = fragment[bold.end():]
            entry = {"word": word, "text": text, "heading_prefix": heading_prefix, "body_html": body_html, "page": page}
            if stress is not None:
                entry["stress"] = stress
            if star:
                entry["class_marker"] = True
            if homonym:
                entry["homonym"] = homonym
            if spelling_forms:
                entry["spelling_forms"] = spelling_forms
            result.append(entry)
        else:
            if not result:
                raise ValueError(f"Orphan continuation on page {page}: {text}")
            previous = result[-1]["text"]
            if previous.endswith("-") and re.search(r"[а-яё]́?-$", previous) and re.match(r"[а-яё]", text):
                result[-1]["text"] = previous[:-1] + text
            else:
                result[-1]["text"] += " " + text
            result[-1]["body_html"] = result[-1].get("body_html", "") + " " + fragment
    return result


# --- Gender-form derivation for the class-marker asterisk ---------------


def derive_gender_forms(word):
    """Regular б/в/й class-agreement triple for adjective/pronoun-shaped
    headwords (the same alternation av-ru.2006 stores explicitly in
    `gender_forms`, e.g. абадияб/абадияв/абадияй). Only safe for words
    ending in -б: many class-marker headwords are verbs or already a
    single gendered noun (абазинав "male Abazin"), where no regular
    triple exists -- those keep the plain `class_marker` flag instead."""
    if len(word) > 1 and word[-1] == "б":
        stem = word[:-1]
        return [word, stem + "в", stem + "й"]
    return None


# --- Sense splitting ------------------------------------------------------

CASE_LABEL_RE = re.compile(
    r"(?:\d+-го\s+скл\.|род\.\s*п\.|эрг\.\s*п\.|местн\.\s*п\.|мн\.|ед\.|повел\.|прич\.|"
    r"прош\.\s*вр\.|буд\.\s*вр\.|наст\.\s*вр\.|общ\.\s*вр\.)\s*",
    re.I,
)
RELATION_BRACKET_RE = re.compile(
    r"^((?:прич\.|масд\.|понуд\.|учащ\.|повел\.|прош\.\s*вр\.|буд\.\s*вр\.|наст\.\s*вр\.|общ\.\s*вр\.)[^,;]*?)"
    r"\s+(?:от|глагола)\s+(\S.*)$"
)
# A single word/token for a cross-reference target: excludes the punctuation
# that can immediately follow it in prose (comma, period, semicolon), so a
# greedy match can never swallow less than the whole token -- unlike `\S+?`,
# whose laziness stops at the first character once everything after it in
# the pattern is optional (confirmed bug: truncated "ине" to "и").
TOKEN = r"[^\s,.;]+"


def strip_stress(text):
    return unicodedata.normalize(
        "NFC", "".join(ch for ch in unicodedata.normalize("NFD", text) if ch not in "́̀")
    )


def parse_headword_bracket(content):
    """A `[...]` note right after the headword is either a relation to
    another word (`[прич. от къазе]`) or a list of this word's own
    inflected forms (`[род. п. алъу́л]`, `[род. п. X; мн. Y]`).

    Only recognized when a known case/form label is present: unlabeled
    bracket content (seen once, from an OCR-mangled page-wrap entry) is
    reported as unknown rather than guessed at, so garbage prose is not
    silently misfiled as a word form."""
    relation = RELATION_BRACKET_RE.match(content)
    if relation:
        return {"kind": "relation", "label": relation[1].strip(), "target": strip_stress(relation[2].strip().rstrip("."))}
    if not CASE_LABEL_RE.search(content):
        return {"kind": "unknown"}
    cleaned = CASE_LABEL_RE.sub("", content)
    forms = []
    for part in re.split(r"[;,]", cleaned):
        for piece in part.split("||"):
            piece = strip_stress(piece.strip())
            if piece:
                forms.append(piece)
    return {"kind": "forms", "forms": forms}


# --- Tag-aware segmentation ------------------------------------------
#
# The book's own typesetting already marks the Avar/Russian boundary that
# flattened text throws away: bold is Avar (headword, example phrases,
# cross-reference targets, cited word forms), italic is a grammatical
# label or comment, and plain text is the Russian translation. Confirmed
# on a random sample of paragraphs and corpus-wide: 75% of ';'-separated
# clauses in the main dictionary start with a bold run.

RUN_RE = re.compile(r"<b>(.*?)</b>|<i>(.*?)</i>|<br\s*/?>|(</?[a-zA-Z][^>]*>)|([^<]+)", re.S)
# Connector words a plain run can be made of while still not being a real
# translation (e.g. "<b>адаб тезе</b> или <b>адаб рехизе</b> преступить
# границы приличия" -- the shared gloss comes after the *second* bold
# phrase, not after "или"). Rare (survives filtering only ~15 times in
# the whole book) but cheap to guard against.
_CONNECTOR_WORDS = {"и", "а", "но", "или", "да", "же", "ли"}


def tag_runs(fragment):
    """Tokenize one HTML fragment into (kind, text) runs, kind in
    {"b", "i", "t"}; adjacent runs of the same kind are merged. A stray
    unmatched closing tag (e.g. a lone `</b>` left behind when a bold span
    is hyphen-split across a page boundary the OCR pipeline did not
    rejoin, a known, rare OCR defect -- see the README) is silently
    dropped rather than leaking as literal `</b>`-shaped text."""
    runs = []
    for m in RUN_RE.finditer(fragment):
        if m[1] is not None:
            kind, content = "b", plain(m[1])
        elif m[2] is not None:
            kind, content = "i", plain(m[2])
        elif m[0].startswith("<br"):
            kind, content = "t", " "
        elif m[3] is not None:
            continue  # stray tag, no run
        else:
            kind, content = "t", plain(m[4])
        if not content:
            continue
        if runs and runs[-1][0] == kind:
            runs[-1] = (kind, (runs[-1][1] + " " + content).strip())
        else:
            runs.append((kind, content))
    return runs


def _isolate_embedded_markers(runs, suffix):
    """A sense number is usually its own bold span, but the typesetting is
    inconsistent in two ways: sometimes only the *major* marker ("1.") is
    bold and the sub-markers ("1)", "2)") are plain text glued into the
    following "t" run (confirmed on "ратизе": `<b>1.</b> 1) быть ...; 2)
    находиться ...`); sometimes a major and sub marker are glued together
    into *one* bold span (confirmed on "рагьизе": `<b>1. 1)</b> открываться
    ...`). Split any such marker out into its own run first (kind
    preserved), so the check below can find it regardless of kind or of
    what it was printed next to."""
    marker_re = re.compile(r"(?<![\d.)])\d+" + re.escape(suffix) + r"(?=\s|$)")
    out = []
    for kind, content in runs:
        if not marker_re.search(content):
            out.append((kind, content))
            continue
        pos = 0
        for m in marker_re.finditer(content):
            before = content[pos:m.start()].strip()
            if before:
                out.append((kind, before))
            out.append((kind, m[0]))
            pos = m.end()
        after = content[pos:].strip()
        if after:
            out.append((kind, after))
    return out


def split_runs_on_markers(runs, suffix):
    """Same counting rule as `split_markers`, but matching a run that is
    nothing but the marker itself -- bold most of the time, but see
    `_isolate_embedded_markers` for the plain-text exception."""
    runs = _isolate_embedded_markers(runs, suffix)
    accepted, expected = [], None
    for i, (kind, content) in enumerate(runs):
        if kind not in ("b", "t") or not re.fullmatch(r"\d+" + re.escape(suffix), content):
            continue
        num = int(content[:-1])
        if expected is None:
            if num in (1, 2):
                accepted.append(i)
                expected = num + 1
        elif num == expected:
            accepted.append(i)
            expected += 1
    if not accepted:
        return [runs] if runs else []
    chunks = []
    head = runs[: accepted[0]]
    if any(c for _, c in head):
        chunks.append(head)
    for j, idx in enumerate(accepted):
        end = accepted[j + 1] if j + 1 < len(accepted) else len(runs)
        chunk = runs[idx + 1 : end]
        if any(c for _, c in chunk):
            chunks.append(chunk)
    return chunks


def split_leaf_runs(runs):
    leaves = []
    for major in split_runs_on_markers(runs, "."):
        leaves.extend(split_runs_on_markers(major, ")"))
    return leaves


def runs_to_text(runs):
    """Flatten runs back to plain text for the existing string-based
    stub/label/see-also regexes, which do not need to know which part
    was bold. Uses `_smart_join` so trailing punctuation from its own run
    (as in a stub target run immediately followed by a lone "." run) does
    not pick up a spurious leading space that would break those regexes'
    `[;,.]?` boundary matching."""
    return _smart_join(c for _, c in runs if c).strip()


_IDIOM = ("◇", "")  # sentinel run marking the position of the ◇ marker
# A "см./ср." italic run ends an example's translation right there, even
# mid-group (e.g. "<b>...</b> что же это ты делаешь?; <i>ср.</i> <b>авго</b>,
# ..."): everything from it onward is a cross-reference list, left in
# `leftover` for the text-based `extract_see_also` to convert, not folded
# into the preceding example's `ru`.
_SEE_ALSO_MARKER_RE = re.compile(r"^(см\.(?:\s+также)?|ср\.)$", re.I)


def _expand_idiom_marker(runs):
    """Replace any 't' run containing '◇' with [before, _IDIOM, after],
    so the marker becomes its own position in the sequence instead of
    being buried inside a run's text (where a later lookahead could
    accidentally swallow it into an example's translation)."""
    expanded = []
    for kind, content in runs:
        if kind == "t" and "◇" in content:
            before, _, after = content.partition("◇")
            if before.strip():
                expanded.append(("t", before.strip()))
            expanded.append(_IDIOM)
            if after.strip():
                expanded.append(("t", after.strip()))
        else:
            expanded.append((kind, content))
    return expanded


def _smart_join(parts):
    """Join run texts the way the printed page would read them: no space
    is forced next to an opening/closing bracket picked up from a plain
    run (e.g. "идёт (" + "или" + "ведёт) в Гуниб" -> "идёт (или ведёт) в
    Гуниб", not "идёт ( или ведёт ) в Гуниб")."""
    out = ""
    for p in parts:
        if not p:
            continue
        if out and not out.endswith(("(", "«", "'")) and not p.startswith((")", ",", ";", ".", "»", "'")):
            out += " "
        out += p
    return out


# A "(букв. ...)" aside -- established av-ru.jsonl convention: `comment`,
# never a label (CLAUDE.md "Решённые вопросы"). Typeset three different
# ways in this book (the parens and "букв." independently italic or
# plain, in any combination) and not always at the end of the sentence
# ("вчера мы получили (букв. к нам пришло) от сына письмо" continues
# *after* the aside) -- so this runs on the final joined `ru` string,
# where none of that typesetting variation matters any more, instead of
# trying to track it through the run-by-run extraction above.
_BUKV_PAREN_RE = re.compile(r"\(\s*букв\.?\s*([^()]*)\)", re.I)


def _extract_bukv_comment(ru):
    m = _BUKV_PAREN_RE.search(ru)
    if m:
        comment = ("букв. " + m[1].strip()).strip()
        remaining = re.sub(r"\s+", " ", ru[: m.start()] + " " + ru[m.end():]).strip(" ;,.")
        return remaining, comment
    # No parens: "...; букв. X" with a real translation before it splits
    # there (comment = "букв. X"); "букв. X" with nothing substantial
    # before it means the book gives only the literal gloss, with no
    # separate figurative translation to set it apart from -- nothing to
    # move into `comment` without leaving `ru` empty, so just drop the
    # now-redundant marker word and keep the gloss as `ru`.
    bare = re.search(r"\bбукв\.?\s+", ru, re.I)
    if not bare:
        return ru, None
    preceding = ru[: bare.start()].strip(" ;,.")
    rest = ru[bare.end():].strip()
    if preceding:
        return preceding, ("букв. " + rest).strip()
    return rest, None


def extract_bold_examples(runs):
    """Pull (av, ru) example pairs out of one leaf's runs using bold-vs-
    plain typesetting: a bold run is that example's Avar phrase, and
    every run after it up to the next bold run (or the ◇ idiom marker, or
    the end of the leaf) is its Russian translation -- plain prose, with
    any inline italic aside folded in (the book also uses italic for a
    parenthetical wording alternative *inside* a translation, e.g. "идёт
    (<i>или</i> ведёт)", not only for grammatical labels). The combined
    translation must contain real letters and be more than a bare
    connector word, or the bold run is left as a cross-reference target /
    cited word form for the existing text-based `try_stub`/
    `extract_see_also` logic instead.

    The idiom marker '◇' switches collection into a second ("idiom")
    bucket from that point on, since an idiom becomes its own sense with
    label "поговорка".

    Returns (leftover_runs, examples, idiom_leftover_runs, idiom_examples).
    """
    runs = _expand_idiom_marker(runs)
    leftover, idiom_leftover = [], []
    examples, idiom_examples = [], []
    after_idiom = False
    i, n = 0, len(runs)
    while i < n:
        if runs[i] is _IDIOM:
            after_idiom = True
            i += 1
            continue
        kind, content = runs[i]
        # A bold sense-number marker that `split_leaf_runs` did not strip
        # (e.g. its siblings were OCR'd as letters -- "а) бодать; б)
        # подать рог; <b>3)</b> рожок ...", where "3)" can never be a
        # valid *first* marker and so is correctly left unsplit) is never
        # a real Avar example phrase: no Avar word is just digits.
        if kind == "b" and re.fullmatch(r"\d+[.)]", content):
            (idiom_leftover if after_idiom else leftover).append((kind, content))
            i += 1
            continue
        prev = runs[i - 1] if i > 0 and runs[i - 1] is not _IDIOM else None
        is_stub_target = (
            kind == "b"
            and prev is not None
            and prev[0] == "i"
            and re.search(r"(?:от|глагола)$", prev[1], re.I)
        )
        if kind == "b" and not is_stub_target:
            j = i + 1
            while (
                j < n
                and runs[j] is not _IDIOM
                and runs[j][0] != "b"
                and not (runs[j][0] == "i" and _SEE_ALSO_MARKER_RE.fullmatch(runs[j][1]))
            ):
                j += 1
            group = list(runs[i + 1 : j])
            # A label right after the Avar phrase (e.g. "<b>...</b>
            # <i>погов.</i> ...") classifies this specific example, rather
            # than being part of its Russian translation.
            ex_labels = []
            while group and group[0][0] == "i":
                content0 = group[0][1]
                if content0 in ABBR_LABELS:
                    ex_labels.append(ABBR_LABELS[content0])
                    group = group[1:]
                    continue
                # A label and "букв." are sometimes typeset glued into one
                # italic run with no parens at all ("<i>погов. букв.</i>
                # любовь к парню — не вина"): extract the label and leave
                # the bare "букв." in place for `_extract_bukv_comment`.
                combo = re.match(r"^(" + "|".join(re.escape(k) for k in ABBR_LABELS) + r")\s*(букв\.?)$", content0, re.I)
                if combo:
                    ex_labels.append(ABBR_LABELS[combo[1]])
                    group = [("i", combo[2])] + group[1:]
                break
            # "букв." ("literally") introduces a literal-translation aside
            # that belongs in `comment`, with no label (established
            # av-ru.jsonl convention, CLAUDE.md "Решённые вопросы"), not
            # folded into the translation itself. Typeset several ways:
            # the whole "(букв." italic, or only the opening "(букв."
            # italic and the closing ")" its own, separate italic run, or
            # no parens at all when the book gives no other, figurative
            # translation to set the literal one apart from (see
            # `_extract_bukv_comment`).
            ru = _smart_join(c for _, c in group).strip(" ;,.")
            ru, ex_comment = _extract_bukv_comment(ru)
            if len(ru) > 2 and ru.lower() not in _CONNECTOR_WORDS and re.search(r"[а-яёА-ЯЁ]", ru):
                pair = {"av": content, "ru": ru}
                if ex_comment:
                    pair["comment"] = ex_comment
                if ex_labels:
                    pair["labels"] = ex_labels
                (idiom_examples if after_idiom else examples).append(pair)
                i = j
                continue
        (idiom_leftover if after_idiom else leftover).append((kind, content))
        i += 1
    return leftover, examples, idiom_leftover, idiom_examples


def split_markers(text, suffix):
    """Split on top-level 'N<suffix>' sense markers that count up from 1
    (the very first, implicit "1." is often not printed, so the sequence
    may start at 2); a number out of sequence is left embedded in the
    surrounding text rather than treated as a split point."""
    pattern = re.compile(r"(?<![\d.)])(\d+)" + re.escape(suffix) + r"\s+")
    matches = list(pattern.finditer(text))
    accepted, expected = [], None
    for m in matches:
        num = int(m[1])
        if expected is None:
            if num in (1, 2):
                accepted.append(m)
                expected = num + 1
        elif num == expected:
            accepted.append(m)
            expected += 1
    if not accepted:
        return [text.strip()] if text.strip() else []
    chunks = []
    head = text[: accepted[0].start()].strip()
    if head:
        chunks.append(head)
    for i, m in enumerate(accepted):
        end = accepted[i + 1].start() if i + 1 < len(accepted) else len(text)
        chunk = text[m.end():end].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def split_senses(text):
    leaves = []
    for major in split_markers(text, "."):
        leaves.extend(split_markers(major, ")"))
    return leaves


SEE_ALSO_RE = re.compile(r";?\s*(см\.(?:\s+также)?|ср\.)\s+([^.]+?)\.?\s*$", re.I)


def extract_see_also(text):
    m = SEE_ALSO_RE.search(text)
    if not m:
        return text, []
    kind = "see" if m[1].lower().startswith("см") else "compare"
    raw_targets = [t.strip().strip("()") for t in re.split(r",\s*| и ", m[2].rstrip(" ;.")) if t.strip()]
    # "см. гӀадил 2, 3" refers to two homonyms of the same base word -- a
    # bare number after the first target reattaches to that target's base.
    targets, base = [], None
    for t in raw_targets:
        if re.fullmatch(r"\d+", t) and base:
            t = f"{base} {t}"
        else:
            bm = re.match(r"^(\S+)\s+\d+$", t)
            base = bm[1] if bm else t
        targets.append(t)
    remaining = text[: m.start()].strip().rstrip(";").strip()
    return remaining, [{"target": strip_stress(t), "kind": kind} for t in targets]


ABBR_LABELS = {
    "масд.": "масдар",
    "понуд.": "понудительная форма",
    "учащ.": "учащательная форма",
    "перен.": "в переносном значении",
    "разг.": "разговорное слово",
    "уст.": "устаревшее слово",
    "прост.": "просторечное слово",
    "книжн.": "книжное",
    "бот.": "ботаника",
    "зоол.": "зоология",
    "мед.": "медицина",
    "межд.": "междометие",
    "посл.": "пословица",
    "погов.": "поговорка",
    "бран.": "бранное слово",
    "ласк.": "ласкательное слово",
    "пренебр.": "пренебрежительно",
    "ирон.": "ироническое",
    "шутл.": "шутливое",
    "диал.": "диалектизм",
    "обл.": "диалектизм",
    "спец.": "специальное",
    "религ.": "религия",
    "рел.": "религия",
    "грам.": "грамматика",
    "нареч.": "наречие",
    "мест.": "местоимение",
    "числ.": "имя числительное",
    # These also appear as a stand-alone inline label ("this headword is
    # itself a plural/genitive/etc. form"), distinct from the "<label> от X"
    # stub below (a *different* headword's derived-form cross-reference).
    "мн.": "множественное число",
    "ед.": "единственное число",
    "род. п.": "родительный падеж",
    "эрг. п.": "эргативный падеж",
    "местн. п.": "местный падеж",
}
# An idiom (◇) defaults to "поговорка", but not when the text already
# names a more specific type of its own.
_IDIOM_TYPE_LABELS = {"поговорка", "пословица"}
LEADING_LABEL_RE = re.compile(
    # A label at the very end of a leaf (e.g. a "масд. понуд." note that
    # applies to all of the headword's numbered sub-senses, printed before
    # the first "1)" with nothing else following it) has no trailing
    # whitespace to require.
    r"^(" + "|".join(re.escape(k) for k in sorted(ABBR_LABELS, key=len, reverse=True)) + r")(?:\s+|$)"
)

# A cross-reference target, with an optional trailing roman-numeral homonym
# marker (бер I); several targets can be chained with ", "/" и " (бер I, II,
# III; аб и ай II).
TARGET = TOKEN + r"(?:\s+I{1,3})?"
# A ", "-joined continuation only ever repeats the roman-numeral homonym
# marker of the *same* base word (бер I, II, III); comma is never used to
# join two distinct-word targets (that's always " и "), so a comma
# followed by anything else (e.g. ", рожь" in "от огоб, рожь" -- a
# trailing gloss, not a second target) must not be swallowed here.
MULTI_TARGET = r"(" + TARGET + r"(?:,\s*I{1,3}|\s+и\s+" + TARGET + r")*)"
# The pronoun oblique-case series (ergative/local) commonly lists several
# gender-marked bases of the *same* pronoun with plain commas (жиб, жив,
# жий) rather than "и" -- unlike a genitive/plural stub's single target
# plus comma-introduced gloss ("от огоб, рожь"), so those two patterns use
# the stricter MULTI_TARGET above instead of this one.
MULTI_TARGET_LOOSE = r"(" + TARGET + r"(?:,\s*" + TARGET + r"|\s+и\s+" + TARGET + r")*)"
# Avar local cases come in several numbered series ("местн. п. 1 от X");
# matched and discarded into the label text, not a separate schema field.
LOCAL_SERIES_RE = re.compile(r"^(местн\.\s*п\.)\s+(\d+)\s+от\s+")


def _targets(raw):
    pieces = [t.strip() for t in re.split(r",\s*|\s+и\s+", raw) if t.strip()]
    targets, base = [], None
    for t in pieces:
        if re.fullmatch(r"I{1,3}|\d+", t) and base:
            t = f"{base} {t}"
        else:
            base = re.sub(r"\s+I{1,3}$", "", t)
        targets.append(strip_stress(t))
    return targets


def _case_stub(match, field_name, label_text):
    """'<label> от X[, gloss]' for a grammatical case form. A single
    source uses the dedicated field (`genitivefrom`/`ergativefrom`, same
    as data/av-ru.jsonl); several sources, or a case with no dedicated
    field (e.g. "местный падеж"), fall back to a labeled comment."""
    targets, rest = _targets(match[1]), match[2].strip()
    if len(targets) == 1 and field_name:
        sense = {field_name: targets[0], "comment": label_text}
    else:
        sense = {"labels": [label_text], "comment": "от " + ", ".join(f"'{t}'" for t in targets)}
    if rest:
        sense["text"] = rest
    return sense, [{"target": t, "kind": "from"} for t in targets]


# Whole-sense "<grammatical note> от X[, gloss]" stubs -- a separate article
# whose only content is "this is a derived form of X" -- matching the field
# names already used for the same relation in data/av-ru.jsonl (av-ru.2006).
STUB_PATTERNS = [
    ("masdarfrom", re.compile(r"^масд\.\s+глагола\s+(" + TOKEN + r")\.?$")),
    ("masdarfrom", re.compile(r"^масд\.\s+от\s+(" + TOKEN + r")\.?$")),
]
PARTICIPLE_RE = re.compile(r"^прич\.(?:\s+прош\.\s+вр\.)?\s+от\s+" + MULTI_TARGET + r"[;,.]?\s*(.*)$")
GENITIVE_RE = re.compile(r"^род\.\s*п\.\s+от\s+" + MULTI_TARGET + r"[;,.]?\s*(.*)$")
ERGATIVE_RE = re.compile(r"^эрг\.\s*п\.\s+от\s+" + MULTI_TARGET_LOOSE + r"[;,.]?\s*(.*)$")
LOCAL_RE = re.compile(r"^местн\.\s*п\.\s+от\s+" + MULTI_TARGET_LOOSE + r"[;,.]?\s*(.*)$")
PLURAL_RE = re.compile(r"^мн\.\s+от\s+" + MULTI_TARGET + r"[;,.]?\s*(.*)$")
CAUSATIVE_RE = re.compile(r"^понуд\.\s+от\s+" + MULTI_TARGET + r"[;,.]?\s*(.*)$")
ITERATIVE_RE = re.compile(r"^учащ\.\s+от\s+" + MULTI_TARGET + r"[;,.]?\s*(.*)$")
IMPERATIVE_RE = re.compile(r"^повел\.\s+от\s+" + MULTI_TARGET + r"[;,.]?\s*(.*)$")
PAST_TENSE_RE = re.compile(r"^прош\.\s+вр\.\s+от\s+" + MULTI_TARGET + r"[;,.]?\s*(.*)$")


def try_stub(leaf):
    """Recognize a whole sense that is nothing but '<label> от X[, gloss]',
    returning (sense_dict, see_also_list) or None if the leaf is not one."""
    local_series = None
    series_match = LOCAL_SERIES_RE.match(leaf)
    if series_match:
        local_series = series_match[2]
        leaf = series_match[1] + " от " + leaf[series_match.end():]
    for field, pattern in STUB_PATTERNS:
        m = pattern.match(leaf)
        if m:
            target = strip_stress(m[1].rstrip("."))
            sense = {"labels": ["масдар"], field: target} if field == "masdarfrom" else {field: target}
            return sense, [{"target": target, "kind": "from"}]
    m = PARTICIPLE_RE.match(leaf)
    if m:
        targets, rest = _targets(m[1]), m[2].strip()
        # single source is the common case (2006 schema: one `participlefrom`
        # string); multiple sources fall back to a plain comment.
        if len(targets) == 1:
            sense = {"participlefrom": targets[0]}
        else:
            sense = {"comment": "причастие от " + ", ".join(f"'{t}'" for t in targets)}
        if rest:
            sense["text"] = rest
        return sense, [{"target": t, "kind": "from"} for t in targets]
    m = GENITIVE_RE.match(leaf)
    if m:
        return _case_stub(m, "genitivefrom", "родительный падеж")
    m = ERGATIVE_RE.match(leaf)
    if m:
        return _case_stub(m, "ergativefrom", "эргативный падеж")
    m = LOCAL_RE.match(leaf)
    if m:
        label = f"местный падеж {local_series}" if local_series else "местный падеж"
        return _case_stub(m, None, label)
    m = PLURAL_RE.match(leaf)
    if m:
        targets, rest = _targets(m[1]), m[2].strip()
        if len(targets) == 1:
            sense = {"labels": ["множественное число"], "pluralfor": targets[0]}
        else:
            sense = {"labels": ["множественное число"], "comment": "от " + ", ".join(f"'{t}'" for t in targets)}
        if rest:
            sense["text"] = rest
        return sense, [{"target": t, "kind": "from"} for t in targets]
    m = CAUSATIVE_RE.match(leaf)
    if m:
        targets, rest = _targets(m[1]), m[2].strip()
        sense = {"comment": "от " + ", ".join(f"'{t}'" for t in targets), "labels": ["понудительная форма"]}
        if rest:
            sense["text"] = rest
        return sense, [{"target": t, "kind": "from"} for t in targets]
    m = ITERATIVE_RE.match(leaf)
    if m:
        targets, rest = _targets(m[1]), m[2].strip()
        sense = {"comment": "от " + ", ".join(f"'{t}'" for t in targets), "labels": ["учащательная форма"]}
        if rest:
            sense["text"] = rest
        return sense, [{"target": t, "kind": "from"} for t in targets]
    m = IMPERATIVE_RE.match(leaf)
    if m:
        targets, rest = _targets(m[1]), m[2].strip()
        sense = {"labels": ["повелительное"], "comment": "от " + ", ".join(f"'{t}'" for t in targets)}
        if rest:
            sense["text"] = rest
        return sense, [{"target": t, "kind": "from"} for t in targets]
    m = PAST_TENSE_RE.match(leaf)
    if m:
        targets, rest = _targets(m[1]), m[2].strip()
        sense = {"labels": ["прошедшее время"], "comment": "от " + ", ".join(f"'{t}'" for t in targets)}
        if rest:
            sense["text"] = rest
        return sense, [{"target": t, "kind": "from"} for t in targets]
    return None


# --- High-confidence example extraction via av-ru.jsonl (av-ru.2006) ---
#
# Splitting an Avar example phrase from its Russian translation inside a
# sense's `text` is not attempted in general (see module docstring): both
# languages are Cyrillic here, with no structural marker reliable enough
# on its own (a stress-accent heuristic was tried and rejected -- too many
# false positives from short unaccented Russian words). But data/av-ru.jsonl
# (av-ru.2006) already has clean `examples[].av` for ~6500 of the same
# headwords; when a 1967 sense's text begins a clause with that exact
# phrase (accents aside -- 1967 never accents Avar text, so no alignment
# issue), the match is used only as a boundary anchor, not as a source of
# content: the Russian translation is still 1967's own wording, not
# av-ru.jsonl's, since they are different books.

_ANCHOR_INDEX: dict | None = None


def _load_anchor_index() -> dict:
    global _ANCHOR_INDEX
    if _ANCHOR_INDEX is None:
        index: dict[str, set] = {}
        path = ROOT / "data" / "av-ru.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            for sense in entry.get("senses", []):
                for ex in sense.get("examples", []) or []:
                    av = ex.get("av")
                    if av:
                        index.setdefault(entry["word"], set()).add(strip_stress(av))
        _ANCHOR_INDEX = index
    return _ANCHOR_INDEX


def extract_known_examples(word, text):
    """Split `text` into (leftover_text, examples[]) using av-ru.jsonl
    anchors for `word` as high-confidence boundaries. A clause (';'-
    separated, as elsewhere in this module) is only split when it starts
    with one of those anchors exactly, followed by a space or the clause's
    own end."""
    anchors = _load_anchor_index().get(word)
    if not anchors or not text:
        return text, []
    clauses = re.split(r";\s*", text)
    kept, examples = [], []
    for clause in clauses:
        bare = clause.rstrip(". ").strip()
        matched = None
        for anchor in sorted(anchors, key=len, reverse=True):
            if bare == anchor or bare.startswith(anchor + " "):
                matched = anchor
                break
        if matched:
            rest = bare[len(matched):].strip()
            if rest:
                examples.append({"av": matched, "ru": rest})
            else:
                kept.append(clause)
        else:
            kept.append(clause)
    leftover = "; ".join(kept)
    return (leftover if leftover else None), examples


def _build_one_sense(leaf_text, examples):
    """Shared tail of sense assembly, after bold-based example extraction
    has already removed any (av, ru) pairs from `leaf_text`'s runs."""
    leaf_text, leaf_see_also = extract_see_also(leaf_text)
    # A plain inline label (e.g. "диал.") can precede a "<label> от X"
    # stub ("диал. понуд. от башлайизе; ..."); strip one leading label at
    # a time and re-check for a stub after each, so the stub is still
    # recognized once it is no longer hidden behind it.
    pre_labels = []
    stub = try_stub(leaf_text) if leaf_text else None
    while leaf_text and not stub:
        m = LEADING_LABEL_RE.match(leaf_text)
        if not m:
            break
        pre_labels.append(ABBR_LABELS[m[1]])
        leaf_text = leaf_text[m.end():].strip()
        stub = try_stub(leaf_text) if leaf_text else None
    see_also = list(leaf_see_also)
    if stub:
        sense, stub_see_also = stub
        combined_labels = pre_labels + sense.get("labels", [])
        if combined_labels:
            sense["labels"] = combined_labels
        see_also.extend(stub_see_also)
    elif leaf_text or pre_labels or examples:
        sense = {}
        if pre_labels:
            sense["labels"] = pre_labels
        if leaf_text:
            sense["text"] = leaf_text
    else:
        sense = None
    if sense is not None and examples:
        sense["examples"] = examples
    return sense, see_also


def build_senses(leaf_run_groups):
    """Turn the leaf-split run groups (see `split_leaf_runs`) into
    `senses`/`see_also`, using the book's own bold/italic typesetting to
    separate Avar examples from their Russian translation (see
    `extract_bold_examples`) before falling back to the text-based
    stub/label/see-also logic for whatever is left."""
    see_also = []
    senses = []
    for runs in leaf_run_groups:
        leftover, examples, idiom_leftover, idiom_examples = extract_bold_examples(runs)
        sense, sense_see_also = _build_one_sense(runs_to_text(leftover), examples)
        see_also.extend(sense_see_also)
        if sense is not None:
            senses.append(sense)
        if idiom_leftover or idiom_examples:
            idiom_sense, idiom_see_also = _build_one_sense(runs_to_text(idiom_leftover), idiom_examples)
            see_also.extend(idiom_see_also)
            if idiom_sense is not None:
                # Default to "поговорка" only when the text itself did not
                # already supply a more specific classification (e.g.
                # "посл." -> "пословица" on one of its examples) -- an
                # idiom is not simultaneously both.
                own_and_example_labels = set(idiom_sense.get("labels", [])) | {
                    l for ex in idiom_sense.get("examples", []) or [] for l in ex.get("labels", []) or []
                }
                if not (own_and_example_labels & _IDIOM_TYPE_LABELS):
                    idiom_sense["labels"] = ["поговорка"] + idiom_sense.get("labels", [])
                senses.append(idiom_sense)
    return senses, see_also


def build_entry(article):
    entry = {"word": article["word"], "source": SOURCE}
    if "stress" in article:
        entry["stress"] = article["stress"]
    if article.get("spelling_forms"):
        entry["spelling_forms"] = article["spelling_forms"]
    if article.get("homonym"):
        entry["homonym"] = article["homonym"]

    body_html = article.get("body_html", "").lstrip()

    # The roman-numeral homonym marker is usually part of the bold heading
    # (caught in articles()), but sometimes sits just outside it -- as
    # plain text ("<b>бай</b> II ...") or in its own bold span ("<b>ба́зе</b>
    # [...] <b>I</b> <b>1)</b> ..."), and either before or after a headword
    # bracket, so this is checked again after the bracket is stripped too.
    loose_homonym_re = re.compile(r"^(?:<b>)?(I{1,3})(?:</b>)?\s+(.*)$", re.S)

    def strip_loose_homonym(html):
        m = loose_homonym_re.match(html)
        if not m:
            return html
        entry["homonym"] = len(m[1])
        return m[2]

    body_html = strip_loose_homonym(body_html)

    if body_html.startswith("["):
        close = body_html.find("]")
        if close != -1:
            bracket = parse_headword_bracket(plain(body_html[1:close]))
            if bracket["kind"] == "forms" and bracket["forms"]:
                entry["forms"] = [strip_stress(article["word"])] + bracket["forms"]
                body_html = body_html[close + 1:].lstrip()
            elif bracket["kind"] == "relation":
                label, target = bracket["label"], bracket["target"]
                rel_sense = {"participlefrom": target} if label.startswith("прич") else {"comment": f"от '{target}'; {label}"}
                entry.setdefault("_bracket_relation", (rel_sense, target))
                body_html = body_html[close + 1:].lstrip()
            # kind == "unknown": leave body_html (bracket included) untouched
            body_html = strip_loose_homonym(body_html)

    senses, see_also = build_senses(split_leaf_runs(tag_runs(body_html)))

    bracket_relation = entry.pop("_bracket_relation", None)
    if bracket_relation:
        rel_sense, target = bracket_relation
        senses.insert(0, rel_sense)
        see_also.append({"target": target, "kind": "from"})

    if article.get("class_marker"):
        gender_forms = derive_gender_forms(article["word"])
        if gender_forms:
            entry["gender_forms"] = gender_forms
        else:
            entry["class_marker"] = True

    for sense in senses:
        if sense.get("text"):
            leftover, examples = extract_known_examples(entry["word"], sense["text"])
            if examples:
                if leftover:
                    sense["text"] = leftover
                else:
                    del sense["text"]
                sense["examples"] = examples

    if senses:
        entry["senses"] = senses
    if see_also:
        entry["see_also"] = see_also
    return entry


if __name__ == "__main__":
    html = (ROOT / "books" / SOURCE / f"{SOURCE}.html").read_text(encoding="utf-8")
    entries = [build_entry(a) for a in articles(html)]
    output = ROOT / "data" / f"{SOURCE}.jsonl"
    output.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n",
        encoding="utf-8",
    )
    print(f"{output}: {len(entries)} entries")
