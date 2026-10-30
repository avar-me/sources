#!/usr/bin/env python3
"""Conservative Unicode and grammatical-abbreviation normalization of the OCR.

Run --apply to update the canonical HTML, then rebuild JSONL.
The archival DOCX is updated only with the explicit --include-docx option. Unknown marks are preserved, never stripped.
"""

import argparse
from difflib import SequenceMatcher
import html
import json
from pathlib import Path
import re
import unicodedata as ud
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "books/av-ru.1936"

# Exact, source-verified graphic aliases. Distinct historical letters stay
# distinct: ħ/ḩ, ļ/ł, x̨/x̵, z/ƶ/ⱬ and q/ꝗ are never collapsed.
ALIASES = {
    **{f"t{mark}": "ţ" for mark in ("\u0323", "\u0327", "\u0326", "\u0328", "\u0307", "\u0331")},
    **{f"k{mark}": "ķ" for mark in ("\u0323", "\u0327", "\u0326", "\u0328", "\u0307")},
    "ƙ": "ķ", "ⱪ": "ķ",
    **{f"c{mark}": "ç" for mark in ("\u0323", "\u0327", "\u0328")},
    "h\u0323": "ḩ", "h\u0327": "ḩ", "h\u0326": "ḩ",
    **{f"l{mark}": "ļ" for mark in ("\u0323", "\u0327", "\u0326")},
    # ɫ is ambiguous (e.g. Bolqarija): keep it for contextual review.
    "ɬ": "ļ", "ɭ": "ļ",
    "ơ": "ƣ", "ʐ": "ⱬ",
    "x\u0326": "x̨", "x\u0327": "x̨", "x\u0328": "x̨",
    "x\u030c": "x̵", "x\u0304": "x̵", "χ": "x̵",
    **{f"z{mark}": "ⱬ" for mark in ("\u0323", "\u0327", "\u0326", "\u0328", "\u0307", "\u0309", "\u0304")},
    "z\u0335": "ƶ", "q\u0335": "ꝗ", "s\u0335": "ꞩ",
    "ı": "i", "ɩ": "i", "ɪ": "i", "ɡ": "g", "ⱼ": "j",
}
CODE_ALIASES = {
    "11": "l1", "12": "l2", "13": "l3", "14": "l4", "15": "l5",
    "I1": "l1", "I2": "l2", "I3": "l3", "I4": "l4", "I5": "l5",
    "ll": "l1", "II": "l1", "pcs": "pos", "poc": "pos", "adu": "adv", "ʃ": "f",
}
CODE_RE = re.compile(r"(?<!\w)(" + "|".join(CODE_ALIASES) + r")(?=\s+[^\W\d_])")


def normalize_unicode(text):
    clusters = re.findall(r"[^\u0300-\u036f][\u0300-\u036f]*|[\u0300-\u036f]+", ud.normalize("NFD", text))
    output = []
    for cluster in clusters:
        stress = "".join(c for c in cluster[1:] if c in "\u0301\u0300")
        core = "".join(c for c in cluster if c not in "\u0301\u0300")
        replacement = ALIASES.get(core.lower())
        if replacement:
            if core[:1].isupper():
                replacement = replacement.upper()
            output.append(replacement + stress)
        else:
            output.append(cluster)
    return ud.normalize("NFC", "".join(output))


def normalize_codes(text):
    # A number or ambiguous OCR l/I sequence is a code only in these slots.
    def bracket(match):
        value = CODE_RE.sub(lambda m: CODE_ALIASES[m[1]], match[1])
        value = re.sub(r"\bact p(?=\s)", "act pl", value)
        return "[" + value + "]"
    text = re.sub(r"\[([^\[\]]*)\]", bracket, text)
    text = re.sub(r"\((" + "|".join(CODE_ALIASES) + r")\)", lambda m: "(" + CODE_ALIASES[m[1]] + ")", text)
    # Only the origin slot immediately before the first Russian gloss outside
    # brackets/parentheses. Bare l inside a paradigm remains a locative label.
    depth = 0
    previous = None
    for token in re.finditer(r"\S+", text):
        value = token[0]
        letters = [c for c in value if c.isalpha()]
        is_russian = letters and sum("CYRILLIC" in ud.name(c, "") for c in letters) > len(letters) / 2
        if depth == 0 and is_russian:
            if previous and previous[0] == "l":
                return text[:previous.start()] + "i" + text[previous.end():]
            break
        depth = max(0, depth + value.count("[") + value.count("(") - value.count("]") - value.count(")"))
        previous = token
    return text


