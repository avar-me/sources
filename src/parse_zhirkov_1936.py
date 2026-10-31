#!/usr/bin/env python3
"""Import Zhirkov 1936 OCR HTML into the existing dictionary schema.

Historical letters and OCR readings are preserved in canonical Unicode.
Headword accents become stress metadata. No transliteration.
See books/av-ru.1936/README.md for extraction rules and limitations.
"""

import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
try:
    from .normalize_zhirkov_1936 import CODE_ALIASES, normalize_unicode
except ImportError:
    from normalize_zhirkov_1936 import CODE_ALIASES, normalize_unicode

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "av-ru.1936"
LATIN_FIELDS = {"word", "forms", "spelling_forms", "gender_forms", "av", "target", "stem"}


def canonical_latin_fields(value):
    """Canonicalize historical Latin only; Russian prose keeps its typography."""
    if isinstance(value, dict):
        return {key: canonical_latin_fields(item) if key not in LATIN_FIELDS
                else normalize_latin_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical_latin_fields(item) for item in value]
    return value


def normalize_latin_value(value):
    if isinstance(value, str):
        return normalize_unicode(value)
    if isinstance(value, list):
        return unique(normalize_latin_value(item) for item in value)
    if isinstance(value, dict):
        return {key: normalize_latin_value(item) for key, item in value.items()}
    return value


def headword_stress(word):
    """Return NFC spelling and a one-based code-point position in that spelling."""
    if not any(c in unicodedata.normalize("NFD", word) for c in "\u0301\u0300"):
        return unicodedata.normalize("NFC", word), None
    clusters = re.findall(r"[^\u0300-\u036f][\u0300-\u036f]*", unicodedata.normalize("NFD", word))
    output, positions = "", []
    for cluster in clusters:
        accented = any(c in cluster for c in "\u0301\u0300")
        clean = unicodedata.normalize("NFC", unaccent(cluster))
        if accented:
            if cluster[0].lower() not in "aeiou":
                raise ValueError(f"Stress on a non-vowel in headword: {word}")
            positions.append(len(output) + 1)
        output += clean
    if len(positions) > 1:
        raise ValueError(f"Multiple stresses in headword need review: {word}")
    return output, positions[0] if positions else None


