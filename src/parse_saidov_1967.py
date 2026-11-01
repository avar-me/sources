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
            entry = {"word": word, "text": text, "heading_prefix": heading_prefix, "page": page}
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


def extract_idiom(text):
    if "◇" not in text:
        return text, None
    main, idiom = text.split("◇", 1)
    return main.strip().rstrip(";").strip(), idiom.strip()


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
        sense = {"comment": "от " + ", ".join(f"'{t}'" for t in targets) + "; повел."}
        if rest:
            sense["text"] = rest
        return sense, [{"target": t, "kind": "from"} for t in targets]
    m = PAST_TENSE_RE.match(leaf)
    if m:
        targets, rest = _targets(m[1]), m[2].strip()
        sense = {"comment": "от " + ", ".join(f"'{t}'" for t in targets) + "; прош. вр."}
        if rest:
            sense["text"] = rest
        return sense, [{"target": t, "kind": "from"} for t in targets]
    return None


def build_senses(remainder):
    """Turn the raw post-headword text into `senses`/`see_also`."""
    see_also = []
    senses = []
    for leaf in split_senses(remainder):
        leaf, leaf_see_also = extract_see_also(leaf)
        see_also.extend(leaf_see_also)
        leaf, idiom = extract_idiom(leaf)
        # A plain inline label (e.g. "диал.") can precede a "<label> от X"
        # stub ("диал. понуд. от башлайизе; ..."); strip one leading label
        # at a time and re-check for a stub after each, so the stub is
        # still recognized once it is no longer hidden behind it.
        pre_labels = []
        stub = try_stub(leaf) if leaf else None
        while leaf and not stub:
            m = LEADING_LABEL_RE.match(leaf)
            if not m:
                break
            pre_labels.append(ABBR_LABELS[m[1]])
            leaf = leaf[m.end():].strip()
            stub = try_stub(leaf) if leaf else None
        if stub:
            sense, stub_see_also = stub
            combined_labels = pre_labels + sense.get("labels", [])
            if combined_labels:
                sense["labels"] = combined_labels
            senses.append(sense)
            see_also.extend(stub_see_also)
        elif leaf or pre_labels:
            sense = {}
            if pre_labels:
                sense["labels"] = pre_labels
            if leaf:
                sense["text"] = leaf
            senses.append(sense)
        if idiom:
            senses.append({"text": idiom, "labels": ["поговорка"]})
    return senses, see_also


def build_entry(article):
    entry = {"word": article["word"], "source": SOURCE}
    if "stress" in article:
        entry["stress"] = article["stress"]
    if article.get("spelling_forms"):
        entry["spelling_forms"] = article["spelling_forms"]
    if article.get("homonym"):
        entry["homonym"] = article["homonym"]

    text = article["text"]
    prefix = article.get("heading_prefix", "")
    remainder = text[len(prefix):].lstrip() if text.startswith(prefix) else text

    # The roman-numeral homonym marker is usually part of the bold heading
    # (caught in articles()), but sometimes sits just outside it ("<b>бай</b>
    # II ...").
    loose_homonym = re.match(r"^(I{1,3})\s+(.*)$", remainder)
    if loose_homonym:
        entry["homonym"] = len(loose_homonym[1])
        remainder = loose_homonym[2]

    if remainder.startswith("["):
        close = remainder.find("]")
        if close != -1:
            bracket = parse_headword_bracket(remainder[1:close])
            if bracket["kind"] == "forms" and bracket["forms"]:
                entry["forms"] = [strip_stress(article["word"])] + bracket["forms"]
                remainder = remainder[close + 1:].lstrip()
            elif bracket["kind"] == "relation":
                label, target = bracket["label"], bracket["target"]
                rel_sense = {"participlefrom": target} if label.startswith("прич") else {"comment": f"от '{target}'; {label}"}
                entry.setdefault("_bracket_relation", (rel_sense, target))
                remainder = remainder[close + 1:].lstrip()
            # kind == "unknown": leave remainder (bracket included) untouched

    senses, see_also = build_senses(remainder)

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
