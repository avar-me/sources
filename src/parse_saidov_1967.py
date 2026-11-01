#!/usr/bin/env python3
"""First-pass structural import of the Saidov 1967 Avar-Russian dictionary.

Source: `books/av-ru.1967/av-ru.1967.html` (OCR, already modern Avar
Cyrillic -- no transliteration needed, unlike av-ru.1936). This is a
*structural* pass only: it preserves article boundaries, the headword
(with stress moved to a `stress` field, same convention as the rest of
this project) and the raw Russian gloss text as a single `text` string.
Breaking `text` down into `senses`/`examples`/`labels` the way
av-ru.1936 and av-ru.2006 do is deliberate follow-up work, not done
here -- see books/av-ru.1967/README.md.

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
        if bold and re.search(r"[А-Яа-яЁё]", text):
            raw_heading = plain(bold[2])
            star = bool(bold[1]) or raw_heading.startswith("*")
            raw_heading = raw_heading.lstrip("*")
            heading = raw_heading.split(",", 1)[0].split("||", 1)[0].strip()
            word, stress = headword_stress(heading)
            spelling_forms = None
            if "||" in raw_heading:
                variants = [unaccent(v).strip() for v in raw_heading.split("||")]
                spelling_forms = [unaccent(word)] + [v for v in variants[1:] if v]
            entry = {"word": word, "text": text, "page": page}
            if stress is not None:
                entry["stress"] = stress
            if star:
                entry["class_marker"] = True
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


def build_entry(article):
    entry = {
        "word": article["word"],
        "text": article["text"],
        "source": SOURCE,
    }
    if "stress" in article:
        entry["stress"] = article["stress"]
    if article.get("spelling_forms"):
        entry["spelling_forms"] = article["spelling_forms"]
    if article.get("class_marker"):
        entry["comment"] = "Перед словом в источнике стоит звёздочка: слово имеет классный показатель"
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
