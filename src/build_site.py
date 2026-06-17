#!/usr/bin/env python3
"""Builder for sources.avar.me.

Reads `sources.json` + `data/*.jsonl` and emits a static site into `docs/`.
Layout:
    docs/index.html              — catalog landing
    docs/sources.json            — copy of root catalog
    docs/styles.css, app.js      — shared assets
    docs/data/<id>.jsonl         — raw downloadable sources
    docs/<id>/index.html         — dictionary table of contents (letter nav)
    docs/<id>/<letter>.html      — entries for one letter (inline, anchors)

Zero external deps (stdlib only). Run `./build.sh` from repo root.
"""

from __future__ import annotations

import html
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = ROOT / "data"
CATALOG = ROOT / "sources.json"
TEMPLATES = ROOT / "src" / "templates"

TELEGRAM = "https://t.me/avarlangme"
GITHUB_REPO = "https://github.com/avar-me/sources"

# Max entries per HTML page. Larger letters get split into several.
PAGE_SIZE = 500

REPORT_TEMPLATE = (
    "Здравствуйте! Заметил неточность в словаре {dict_id}:\n"
    "слово: {word}\n"
    "ссылка: https://sources.avar.me/{dict_id}/{page_file}#word-{anchor}\n\n"
    "Должно быть: ..."
)


def esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def first_letter(word: str) -> str:
    if not word:
        return "?"
    return word[0].lower()


def anchor_for(word: str, seen: dict[str, int]) -> str:
    base = word.replace(" ", "_").replace("/", "_")
    seen[base] += 1
    return base if seen[base] == 1 else f"{base}-{seen[base]}"


def url_quote(text: str) -> str:
    from urllib.parse import quote
    return quote(text, safe="")


def load_jsonl(path: Path) -> list[dict]:
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


# Order used both for letter buckets and for words within a bucket.
# Both ru-av and av-ru sit on top of Cyrillic, so a Russian-alphabet order
# is right for both. Avar digraphs (гь, кӏ, …) fall under their first letter.
ALPHABET_ORDER = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
_CHAR_RANK = {ch: i for i, ch in enumerate(ALPHABET_ORDER)}


def _char_rank(ch: str) -> int:
    # Unknown chars (suffix dash, digits, etc.) go to the end of the book.
    return _CHAR_RANK.get(ch.lower(), 10_000 + ord(ch))


def sort_key(word: str) -> tuple:
    word = word or ""
    return (tuple(_char_rank(c) for c in word.lower()), word)


