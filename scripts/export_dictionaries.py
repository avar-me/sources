#!/usr/bin/env python3
"""Export av-ru.jsonl / ru-av.jsonl into DSL and StarDict for dictionary apps
(GoldenDict, Lingvo, Aard2, etc.).

NOT part of the automated site build (src/build_site.py never calls this) --
it depends on the third-party `pyglossary` package, which the rest of the
build deliberately avoids. Run it manually whenever av-ru.jsonl/ru-av.jsonl
change meaningfully, and commit the regenerated files under exports/.

Usage:
    python3 -m venv .venv-export && .venv-export/bin/pip install pyglossary
    .venv-export/bin/python scripts/export_dictionaries.py
"""
from __future__ import annotations

import html as htmllib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORTS = ROOT / "exports"


def load_entries(path: Path) -> list[dict]:
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ---------- DSL (ABBYY Lingvo) ----------

def dsl_escape(text: str | None) -> str:
    if not text:
        return ""
    return (
        text.replace("\\", "\\\\")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("{", "\\{")
        .replace("}", "\\}")
    )


def render_definition_dsl(entry: dict) -> str:
    lines = []
    meta_bits = []
    if entry.get("pos"):
        meta_bits.append(entry["pos"])
    if entry.get("form") and entry["form"] != "—":
        meta_bits.append(entry["form"])
    if meta_bits:
        lines.append(f'[m1][i]{dsl_escape(", ".join(meta_bits))}[/i][/m1]')

    forms = entry.get("forms") or []
    if len(forms) > 1:
        lines.append(f'[m1][i]формы:[/i] {dsl_escape(", ".join(forms))}[/m1]')
    gforms = entry.get("gender_forms") or []
    if gforms:
        lines.append(f'[m1][i]формы по классам:[/i] {dsl_escape(", ".join(gforms))}[/m1]')

    senses = entry.get("senses") or []
    multi = len(senses) > 1
    for i, sense in enumerate(senses, 1):
        prefix = f"{i}. " if multi else ""
        bold = f"[b]{prefix}[/b]" if prefix else ""
        text = sense.get("text") or ""
        precomment = sense.get("precomment")
        pre_str = f'[i]{dsl_escape(precomment)}[/i] ' if precomment else ""
        labels = sense.get("labels") or []
        label_str = f' [i]({dsl_escape(", ".join(labels))})[/i]' if labels else ""
        comment = sense.get("comment")
        comment_str = (
            f' [i]{dsl_escape(comment)}[/i]'
            if comment and sense.get("comment_lang") != "av"
            else ""
        )
        if text or label_str or comment_str:
            lines.append(f'[m1]{bold}{pre_str}{dsl_escape(text)}{label_str}{comment_str}[/m1]')

        for ex in sense.get("examples") or []:
            av = dsl_escape(ex.get("av", ""))
            ru = dsl_escape(ex.get("ru", ""))
            ex_comment = ex.get("comment")
            comment_tail = f' [i]({dsl_escape(ex_comment)})[/i]' if ex_comment else ""
            if av or ru:
                lines.append(f'[m2][ex]{av} — {ru}{comment_tail}[/ex][/m2]')

    see_also = entry.get("see_also") or []
    if see_also:
        refs = ", ".join(f'[ref]{dsl_escape(sa["target"])}[/ref]' for sa in see_also)
        lines.append(f'[m1][i]см. также:[/i] {refs}[/m1]')

    return "\n".join(lines) if lines else "[m1](нет данных)[/m1]"


def write_dsl(entries: list[dict], out_path: Path, dict_name: str, index_lang: str, contents_lang: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"#NAME\t{dict_name}\n")
        f.write(f"#INDEX_LANGUAGE\t{index_lang}\n")
        f.write(f"#CONTENTS_LANGUAGE\t{contents_lang}\n\n")
        for e in entries:
            word = e.get("word", "")
            if not word:
                continue
            f.write(word + "\n")
            for line in render_definition_dsl(e).split("\n"):
                f.write("\t" + line + "\n")
            f.write("\n")


# ---------- StarDict (via pyglossary) ----------

def html_escape(text: str | None) -> str:
    return htmllib.escape(text or "")