def normalize_text(text):
    return normalize_codes(normalize_unicode(text))


def patch_parts(parts, before, after):
    """Apply a character diff across styled runs without changing their markup."""
    offsets, offset = [], 0
    for part in parts:
        offsets.append(offset)
        offset += len(part[0])
    edits = []
    cluster_re = re.compile(r"[^\u0300-\u036f][\u0300-\u036f]*|[\u0300-\u036f]+")
    for tag, start, end, a, b in SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        old_clusters = list(cluster_re.finditer(before[start:end]))
        new_clusters = list(cluster_re.finditer(after[a:b]))
        if tag == "replace" and len(old_clusters) == len(new_clusters):
            # Keep adjacent normalized graphemes in their original styled runs.
            edits += [(start + old.start(), start + old.end(), new[0])
                      for old, new in zip(old_clusters, new_clusters)]
        else:
            edits.append((start, end, after[a:b]))
    for start, end, replacement in reversed(edits):
        if start == end:
            if replacement and ud.combining(replacement[0]) and start:
                # A new combining mark belongs to the preceding grapheme,
                # including when a bold HTML/run boundary follows that base.
                index = max(i for i, off in enumerate(offsets) if off < start <= off + len(parts[i][1]))
            else:
                index = max(i for i, off in enumerate(offsets) if off <= start)
            local = start - offsets[index]
            parts[index][0] = parts[index][0][:local] + replacement + parts[index][0][local:]
            continue
        affected = [i for i, off in enumerate(offsets) if off < end and off + len(parts[i][1]) > start]
        for i in affected:
            value = parts[i][0]
            left, right = max(0, start - offsets[i]), min(len(parts[i][1]), end - offsets[i])
            parts[i][0] = value[:left] + (replacement if i == affected[0] else "") + value[right:]


def normalize_fragment(fragment):
    pieces = re.split(r"(<[^>]*>)", fragment)
    indices = list(range(0, len(pieces), 2))
    parts = [[html.unescape(pieces[i]), html.unescape(pieces[i])] for i in indices]
    before = "".join(p[0] for p in parts)
    after = normalize_text(before)
    patch_parts(parts, before, after)
    assert "".join(p[0] for p in parts) == after
    for i, part in zip(indices, parts):
        if part[0] != part[1]:
            pieces[i] = html.escape(part[0], quote=False)
    return "".join(pieces), before, after


def apply(include_docx=False):
    html_path, docx_path = BOOK / "av-ru.1936.html", BOOK / "av-ru.1936.docx"
    source = html_path.read_text(encoding="utf-8")
    changes = {"html": [], "docx": []}
    def paragraph(match):
        value, before, after = normalize_fragment(match[1])
        if before != after:
            changes["html"].append({"before": before, "after": after})
        return "<p>" + value + "</p>"
    result = re.sub(r"<p>(.*?)</p>", paragraph, source, flags=re.S)
    if not include_docx:
        html_path.write_text(result, encoding="utf-8")
        return changes
    from lxml import etree as E
    with zipfile.ZipFile(docx_path) as z:
        infos = z.infolist()
        members = {i.filename: z.read(i.filename) for i in infos}
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    document = E.fromstring(members["word/document.xml"])
    for p in document.findall(".//w:p", ns):
        nodes = p.findall(".//w:t", ns)
        parts = [[t.text or "", t.text or ""] for t in nodes]
        before = "".join(part[0] for part in parts)
        after = normalize_text(before)
        if before == after:
            continue
        patch_parts(parts, before, after)
        assert "".join(part[0] for part in parts) == after
        for t, part in zip(nodes, parts):
            if part[0] != part[1]:
                t.text = part[0]
                if part[0].startswith(" ") or part[0].endswith(" "):
                    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        changes["docx"].append({"before": before, "after": after})
    members["word/document.xml"] = E.tostring(document, encoding="UTF-8", xml_declaration=True, standalone=True)
    temporary = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(temporary, "w") as z:
        for info in infos:
            z.writestr(info, members[info.filename])
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
    html_path.write_text(result, encoding="utf-8")
    temporary.replace(docx_path)
    return changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--include-docx", action="store_true", help="Also update the archival Word snapshot (normally HTML only)")
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    if not args.apply:
        parser.error("Use --apply explicitly to update the editable sources")
    changes = apply(include_docx=args.include_docx)
    if args.log:
        args.log.write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({name: len(items) for name, items in changes.items()})