def group_by_letter(entries: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        word = entry.get("word", "")
        grouped[first_letter(word)].append(entry)
    for letter in grouped:
        grouped[letter].sort(key=lambda e: sort_key(e.get("word", "")))
    return grouped


# ---------- HTML rendering ----------

def render_labels(labels) -> str:
    if not labels:
        return ""
    chips = "".join(f'<span class="label">{esc(lab)}</span>' for lab in labels if lab)
    return f'<span class="labels">{chips}</span>'


def render_examples(examples) -> str:
    if not examples:
        return ""
    items = []
    for ex in examples:
        av = esc(ex.get("av", ""))
        ru = esc(ex.get("ru", ""))
        labels = render_labels(ex.get("labels"))
        comment = ex.get("comment")
        comment_html = f' <span class="ex-comment">({esc(comment)})</span>' if comment else ""
        items.append(
            '<li class="example">'
            f'<span class="ex-av">{av}</span>'
            f'<span class="ex-sep"> — </span>'
            f'<span class="ex-ru">{ru}</span>'
            f'{comment_html}{labels}'
            '</li>'
        )
    return f'<ul class="examples">{"".join(items)}</ul>'


def render_see_also(see_also, word_to_page: dict[str, str]) -> str:
    if not see_also:
        return ""
    kind_label = {"see": "см.", "from": "от", "syn": "синоним"}
    items = []
    for ref in see_also:
        if isinstance(ref, str):
            target, kind = ref, "see"
        else:
            target = ref.get("target") or ref.get("ref") or ""
            kind = ref.get("kind") or "see"
        if not target:
            continue
        page_file = word_to_page.get(target)
        if page_file:
            href = f'{page_file}#word-{url_quote(target)}'
            link = f'<a href="{href}">{esc(target)}</a>'
        else:
            link = esc(target)
        label = kind_label.get(kind, kind)
        items.append(f'<li><span class="see-kind">{esc(label)}</span> {link}</li>')
    if not items:
        return ""
    return f'<aside class="see-also"><ul>{"".join(items)}</ul></aside>'


def render_sense(sense: dict, idx: int, total: int) -> str:
    text = sense.get("text") or ""
    comment = sense.get("comment") or ""
    labels = sense.get("labels") or []
    examples = sense.get("examples") or []
    masdarfrom = sense.get("masdarfrom")
    forceto = sense.get("forceto")

    parts = ['<li class="sense">' if total > 1 else '<div class="sense">']
    if total > 1:
        parts.append(f'<span class="sense-num">{idx}.</span>')

    head_bits = []
    if labels:
        head_bits.append(render_labels(labels))
    if head_bits:
        parts.append(f'<span class="sense-meta">{"".join(head_bits)}</span>')

    if text:
        parts.append(f'<span class="sense-text">{esc(text)}</span>')
    if comment:
        parts.append(f' <span class="sense-comment">({esc(comment)})</span>')

    if masdarfrom:
        parts.append(f' <span class="sense-ref">→ масдар от <em>{esc(masdarfrom)}</em></span>')
    if forceto:
        parts.append(f' <span class="sense-ref">→ понуд. от <em>{esc(forceto)}</em></span>')

    parts.append(render_examples(examples))
    parts.append("</li>" if total > 1 else "</div>")
    return "".join(parts)


def render_entry(entry: dict, anchor: str, word_to_page: dict[str, str], dict_id: str, page_file: str) -> str:
    word = entry.get("word", "")
    forms = entry.get("forms") or []
    senses = entry.get("senses") or []
    see_also = entry.get("see_also")

    # show forms that differ from the headword
    extra_forms = [f for f in forms if f and f != word]
    forms_html = ""
    if extra_forms:
        forms_html = f'<p class="entry-forms">{esc(", ".join(extra_forms))}</p>'

    senses_html_inner = "".join(
        render_sense(s, i + 1, len(senses)) for i, s in enumerate(senses)
    )
    if len(senses) > 1:
        senses_html = f'<ol class="senses">{senses_html_inner}</ol>'
    else:
        senses_html = f'<div class="senses">{senses_html_inner}</div>'

    see_also_html = render_see_also(see_also, word_to_page)

    report_text = REPORT_TEMPLATE.format(
        dict_id=dict_id,
        word=word,
        page_file=page_file,
        anchor=anchor,
    )
    report_href = f'{TELEGRAM}?text={url_quote(report_text)}'

    return (
        f'<article class="entry" id="word-{esc(anchor)}">'
        f'<header class="entry-head">'
        f'<h2 class="entry-word">{esc(word)}</h2>'
        f'{forms_html}'
        f'</header>'
        f'{senses_html}'
        f'{see_also_html}'
        f'<footer class="entry-foot">'
        f'<a class="report-link" href="{report_href}" target="_blank" rel="noopener" '
        f'title="Сообщить об ошибке в Telegram">сообщить о неточности</a>'
        f'</footer>'
        f'</article>'
    )


# ---------- Page templates ----------

def page_head(title: str, description: str, asset_prefix: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{esc(description)}">
<title>{esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&family=Onest:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset_prefix}styles.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>☀</text></svg>">
</head>
<body>
<div class="bg-pattern" aria-hidden="true"></div>
"""


def footer_html(asset_prefix: str = "") -> str:
    return (
        '<footer class="site-footer">'
        f'<p>Сообщайте об ошибках в Telegram: <a href="{TELEGRAM}">@avarlangme</a></p>'
        f'<p>Проект <a href="https://avar.me">avar.me</a> · '
        f'<a href="{GITHUB_REPO}">github.com/avar-me/sources</a></p>'
        '</footer></body></html>'
    )


def render_catalog(catalog: dict, stats: dict[str, dict]) -> str:
    items = []
    for src in catalog["sources"]:
        sid = src["id"]
        s = stats.get(sid, {})
        entry_count = s.get("entry_count", 0)
        items.append(f"""
<article class="catalog-card">
  <header class="card-top">
    <h2><a href="{esc(src['site_path'])}">{esc(src['title'])}</a></h2>
    <span class="badge badge-{esc(src.get('status', 'stable'))}">{esc(src.get('status', 'stable'))}</span>
  </header>
  <p class="card-sub">{esc(src.get('subtitle', ''))} · {entry_count:,} статей · {esc(src.get('format', 'jsonl'))}</p>
  <p class="card-desc">{esc(src['description'])}</p>
  <p class="card-source"><span class="muted">источник:</span> {esc(src.get('based_on', ''))}</p>
  <div class="card-actions">
    <a class="btn btn-primary" href="{esc(src['site_path'])}">читать</a>
    <a class="btn btn-ghost" href="{esc(src['data_path'])}" download>скачать {esc(src['format'])}</a>
  </div>
</article>""")

    sources_block = "\n".join(items)

    return f"""{page_head(catalog['title'], catalog['description'])}
<header class="hero">
  <div class="hero-inner">
    <p class="hero-tag">sources.avar.me</p>
    <h1>исходники<span class="dot">.</span></h1>
    <p class="hero-lead">{esc(catalog['description'])}</p>
  </div>
</header>

<main class="container">
  <section class="intro">
    <p>Здесь живут <strong>исходные данные</strong> для всех проектов avar.me. Читайте,
    проверяйте, замечайте неточности — и пишите в канал
    <a href="{TELEGRAM}">@avarlangme</a>. Поправим, и обновлённые исходники
    автоматически разойдутся по другим сайтам экосистемы.</p>
  </section>

  <section class="catalog">
    <h2 class="section-title">Источники</h2>
    <div class="catalog-grid">{sources_block}</div>
  </section>

  <section class="how-it-works">
    <h2 class="section-title">Как работает</h2>
    <ol class="flow">
      <li><strong>Читатели</strong> листают словарь и замечают ошибку.</li>
      <li><strong>Пишут в канал</strong> <a href="{TELEGRAM}">@avarlangme</a>: «слово такое-то — там опечатка / неверный перевод».</li>
      <li><strong>Админ правит</strong> строку в <code>data/&lt;source&gt;.jsonl</code> и пушит в репозиторий.</li>
      <li><strong>Сайт пересобирается</strong> автоматически (GitHub Actions).</li>
      <li><strong>Зависимые проекты</strong> (avar.me, forms, corrector …) подтянут обновлённый jsonl при своей следующей сборке.</li>
    </ol>
  </section>

  <section class="downloads">
    <h2 class="section-title">Прямые ссылки на исходники</h2>
    <ul class="downloads-list">
      <li><a href="sources.json"><code>sources.json</code></a> — реестр всех источников</li>
      {''.join(f'<li><a href="{esc(s["data_path"])}"><code>{esc(s["data_path"])}</code></a> — {esc(s["title"])}</li>' for s in catalog['sources'])}
    </ul>
  </section>
</main>

{footer_html()}
"""


def render_dictionary_index(src: dict, letters: list[tuple[str, int]], letter_pages: dict[str, list[str]]) -> str:
    title = f"{src['title']} — sources.avar.me"
    nav_items = "".join(
        f'<a class="alpha-cell" href="{esc(letter_pages[letter][0])}"><span class="alpha-char">{esc(letter)}</span>'
        f'<span class="alpha-count">{count:,}</span></a>'
        for letter, count in letters
    )
    total = sum(c for _, c in letters)

    return f"""{page_head(title, src['description'], asset_prefix='../')}
<header class="hero hero-dict">
  <div class="hero-inner">
    <p class="hero-tag"><a href="../">sources.avar.me</a> / {esc(src['id'])}</p>
    <h1>{esc(src['title'])}</h1>
    <p class="hero-lead">{esc(src['subtitle'])} · {total:,} статей</p>
    <p class="hero-source">{esc(src.get('based_on', ''))}</p>
    <div class="hero-actions">
      <a class="btn btn-ghost" href="../{esc(src['data_path'])}" download>скачать {esc(src['format'])}</a>
    </div>
  </div>
</header>

<main class="container">
  <section class="dict-intro">
    <p>Перейдите к нужной букве. Внутри страницы — все статьи на эту букву в алфавитном порядке.
    Заметили опечатку? Под каждой статьёй есть ссылка «сообщить о неточности» — пишет в
    <a href="{TELEGRAM}">@avarlangme</a> с готовой темой.</p>
  </section>

  <section>
    <h2 class="section-title">Алфавит</h2>
    <nav class="alphabet">{nav_items}</nav>
  </section>
</main>

{footer_html(asset_prefix='../')}
"""


def render_letter_page(
    src: dict,
    letter: str,
    page_index: int,
    page_count: int,
    page_entries: list[dict],
    letter_total: int,
    letters: list[tuple[str, int]],
    letter_pages: dict[str, list[str]],
    word_to_page: dict[str, str],
    prev_page: str | None,
    next_page: str | None,
    page_file: str,
) -> str:
    page_suffix = f" — стр. {page_index + 1}/{page_count}" if page_count > 1 else ""
    title = f"{letter.upper()}{page_suffix} — {src['title']} — sources.avar.me"
    description = f"Статьи на букву «{letter}» в словаре {src['title']}"

    seen_anchors: dict[str, int] = defaultdict(int)
    entries_html_parts = []
    toc_parts = []
    for entry in page_entries:
        anchor = anchor_for(entry.get("word", ""), seen_anchors)
        entries_html_parts.append(
            render_entry(entry, anchor, word_to_page, src['id'], page_file)
        )
        toc_parts.append(
            f'<li><a href="#word-{url_quote(anchor)}">{esc(entry.get("word", ""))}</a></li>'
        )
    entries_html = "\n".join(entries_html_parts)
    toc_html = "".join(toc_parts)

    alphabet_nav = "".join(
        f'<a class="alpha-mini{" current" if l == letter else ""}" href="{esc(letter_pages[l][0])}">{esc(l)}</a>'
        for l, _ in letters
    )

    page_pagination = ""
    if page_count > 1:
        page_links = "".join(
            f'<a class="page-num{" current" if i == page_index else ""}" '
            f'href="{esc(letter_pages[letter][i])}">{i + 1}</a>'
            for i in range(page_count)
        )
        page_pagination = (
            f'<nav class="letter-paging" aria-label="Страницы буквы «{esc(letter)}»">'
            f'<span class="paging-label">страницы:</span>{page_links}</nav>'
        )

    prev_link = (
        f'<a class="page-nav prev" href="{esc(prev_page)}">← назад</a>'
        if prev_page else '<span class="page-nav-stub"></span>'
    )
    next_link = (
        f'<a class="page-nav next" href="{esc(next_page)}">вперёд →</a>'
        if next_page else '<span class="page-nav-stub"></span>'
    )

    return f"""{page_head(title, description, asset_prefix='../')}
<header class="letter-header">
  <div class="letter-header-inner">
    <p class="letter-tag"><a href="../">sources.avar.me</a> / <a href="./">{esc(src['id'])}</a></p>
    <h1 class="letter-h1">{esc(letter.upper())}{esc(page_suffix)}</h1>
    <p class="letter-count">{letter_total:,} статей на этой букве{(' · ' + str(len(page_entries)) + ' на странице') if page_count > 1 else ''}</p>
    <nav class="alphabet-mini">{alphabet_nav}</nav>
    {page_pagination}
  </div>
</header>

<main class="container">
  <details class="toc" {"" if page_count > 1 else "open"}>
    <summary>Оглавление ({len(page_entries):,})</summary>
    <ul class="toc-list">{toc_html}</ul>
  </details>

  <div class="entries">
    {entries_html}
  </div>

  <nav class="page-nav-bar">
    {prev_link}
    <a class="page-nav up" href="./">к оглавлению</a>
    {next_link}
  </nav>
</main>

{footer_html(asset_prefix='../')}
"""


# ---------- Build ----------

def build():
    print("=== sources.avar.me build ===")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    # Reset docs/
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)

    # Copy shared assets
    for asset in ("styles.css", "app.js"):
        src = TEMPLATES / asset
        if src.exists():
            shutil.copy2(src, DOCS / asset)

    # Copy catalog + raw data
    shutil.copy2(CATALOG, DOCS / "sources.json")
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    for src in catalog["sources"]:
        data_file = ROOT / src["data_path"]
        target = DOCS / src["data_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(data_file, target)

    # Per-dictionary build
    stats: dict[str, dict] = {}
    for src in catalog["sources"]:
        sid = src["id"]
        print(f"--- {sid} ({src['title']}) ---")
        entries = load_jsonl(ROOT / src["data_path"])
        print(f"    loaded {len(entries):,} entries")
        grouped = group_by_letter(entries)
        letters_sorted = sorted(grouped.keys(), key=sort_key)
        letter_counts = [(l, len(grouped[l])) for l in letters_sorted]

        # Split each letter's entries into pages of PAGE_SIZE. Compute file names.
        # letter_pages[letter] = ["а.html", "а-2.html", ...]
        letter_pages: dict[str, list[str]] = {}
        letter_chunks: dict[str, list[list[dict]]] = {}
        for letter in letters_sorted:
            ents = grouped[letter]
            chunks = [ents[i:i + PAGE_SIZE] for i in range(0, len(ents), PAGE_SIZE)] or [[]]
            letter_chunks[letter] = chunks
            files = []
            for idx in range(len(chunks)):
                files.append(f"{letter}.html" if idx == 0 else f"{letter}-{idx + 1}.html")
            letter_pages[letter] = files

        # word → page-file map for see_also linking
        word_to_page: dict[str, str] = {}
        for letter in letters_sorted:
            for idx, chunk in enumerate(letter_chunks[letter]):
                page_file = letter_pages[letter][idx]
                for entry in chunk:
                    word_to_page.setdefault(entry.get("word", ""), page_file)

        # Linear list of (letter, idx, page_file) — for prev/next navigation
        linear_pages: list[tuple[str, int, str]] = []
        for letter in letters_sorted:
            for idx, _ in enumerate(letter_chunks[letter]):
                linear_pages.append((letter, idx, letter_pages[letter][idx]))

        # Directory
        dict_dir = DOCS / sid
        dict_dir.mkdir(parents=True, exist_ok=True)

        # Index page
        (dict_dir / "index.html").write_text(
            render_dictionary_index(src, letter_counts, letter_pages),
            encoding="utf-8",
        )

        # Letter pages
        pages_written = 0
        for global_idx, (letter, idx, page_file) in enumerate(linear_pages):
            chunks = letter_chunks[letter]
            page_count = len(chunks)
            page_entries = chunks[idx]
            prev_page = linear_pages[global_idx - 1][2] if global_idx > 0 else None
            next_page = linear_pages[global_idx + 1][2] if global_idx < len(linear_pages) - 1 else None

            html_text = render_letter_page(
                src,
                letter,
                idx,
                page_count,
                page_entries,
                len(grouped[letter]),
                letter_counts,
                letter_pages,
                word_to_page,
                prev_page,
                next_page,
                page_file,
            )
            (dict_dir / page_file).write_text(html_text, encoding="utf-8")
            pages_written += 1
        print(f"    wrote {pages_written} pages across {len(letters_sorted)} letters")

        stats[sid] = {
            "entry_count": len(entries),
            "letter_count": len(letters_sorted),
            "page_count": pages_written,
        }

    # Catalog landing page
    (DOCS / "index.html").write_text(render_catalog(catalog, stats), encoding="utf-8")

    # Stats meta
    (DOCS / "build.json").write_text(
        json.dumps(
            {
                "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "stats": stats,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"=== done: docs/ ready ({sum(s['entry_count'] for s in stats.values()):,} entries) ===")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        raise