def render_definition_html(entry: dict) -> str:
    parts = []
    meta_bits = []
    if entry.get("pos"):
        meta_bits.append(entry["pos"])
    if entry.get("form") and entry["form"] != "—":
        meta_bits.append(entry["form"])
    if meta_bits:
        parts.append(f'<p><i>{html_escape(", ".join(meta_bits))}</i></p>')

    forms = entry.get("forms") or []
    if len(forms) > 1:
        parts.append(f'<p><i>формы:</i> {html_escape(", ".join(forms))}</p>')
    gforms = entry.get("gender_forms") or []
    if gforms:
        parts.append(f'<p><i>формы по классам:</i> {html_escape(", ".join(gforms))}</p>')

    senses = entry.get("senses") or []
    multi = len(senses) > 1
    parts.append("<ol>" if multi else "<div>")
    tag = "li" if multi else "p"
    for sense in senses:
        text = sense.get("text") or ""
        precomment = sense.get("precomment")
        pre_str = f"<i>{html_escape(precomment)}</i> " if precomment else ""
        labels = sense.get("labels") or []
        label_str = f' <i>({html_escape(", ".join(labels))})</i>' if labels else ""
        comment = sense.get("comment")
        comment_str = (
            f' <i>{html_escape(comment)}</i>'
            if comment and sense.get("comment_lang") != "av"
            else ""
        )
        parts.append(f"<{tag}>{pre_str}<b>{html_escape(text)}</b>{label_str}{comment_str}")
        examples = sense.get("examples") or []
        if examples:
            parts.append("<ul>")
            for ex in examples:
                av = html_escape(ex.get("av", ""))
                ru = html_escape(ex.get("ru", ""))
                ex_comment = ex.get("comment")
                comment_tail = f" <i>({html_escape(ex_comment)})</i>" if ex_comment else ""
                parts.append(f"<li>{av} — {ru}{comment_tail}</li>")
            parts.append("</ul>")
        parts.append(f"</{tag}>")
    parts.append("</ol>" if multi else "</div>")

    see_also = entry.get("see_also") or []
    if see_also:
        refs = ", ".join(html_escape(sa["target"]) for sa in see_also)
        parts.append(f'<p><i>см. также:</i> {refs}</p>')

    return "".join(parts)


def write_stardict(entries: list[dict], out_base: Path, dict_name: str, description: str) -> None:
    try:
        from pyglossary.glossary_v2 import Glossary
    except ImportError:
        print("pyglossary not installed -- skipping StarDict export. "
              "Install with: pip install pyglossary", file=sys.stderr)
        return

    Glossary.init()
    glos = Glossary()
    glos.setInfo("title", dict_name)
    glos.setInfo("author", "avar.me")
    glos.setInfo("description", description)
    for e in entries:
        word = e.get("word", "")
        if not word:
            continue
        defi = render_definition_html(e)
        glos.addEntry(glos.newEntry([word], defi, defiFormat="h"))
    out_base.parent.mkdir(parents=True, exist_ok=True)
    glos.write(str(out_base), formatName="Stardict")


# ---------- main ----------

SOURCES = [
    {
        "data": "data/av-ru.jsonl",
        "out_dir": EXPORTS / "av-ru",
        "name": "Аварско-русский словарь (sources.avar.me)",
        "description": "Аварско-русский словарь, около 22 800 статей. Источник: sources.avar.me/av-ru",
        "index_lang": "Avar",
        "contents_lang": "Russian",
        "base": "av-ru",
    },
    {
        "data": "data/ru-av.jsonl",
        "out_dir": EXPORTS / "ru-av",
        "name": "Русско-аварский словарь (sources.avar.me)",
        "description": "Русско-аварский словарь, около 38 900 статей. Источник: sources.avar.me/ru-av",
        "index_lang": "Russian",
        "contents_lang": "Avar",
        "base": "ru-av",
    },
]


def main() -> None:
    for spec in SOURCES:
        entries = load_entries(ROOT / spec["data"])
        print(f"{spec['data']}: {len(entries):,} entries")

        dsl_path = spec["out_dir"] / f"{spec['base']}.dsl"
        write_dsl(entries, dsl_path, spec["name"], spec["index_lang"], spec["contents_lang"])
        print(f"  wrote {dsl_path}")

        stardict_base = spec["out_dir"] / spec["base"]
        write_stardict(entries, stardict_base, spec["name"], spec["description"])
        print(f"  wrote {stardict_base}.ifo/.idx/.dict")


if __name__ == "__main__":
    main()