def extract_form_stresses(value):
    """Preserve form order and stress distinctions even after spellings coincide."""
    if isinstance(value, list):
        return [extract_form_stresses(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key != "forms":
            result[key] = extract_form_stresses(item)
            continue
        converted = [headword_stress(form) for form in item]
        result[key] = [form for form, _ in converted]
        stresses = {str(i): stress for i, (_, stress) in enumerate(converted) if stress is not None}
        if stresses:
            result["form_stresses"] = stresses
    return result


ORIGINS = {
    "a": "арабское происхождение", "p": "персидское происхождение",
    "r": "русское происхождение", "t": "тюркское происхождение",
    "i": "интернациональный термин",
}
# Visually identical OCR glyphs in an isolated origin abbreviation only.
ORIGIN_GLYPHS = {"а": "a", "р": "p", "т": "t"}
GRAMMAR = {
    "act": "эргативный падеж", "pos": "родительный падеж", "poss": "родительный падеж",
    "dat": "дательный падеж", "l": "местный падеж",
    "al": "направительный падеж", "all": "направительный падеж",
    "el": "исходный падеж", "pl": "множественное число",
    "m": "мужской род", "f": "женский род",
    "perf": "прошедшее время", "pr": "настоящее время", "fut": "будущее время",
    "part": "причастие", "imp": "повелительная форма",
    "neg": "отрицательная форма", "frequ": "учащательная форма",
    "adv": "деепричастие", "ger": "деепричастие",
}
GRAMMAR_CODES = r"act|poss|pos|dat|all|al[1-5]?|el[1-5]?|l[1-5]?|pl|m|f|perf|pr|fut|part|imp|neg|frequ|adv|ger|" + "|".join(map(re.escape, CODE_ALIASES))
GRAMMAR_RE = re.compile(r"^(" + GRAMMAR_CODES + r")\.?($|[\s,]+)")
REFERENCE_RE = re.compile(r"(?<!\w)(см\.|ср\.|cp\.)\s*|=+")


def reference_kind(marker):
    return "spelling" if marker.startswith("=") else "compare" if marker in ("ср.", "cp.") else "see"


RUSSIAN_LABELS = {
    "редко": "редко", "устаревшее слово": "устаревшее слово",
    "о животном": "о животном", "детское слово": "детская лексика",
}


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
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


def unique(items):
    return list(dict.fromkeys(items))


def unaccent(text):
    return text.replace("\u0301", "").replace("\u0300", "")


def clean_space(text):
    return re.sub(r"\s+([.,;:!?])", r"\1", re.sub(r"\s+", " ", text)).strip()


def russian(token):
    letters = [c for c in token if c.isalpha()]
    return bool(letters) and sum("CYRILLIC" in unicodedata.name(c, "") for c in letters) / len(letters) > .5


def split_top(text, delimiter=";"):
    """Split outside parentheses and square brackets, retaining internal punctuation."""
    parts, start, depth = [], 0, 0
    for i, char in enumerate(text):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        elif char == delimiter and depth == 0:
            parts.append(text[start:i].strip())
            start = i + 1
    parts.append(text[start:].strip())
    return parts


def groups(text):
    """Balanced outer parenthetical spans, so targets like ab(in) remain intact."""
    depth, start = 0, 0
    for i, char in enumerate(text):
        if char == "(":
            if depth == 0:
                start = i
            depth += 1
        elif char == ")" and depth:
            depth -= 1
            if depth == 0:
                yield start, i + 1, text[start + 1:i]


def grammar_prefix(text):
    labels = []
    while match := GRAMMAR_RE.match(text.strip()):
        text = text.strip()
        code = CODE_ALIASES.get(match[1], match[1])
        base = re.sub(r"[1-5]$", "", code)
        labels.append(GRAMMAR[base])
        if code[-1:].isdigit():
            labels.append(f"{code[-1]}-я серия")
        text = text[match.end():]
    return text.strip(), unique(labels)


def annotation(text):
    rest, labels = grammar_prefix(text)
    if labels and not rest:
        return labels
    label = RUSSIAN_LABELS.get(unaccent(text).strip())
    return [label] if label else []


def articles(html):
    """Keep initial import's article boundaries, including column continuations."""
    result, page = [], 0
    for match in re.finditer(r"<!-- p(\d+).*?-->|<p>(.*?)</p>", html, re.S):
        if match[1]:
            page = int(match[1])
            continue
        if not (page == 7 or 10 <= page <= 142):
            continue
        fragment = match[2]
        text = plain(fragment)
        bold = re.match(r"\s*<b>(.*?)</b>", fragment, re.S)
        # A heading and paradigm may precede the Russian gloss across a
        # column/page break; its recognition must not rely on Cyrillic OCR.
        # A headword followed only by an italic origin code can have its gloss
        # on the next page (maħrum). Alphabet headings/footers are not entries.
        origin_only = bold and re.fullmatch(r"\s*<i>[aiprtарт]</i>\s*", fragment[bold.end():])
        if not re.search(r"[А-Яа-яЁё]|=", text) and not (bold and ("[" in text or origin_only)):
            continue
        if bold:
            # OCR can place the final letter's combining mark just outside
            # the bold span. It is still part of the headword grapheme.
            tail_marks = re.match(r"[\u0300-\u036f]*", fragment[bold.end():])[0]
            heading = plain(bold[1]) + tail_marks
            word = heading.split(",", 1)[0].rstrip("*").strip()
            result.append({"word": word, "text": text, "heading": heading, "page": page})
        else:
            if not result:
                raise ValueError(f"Orphan continuation on scan {page}: {text}")
            previous = result[-1]["text"]
            if previous.endswith('-') and (previous.count('[') > previous.count(']')
                    or (re.search(r'[А-Яа-яЁё]\u0301?-$', previous) and re.match(r'[а-яё]', text))):
                result[-1]["text"] = previous[:-1] + text
            else:
                result[-1]["text"] += " " + text
    return result


def qualified_forms(item, current, forms, morphology):
    """Retain meaning/dialect qualifiers beside their actual bracketed forms."""
    if not any(russian(t) for t in item.split()):
        return False
    pending, comments, extra, result = [], [], [], []
    def flush():
        if not pending:
            return
        value = " ".join(pending)
        record = {"labels": unique(current + extra), "forms": [value]}
        if comments:
            record["comment"] = " ".join(comments)
        result.append(record)
        pending.clear()
        comments.clear()
        extra.clear()
    for token in split_top(item, " "):
        if not token:
            continue
        if token.startswith("(") and token.endswith(")"):
            inner = token[1:-1]
            found = annotation(inner)
            if found:
                extra.extend(found)
            else:
                comments.append(inner)
        elif russian(token):
            comments.append(token)
        else:
            if pending and (comments or extra):
                flush()
            pending.append(token)
    flush()
    if not result:
        return False
    for record in result:
        forms.extend(record["forms"])
        morphology.append(record)
    return True


def extract_forms(block, forms, morphology, notes, refs):
    """Only explicit grammatical labels are inherited; unmarked is not always pl."""
    current = []
    # Some comma separators are absent in OCR, but an explicit code still
    # unambiguously starts a labelled group after an actual form.
    items = []
    for item in [item for part in split_top(block) for item in split_top(part, ",")]:
        chunks = re.split(r"\s+(?=(?:" + GRAMMAR_CODES + r")\.?\s)", item)
        combined = ""
        for chunk in chunks:
            remainder, _ = grammar_prefix(combined)
            if combined and remainder:
                items.append(combined)
                combined = chunk
            else:
                combined = (combined + " " + chunk).strip()
        items.append(combined)
    for item in items:
        original = item
        item, labels = grammar_prefix(item)
        if labels:
            current = labels
        form_refs, _ = referral(item)
        if form_refs:
            refs.extend(form_refs)
            continue
        if qualified_forms(item, current, forms, morphology):
            continue
        ending = re.fullmatch(r"(\S+)\s+\((-[^()]+)\)", item)
        if ending:
            forms.append(ending[1])
            morphology.append({"labels": current[:], "forms": [ending[1]],
                               "comment": "Вариант окончания в источнике: " + ending[2]})
            continue
        # A parenthetical qualifier must not become part of a search form.
        qualifiers = []
        for start, end, inner in reversed(list(groups(item))):
            if (start == 0 or item[start - 1].isspace()) and annotation(inner):
                qualifiers[0:0] = annotation(inner)
                item = item[:start] + item[end:]
        item = item.strip().rstrip("*")
        if not item:
            notes.append("Формы в источнике: [" + block + "]")
            continue
        # Unknown OCR fragments remain readable, rather than becoming fake forms.
        tokens = item.split()
        if any(russian(t) or t.isdigit() or t in GRAMMAR or t in ("I", "II", "ll", "11", "15", "I1", "I5", "pcs", "poc", "adu", "cp.") for t in tokens):
            notes.append("Неразобранная форма: " + original)
            continue
        forms.append(item)
        if current or qualifiers:
            morphology.append({"labels": unique(current + qualifiers), "forms": [item]})


def targets(text):
    text = text.strip().rstrip(",;").strip()
    if text.endswith(".") and not text.endswith("..."):
        text = text[:-1].rstrip()
    values = split_top(text, ",")
    cleaned = [v.strip().rstrip("*").strip() for v in values]
    if not cleaned or any(not v or any(russian(t) for t in v.split()) for v in cleaned):
        return None
    return cleaned


def extract_references(text, refs):
    for start, end, inner in reversed(list(groups(text))):
        match = REFERENCE_RE.match(inner)
        if match:
            values, _ = referral(inner)
            if values:
                refs[0:0] = values
                before = inner[:match.start()].strip().rstrip(";").strip()
                replacement = "(" + before + ")" if before else ""
                text = text[:start] + replacement + text[end:]
    return clean_space(text)


def strip_annotations(text):
    labels, comments = [], []
    for start, end, inner in reversed(list(groups(text))):
        found = annotation(inner)
        if found and (start == 0 or text[start - 1].isspace()):
            labels[0:0] = found
            text = text[:start] + text[end:]
    return clean_space(text), unique(labels), comments


def prose_comments(text):
    """Move standalone Russian parenthetical explanations, not optional letters."""
    comments = []
    for start, end, inner in reversed(list(groups(text))):
        # Subject/number alternatives are grammar of the translation itself,
        # e.g. "да будет он (будут они) здоров(ы)", not an explanation.
        before_plain = unaccent(unicodedata.normalize("NFD", text[:start]))
        inner_plain = unaccent(unicodedata.normalize("NFD", inner))
        if re.search(r"\b(?:он|она|оно)\s*$", before_plain) and re.fullmatch(r"(?:будут\s+)?они", inner_plain):
            continue
        if ((start == 0 or text[start - 1].isspace())
                and (end == len(text) or not text[end].isalpha())
                and any(russian(t) for t in inner.split())):
            comments[0:0] = [inner]
            text = text[:start] + text[end:]
    return clean_space(text), comments


def referral(text):
    """A whole segment can be a referral followed by an explicit grammar mark."""
    labels = []
    suffix = re.search(r"\s+(frequ|imp|part perf|part|perf|adv)\.?\s*\.?$", text)
    if suffix:
        _, labels = grammar_prefix(suffix[1])
        text = text[:suffix.start()].strip()
    matches = list(REFERENCE_RE.finditer(text))
    if not matches or matches[0].start() != 0:
        return [], []
    refs = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        values = targets(text[match.end():end])
        if not values:
            return [], []
        refs.extend({"target": value, "kind": reference_kind(match[0].strip())} for value in values)
    return refs, labels


def split_example(text):
    """Detect a Latin phrase followed by a Russian gloss, tolerating mixed OCR."""
    if not text or text[0] in "([]" or russian(text.split()[0]):
        return None
    depth = 0
    for token in re.finditer(r"\S+", text):
        value = token[0]
        if depth == 0 and russian(value):
            av, ru = text[:token.start()].strip(), text[token.start():].strip()
            if av and any(c.isalpha() for c in av):
                return av, ru
            # A numeric Russian definition is not a Latin example; do not
            # continue past its first Russian word into a parenthetical gloss.
            return None
        depth += value.count("(") - value.count(")")
        depth = max(0, depth)
    return None


def inline_parts(text, word):
    """Recover a missing example separator only for a related headword phrase.

    Parenthetical citations and unrelated Latin runs are left for review.
    """
    root = re.sub(r"[()*-]", "", unaccent(word)).lower()[:3]
    if len(root) < 3:
        return [text]
    depth = 0
    for token in re.finditer(r"\S+", text):
        value = token[0]
        if token.start() and depth == 0 and not russian(value) and any("LATIN" in unicodedata.name(c, "") for c in value):
            prefix, candidate = text[:token.start()].strip(), text[token.start():]
            pair = split_example(candidate)
            if pair and any(russian(t) for t in prefix.split()):
                phrase = re.sub(r"[()*-]", "", unaccent(pair[0])).lower()
                if root in phrase:
                    return [prefix] + inline_parts(candidate, word)
        depth = max(0, depth + value.count("(") - value.count(")"))
    return [text]


def headword_spellings(word):
    """Expand optional letters in a heading; never expand grammar annotations."""
    abbreviation = re.fullmatch(r"([^()\s]+)\s+\(([A-Z]+)\)", word)
    if abbreviation:
        return list(abbreviation.groups())
    if "(" not in word and ")" not in word:
        return [word]
    # Broken/nested parentheses need a source correction, not a guessed spelling.
    if re.sub(r"\([^()]+\)", "", word).count("(") or re.sub(r"\([^()]+\)", "", word).count(")"):
        return [word]
    variants = [""]
    end = 0
    for match in re.finditer(r"\(([^()]+)\)", word):
        optional = match[1]
        if not all(c.isalpha() or c == "-" or unicodedata.combining(c) for c in optional):
            return [word]
        prefix = word[end:match.start()]
        # A separated optional suffix belongs to the same spelling.
        if optional.startswith("-"):
            prefix = prefix.rstrip()
        variants = [v + prefix + suffix for v in variants for suffix in (optional, "")]
        end = match.end()
    return unique(v + word[end:] for v in variants)


def structure(article):
    word = article["word"]
    rest = article["text"][len(word):].strip()
    forms, morphology, notes, labels, refs = [word], [], [], [], []
    qualifier_form = None
    precomments = []
    # Leading variants, bracketed forms and abbreviations alternate in the source.
    while rest:
        previous = rest
        if rest.startswith("*"):
            marker = re.match(r"\*+", rest)[0]
            notes.append(f"Знак {marker} в источнике: изменяемый родовой признак")
            rest = rest[len(marker):].strip()
        elif rest.startswith("[") and "]" in rest:
            end = rest.index("]")
            extract_forms(rest[1:end], forms, morphology, notes, refs)
            rest = rest[end + 1:].strip()
        elif rest.startswith(","):
            if re.match(r"\s*[aiprtарт](?=\s|,)", rest[1:]):
                # Origin codes may themselves be comma-separated (r, p).
                rest = rest[1:].lstrip()
                continue
            candidate = split_example(rest[1:].lstrip())
            if (candidate and len(candidate[0].split()) > 1
                    and not any(c in candidate[0] for c in ",;[]=")
                    and not any(grammar_prefix(t.strip("()."))[1] or t in ORIGINS for t in candidate[0].split())):
                # A comma may introduce a whole example, not another spelling.
                rest = rest[1:].lstrip()
                continue
            match = re.match(r",\s*([^,;\[\]\s]+(?:\([^)]*\))?)", rest)
            if match and not russian(match[1]) and match[1] not in ("=",):
                variant = match[1].rstrip("*")
                forms.append(variant)
                qualifier_form = variant
                if match[1].endswith("*"):
                    notes.append("Знак * в источнике: изменяемый родовой признак")
                rest = rest[match.end():].strip()
            elif rest[1:].lstrip().startswith("["):
                rest = rest[1:].lstrip()
        elif rest.startswith("("):
            first = next(groups(rest), None)
            if (first and first[0] == 0 and first[1] < len(rest)
                    and rest[first[1]].isalpha()
                    and re.fullmatch(r"[А-Яа-яЁё]+-?", first[2])
                    and not annotation(first[2])):
                # (на)против / (воз)обновляться are whole Russian words.
                break
            if first and first[0] == 0 and referral(first[2])[0]:
                refs.extend(referral(first[2])[0])
                rest = rest[first[1]:].strip()
            elif first and first[0] == 0 and annotation(first[2]):
                if qualifier_form:
                    morphology.append({"labels": annotation(first[2]), "forms": [qualifier_form]})
                    qualifier_form = None
                else:
                    labels += annotation(first[2])
                rest = rest[first[1]:].strip()
            elif first and first[0] == 0:
                if qualifier_form:
                    notes.append(f"Форма '{qualifier_form}': ({first[2]})")
                    qualifier_form = None
                elif any(russian(t) for t in first[2].split()):
                    precomments.append(first[2])
                else:
                    notes.append(f"Помета источника: ({first[2]})")
                rest = rest[first[1]:].strip()
        else:
            match = re.match(r"([aiprtарт])(?=\s|,)", rest)
            if match:
                code = ORIGIN_GLYPHS.get(match[1], match[1])
                labels.append(ORIGINS[code])
                rest = rest[match.end():].strip()
            elif re.match(r"l\s", rest):
                # Confirmed origin-slot OCR i/l confusion. Parenthesized l and
                # l inside paradigms continue to mean the locative case.
                labels.append(ORIGINS["i"])
                rest = rest[1:].strip()
            else:
                remainder, found = grammar_prefix(rest)
                if found:
                    labels += found
                    rest = remainder
        if rest == previous:
            break
    rest = extract_references(rest, refs)
    lexical = []
    segments = [part for segment in split_top(rest) for part in inline_parts(segment, word)]
    for segment in segments:
        segment = segment.lstrip(", ")
        segment = re.sub(r",\s*\.$", ".", segment)
        if not segment or segment == ".":
            continue
        found_refs, found_labels = referral(segment)
        if found_refs:
            refs += found_refs
            labels += found_labels
            if segment.startswith("=="):
                notes.append("Знак == в источнике")
            continue
        # Referrals on an example belong to that example, not the headword.
        equality = split_top(segment, "=")
        if len(equality) > 1 and equality[0].strip() and not russian(segment.split()[0]):
            av, rhs = equality[0], "=".join(equality[1:])
            av, example_labels, _ = strip_annotations(av.strip())
            target_text, target_comments = prose_comments(rhs)
            values = targets(target_text)
            if values:
                context = "; ".join(["Отсылка при выражении: " + av] + target_comments)
                refs.extend({"target": value, "kind": "spelling", "comment": context} for value in values)
                labels += example_labels
            elif av and any(russian(t) for t in rhs.split()):
                if not lexical:
                    lexical.append({})
                item = {"av": av, "ru": rhs.strip()}
                if example_labels:
                    item["labels"] = example_labels
                lexical[-1].setdefault("examples", []).append(item)
            else:
                notes.append("Неразобранная отсылка: " + segment)
            continue
        example = split_example(segment)
        if example:
            av, ru = example
            av, example_labels, _ = strip_annotations(av)
            av = av.rstrip(",").strip()
            # Bare numbered case codes are grammar, even after a starred form.
            # Restrict this to numbered series: ordinary words may match short codes.
            case_suffix = re.search(r"\s+((?:al|el|l)[1-5])\.?$", av)
            if case_suffix:
                example_labels += grammar_prefix(case_suffix[1])[1]
                av = av[:case_suffix.start()].rstrip()
            ru, comments = prose_comments(ru)
            if case_suffix:
                marker = re.search(r"\*+$", av)
                if marker:
                    comments.insert(0, f"Знак {marker[0]} в источнике: изменяемый родовой признак")
                    av = av[:marker.start()].rstrip()
            if av == "h.":
                av = word + " h."
            for match in reversed(list(re.finditer(r"\[([^\[\]]+)\]", av))):
                comments.insert(0, "Формы выражения в источнике: [" + match[1] + "]")
                av = (av[:match.start()] + av[match.end():]).strip()
            # A final full stop may belong to the removed reference, not to
            # an already complete exclamation/question in the example.
            ru = re.sub(r"([!?])\.$", r"\1", ru)
            item = {"av": av, "ru": ru}
            if example_labels:
                item["labels"] = example_labels
            if comments:
                item["comment"] = "; ".join(comments)
            if not lexical:
                lexical.append({})
            lexical[-1].setdefault("examples", []).append(item)
        elif lexical and lexical[-1].get("examples"):
            # A following Russian-only segment continues the example translation.
            previous = lexical[-1]["examples"][-1]
            field = "ru" if "ru" in previous else "comment"
            previous[field] += "; " + segment
        else:
            segment, segment_labels, _ = strip_annotations(segment)
            sense = {}
            first = next(groups(segment), None)
            if (first and first[0] == 0 and any(russian(t) for t in first[2].split())
                    and (first[1] == len(segment) or not segment[first[1]].isalpha())):
                sense["precomment"] = first[2]
                segment = segment[first[1]:].strip()
            segment, comments = prose_comments(segment)
            if segment:
                sense["text"] = segment.rstrip(",;")
            if segment_labels:
                sense["labels"] = segment_labels
            if comments:
                sense["comment"] = "; ".join(comments)
            lexical.append(sense)
    if not lexical and (labels or notes or precomments):
        lexical.append({})
    for i, sense in enumerate(lexical):
        if precomments and i == 0:
            sense["precomment"] = "; ".join(precomments + ([sense["precomment"]] if sense.get("precomment") else []))
        if labels:
            sense["labels"] = unique(labels + sense.get("labels", []))
        if notes and i == 0:
            sense["comment"] = "; ".join(unique(notes + ([sense["comment"]] if sense.get("comment") else [])))
        # Keep the repository's human-readable sense key order.
        lexical[i] = {k: sense[k] for k in ("text", "precomment", "labels", "comment", "examples") if k in sense}
    # Group equally labelled paradigmatic forms without manufacturing translations.
    grouped = {}
    for item in morphology:
        key = (tuple(item["labels"]), item.get("comment"))
        grouped.setdefault(key, []).extend(item["forms"])
    senses = lexical
    for (group_labels, comment), values in grouped.items():
        group = {"forms": unique(values)}
        if group_labels:
            group = {"labels": list(group_labels), **group}
        if comment:
            group["comment"] = comment
        senses.append(group)
    spellings = headword_spellings(word)
    forms = [variant for form in forms for variant in (spellings if form == word else [form])]
    entry = {"word": spellings[0], "forms": unique(forms)}
    if len(spellings) > 1:
        entry["spelling_forms"] = spellings
    if senses:
        entry["senses"] = senses
    if refs:
        entry["see_also"] = [dict(item) for item in dict.fromkeys(tuple(r.items()) for r in refs)]
    entry["source"] = SOURCE
    entry = canonical_latin_fields(entry)
    accented = entry["word"]
    clean, stress = headword_stress(accented)
    if stress is not None:
        entry = {"word": clean, "stress": stress, **{k: v for k, v in entry.items() if k != "word"}}
        for field in ("spelling_forms",):
            if field in entry:
                entry[field] = unique(clean if value == accented else value for value in entry[field])
    return extract_form_stresses(entry)


def parse(html):
    source = articles(html)
    entries = [structure(article) for article in source]
    headings = {normalize_unicode(article["word"]): entry["word"] for article, entry in zip(source, entries)}
    for entry in entries:
        for reference in entry.get("see_also", []):
            before = reference["target"]
            reference["target"] = headings.get(before, before)
            if reference["target"] != before and headword_stress(before)[1] is not None:
                note = "Ударение цели в источнике: " + before
                reference["comment"] = "; ".join(filter(None, (reference.get("comment"), note)))
    return entries


if __name__ == "__main__":
    entries = parse((ROOT / "books" / SOURCE / f"{SOURCE}.html").read_text(encoding="utf-8"))
    output = ROOT / "data" / f"{SOURCE}.jsonl"
    output.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries), encoding="utf-8")
    print(f"{output}: {len(entries)} entries")
