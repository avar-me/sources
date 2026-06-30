#!/usr/bin/env python3
"""One-shot parser: ns/*.{docx,doc} -> data/mukhidinov-library.jsonl.

Reads six contemporary Avar books (provided by Mukhidinovs) from the `books/`
folder and emits one JSONL record per book.

Run once after the originals are placed in `books/` under the names expected
below. Requires `python-docx` for .docx and `textutil` (macOS) for .doc.

    python3 -m venv .venv && source .venv/bin/activate
    pip install python-docx
    python src/parse_mukhidinov_library.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ROOT / "books"
DATA = ROOT / "data" / "mukhidinov-library.jsonl"


# Palochka normalization. See rules in CLAUDE.md (раздел «Аварская графика»).
# Палочка допускается только внутри диграфа (после т/г/к/х/ц/ч).
# Регистр палочки совпадает с регистром базовой буквы:
#   строчная ӏ (U+04CF) после строчной базы,
#   заглавная Ӏ (U+04C0) после заглавной базы.
# Палочка-глиф вне диграфа → цифра «1» (годы, нумерация и т. п.).
# Латиница I/i/l внутри диграфа → палочка; вне диграфа около цифры → «1»,
# иначе оставляем как есть (может быть осмысленной латиницей).
PALOCHKA_GLYPHS = set("Ӏӏ|ǀ")
LATIN_LOOKALIKES = set("Iil")
DIGRAPH_BASE_UP = set("ТГКХЦЧ")
DIGRAPH_BASE_LO = set("тгкхцч")


def normalize_palochka(text: str) -> str:
    chars = list(text)
    n = len(chars)
    out: list[str] = []
    idx = 0
    while idx < n:
        ch = chars[idx]
        if ch in PALOCHKA_GLYPHS or ch in LATIN_LOOKALIKES or ch == "1":
            prev_ch = chars[idx - 1] if idx > 0 else ""
            if prev_ch in DIGRAPH_BASE_UP:
                out.append("\u04C0")
                idx += 1
                while idx < n and (
                    chars[idx] in PALOCHKA_GLYPHS
                    or chars[idx] in LATIN_LOOKALIKES
                    or chars[idx] == "1"
                ):
                    idx += 1
                continue
            if prev_ch in DIGRAPH_BASE_LO:
                out.append("\u04CF")
                idx += 1
                while idx < n and (
                    chars[idx] in PALOCHKA_GLYPHS
                    or chars[idx] in LATIN_LOOKALIKES
                    or chars[idx] == "1"
                ):
                    idx += 1
                continue
            if ch == "1":
                out.append("1")
                idx += 1
                continue
            if ch in PALOCHKA_GLYPHS:
                out.append("1")
                idx += 1
                continue
            run_start = idx
            while idx < n and chars[idx] in LATIN_LOOKALIKES:
                idx += 1
            after_ch = chars[idx] if idx < n else ""
            if (prev_ch.isascii() and prev_ch.isalpha()) or (
                after_ch.isascii() and after_ch.isalpha()
            ):
                out.extend(chars[run_start:idx])
            else:
                out.extend(["1"] * (idx - run_start))
        else:
            out.append(ch)
            idx += 1
    return "".join(out)


def collapse_blank_lines(text: str) -> str:
    # Trim trailing whitespace on each line, collapse 3+ blank lines to 2.
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: list[str] = []
    blank = 0
    for ln in lines:
        if not ln:
            blank += 1
            if blank <= 1:
                out.append("")
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip() + "\n"


def read_docx(path: Path) -> str:
    import docx  # type: ignore

    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def read_doc(path: Path) -> str:
    # macOS-bundled textutil handles legacy .doc -> txt conversion well.
    out = subprocess.run(
        ["textutil", "-convert", "txt", "-encoding", "UTF-8", "-stdout", str(path)],
        check=True, capture_output=True, text=True,
    )
    return out.stdout


def load_book(path: Path) -> str:
    text = read_docx(path) if path.suffix.lower() == ".docx" else read_doc(path)
    text = normalize_palochka(text)
    return collapse_blank_lines(text)


# slug -> (filename in books/, title, author, editor, date, categories)
BOOKS_META = [
    {
        "slug": "mukhidinov-tohal",
        "file": "Mukhidinov_Tohal_2024.docx",
        "title": "ТӀохал… тӀохал… тӀохал…",
        "author": "Шамил МухӀидинов",
        "editor": None,
        "date": "2024-01-01",
        "categories": ["essays", "criticism"],
    },
    {
        "slug": "mukhidinov-sakhavatab-ganhvaro",
        "file": "Mukhidinov_Sakhavatab-ganhvaro_2022.docx",
        "title": "Сахаватаб гӀанхваро. Басняби",
        "author": "Шамил МухӀидинов",
        "editor": None,
        "date": "2022-01-01",
        "categories": ["fables", "poetry"],
    },
    {
        "slug": "avar-teachers-forum-2",
        "file": "Avar-teachers-forum-2_2017.docx",
        "title": "Аваразул пашманлъи — авар мацӀ лъачӀел лъимал. Доклады со 2-го форума учителей авар. яз.",
        "author": "Коллектив авторов (форум учителей авар. яз.)",
        "editor": "Баху Ш. МухӀидинова",
        "date": "2017-04-22",
        "categories": ["forum", "education", "essays"],
    },
    {
        "slug": "galbatsov-tirulev-sverulev",
        "file": "Galbatsov_Tirulev-sverulev_2015.docx",
        "title": "Тирулеб сверулеб гьобоги буго… Публицистика",
        "author": "ГъазимухӀамад ГъалбацӀов",
        "editor": "Баху МухӀидинова",
        "date": "2015-01-01",
        "categories": ["publicistic"],
    },
    {
        "slug": "daci-moi-hukumat",
        "file": "Daci_Moi-Hukumat_2013.docx",
        "title": "Мой ХӀукумат. КучӀдул",
        "author": "БакьагьечӀиса Даци (МухӀамад ХӀосенов)",
        "editor": "Баху Ш. МухӀидинова",
        "date": "2013-01-01",
        "categories": ["poetry", "satire"],
    },
    {
        "slug": "galbatsov-kalelalde-hvaral-harbal",
        "file": "Galbatsov_Kalelalde-hvaral-harbal.doc",
        "title": "Къалъелалде хъварал харбал",
        "author": "ГъазимухӀамад ГъалбацӀов",
        "editor": None,
        "date": "2010-01-01",
        "categories": ["prose"],
    },
]


def main() -> int:
    records: list[dict] = []
    missing: list[str] = []

    for meta in BOOKS_META:
        src = BOOKS / meta["file"]
        if not src.exists():
            missing.append(meta["file"])
            continue
        text = load_book(src)
        rec = {
            "slug": meta["slug"],
            "title": meta["title"],
            "author": meta["author"],
            "date": meta["date"],
            "categories": meta["categories"],
            "book_path": f"books/{meta['file']}",
            "text": text,
        }
        if meta["editor"]:
            rec["editor"] = meta["editor"]
        records.append(rec)
        print(f"  {meta['file']}: {len(text):,} chars, "
              f"{text.count(chr(10)):,} lines")

    if missing:
        print("Missing source files in books/:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        print("Place the originals there and re-run.", file=sys.stderr)
        return 1

    # Sort by date descending (matches build_articles sort order).
    records.sort(key=lambda r: r["date"], reverse=True)

    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total_chars = sum(len(r["text"]) for r in records)
    print(f"Wrote {len(records)} records, {total_chars:,} characters -> {DATA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
