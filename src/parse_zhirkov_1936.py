#!/usr/bin/env python3
"""Conservative import of Zhirkov's Latin-script dictionary from supplied OCR HTML.

Run from any directory: python3 src/parse_zhirkov_1936.py
No transliteration, spelling correction, stress removal or semantic inference.
The first bold headword becomes word; the rest of the article stays in one
sense.text, including variants, grammatical notation, references and examples.
Original HTML/DOCX/PDF remain available for subsequent editorial work.
"""

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "av-ru.1936"


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


def parse(html):
    entries = []
    page = 0
    for match in re.finditer(r"<!-- p(\d+).*?-->|<p>(.*?)</p>", html, re.S):
        if match[1]:
            page = int(match[1])
            continue
        # OCR scan order: dictionary starts on scan 7; scans 8–9 are
        # displaced introductory pages. Appendices begin on scan 143.
        if not (page == 7 or 10 <= page <= 142):
            continue
        fragment = match[2]
        text = plain(fragment)
        # Alphabet headings, sound-comparison footers and printing signatures.
        if not re.search(r"[А-Яа-яЁё]|=", text):
            continue
        bold = re.match(r"\s*<b>(.*?)</b>", fragment, re.S)
        if bold:
            heading = plain(bold[1])
            # Some OCR paragraphs bold several variants or even the whole line.
            word = heading.split(",", 1)[0].rstrip("*").strip()
            remainder = text[len(word):].strip()
            if not word or not remainder:
                raise ValueError(f"Incomplete entry on scan {page}: {text}")
            entries.append({"word": word, "senses": [{"text": remainder}], "source": SOURCE})
        else:
            if not entries:
                raise ValueError(f"Orphan continuation on scan {page}: {text}")
            # Page/column continuations keep their OCR spelling and hyphens.
            entries[-1]["senses"][0]["text"] += " " + text
    return entries


if __name__ == "__main__":
    entries = parse((ROOT / "books" / SOURCE / f"{SOURCE}.html").read_text(encoding="utf-8"))
    output = ROOT / "data" / f"{SOURCE}.jsonl"
    output.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries), encoding="utf-8")
    print(f"{output}: {len(entries)} entries")
