#!/usr/bin/env python3
"""Builder for sources.avar.me.

Reads `sources.json` + `data/*.jsonl` (+ `books/*.pdf`) and emits a static
site into `docs/`.

Site layout:

    docs/index.html                  — catalog landing
    docs/sources.json                — copy of root catalog
    docs/styles.css, app.js          — shared assets
    docs/data/<id>.jsonl             — raw downloadable sources
    docs/books/*.pdf                 — original scanned sources
    docs/<id>/index.html             — dictionary landing (alphabet + per-letter
                                       TOC of 3-letter prefixes)
    docs/<id>/<prefix>.html          — entries for a 3-letter prefix bucket
                                       (digraphs like тӏ/лъ/гь count as one
                                       letter; large buckets paginate
                                       <prefix>-2.html, <prefix>-3.html …)

Reporting flow: each entry has a "сообщить о неточности" link that opens
@avarme_chat with a pre-filled message including a stable URL.

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
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CATALOG = ROOT / "sources.json"
TEMPLATES = ROOT / "src" / "templates"

TELEGRAM_CHAT = "https://t.me/avarme_chat"
TELEGRAM_CHANNEL = "https://t.me/avarlangme"
GITHUB_REPO = "https://github.com/avar-me/sources"

# Hard cap per HTML page. A 3-letter prefix bucket bigger than this is split
# into <prefix>.html, <prefix>-2.html, …
PAGE_SIZE = 500

REPORT_TEMPLATE = (
    "Здравствуйте! Заметил неточность в словаре {dict_id}:\n"
    "слово: {word}\n"
    "ссылка: https://sources.avar.me/{dict_id}/{page_file}#word-{anchor}\n\n"
    "Должно быть: ..."
)


# ---------- Alphabet ----------

AVAR_DIGRAPHS = ("гъ", "гь", "гӏ", "къ", "кь", "кӏ", "лъ", "тӏ", "хъ", "хь", "хӏ", "цӏ", "чӏ")

AVAR_ALPHABET = [
    "а", "б", "в", "г", "гъ", "гь", "гӏ", "д", "е", "ё", "ж", "з",
    "и", "й", "к", "къ", "кь", "кӏ", "л", "лъ", "м", "н", "о", "п",
    "р", "с", "т", "тӏ", "у", "ф", "х", "хъ", "хь", "хӏ", "ц", "цӏ",
    "ч", "чӏ", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я",
]

RUSSIAN_ALPHABET = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


def normalize_palochka(text: str) -> str:
    """Map various palochka glyphs to the canonical Cyrillic palochka U+04CF / U+04C0.

    Source data sometimes contains Latin I / lower l / | / ӏ — unify so digraph
    detection works.
    """
    out = []
    for ch in text:
        if ch in "IiӀ|ǀl":
            out.append("ӏ")
        else:
            out.append(ch)
    return "".join(out)


def make_alphabet(language: str) -> list[str]:
    if language == "av":
        return AVAR_ALPHABET
    return RUSSIAN_ALPHABET


def make_tokenizer(language: str):
    """Return a function that splits a word into ordered letter units."""
    if language == "av":
        digraphs = set(AVAR_DIGRAPHS)

        def tokenize(word: str) -> list[str]:
            word = normalize_palochka((word or "").lower())
            tokens: list[str] = []
            i, n = 0, len(word)
            while i < n:
                if i + 1 < n and word[i : i + 2] in digraphs:
                    tokens.append(word[i : i + 2])
                    i += 2
                else:
                    tokens.append(word[i])
                    i += 1
            return tokens

        return tokenize

    def tokenize(word: str) -> list[str]:
        return list((word or "").lower())

    return tokenize


def make_rank(alphabet: list[str]) -> dict[str, int]:
    return {letter: i for i, letter in enumerate(alphabet)}


def make_sort_key(rank: dict[str, int], tokenize):
    """Stable sort key. Unknown letters go to the end of the book."""

    def token_rank(tok: str) -> int:
        if tok in rank:
            return rank[tok]
        return 10_000 + sum(ord(c) for c in tok)

    def key(word: str):
        tokens = tokenize(word)
        return (tuple(token_rank(t) for t in tokens), word)

    return key


# ---------- Helpers ----------

def esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def url_quote(text: str) -> str:
    return quote(text, safe="")


def anchor_for(word: str, seen: dict[str, int]) -> str:
    base = word.replace(" ", "_").replace("/", "_") or "_"
    seen[base] += 1
    return base if seen[base] == 1 else f"{base}-{seen[base]}"


def load_jsonl(path: Path) -> list[dict]:
    entries: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


# ---------- HTML rendering ----------

def render_entry(entry: dict, anchor: str, dict_id: str, page_file: str) -> str:
    """Render an entry as its raw JSON (pretty-printed) under the word heading.

    The site is meant for spotting errors in the source data — showing the
    original JSON is more honest than any interpreted layout.
    """
    word = entry.get("word", "")
    json_text = json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=False)

    report_text = REPORT_TEMPLATE.format(
        dict_id=dict_id,
        word=word,
        page_file=page_file,
        anchor=anchor,
    )
    report_href = f"{TELEGRAM_CHAT}?text={url_quote(report_text)}"

    return (
        f'<article class="entry" id="word-{esc(anchor)}">'
        f'<header class="entry-head">'
        f'<h2 class="entry-word">{esc(word)}</h2>'
        f'<a class="report-link" href="{report_href}" target="_blank" rel="noopener" '
        f'title="Сообщить об ошибке в @avarme_chat">сообщить о неточности</a>'
        f'</header>'
        f'<pre class="entry-json"><code>{esc(json_text)}</code></pre>'
        f'</article>'
    )


# ---------- Page chrome ----------

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
<script defer src="{asset_prefix}app.js"></script>
</head>
<body>
<div class="bg-pattern" aria-hidden="true"></div>
"""


def footer_html() -> str:
    return (
        '<footer class="site-footer">'
        f'<p>Сообщайте о неточностях в чат '
        f'<a href="{TELEGRAM_CHAT}">@avarme_chat</a> · '
        f'новости в канале <a href="{TELEGRAM_CHANNEL}">@avarlangme</a></p>'
        f'<p>Проект <a href="https://avar.me">avar.me</a> · '
        f'<a href="{GITHUB_REPO}">github.com/avar-me/sources</a></p>'
        '</footer></body></html>'
    )


# ---------- Catalog (root index.html) ----------

def render_catalog(catalog: dict, stats: dict[str, dict]) -> str:
    items = []
    for src in catalog["sources"]:
        sid = src["id"]
        s = stats.get(sid, {})
        entry_count = s.get("entry_count", 0)
        documents_links = ""
        if src.get("documents"):
            doc_links_html = " · ".join(
                f'<a href="{esc(doc["path"])}" target="_blank" rel="noopener">{esc(doc.get("kind", "файл").upper())}</a>'
                for doc in src["documents"]
            )
            documents_links = f'<p class="card-docs"><span class="muted">оригинал:</span> {doc_links_html}</p>'

        items.append(f"""
<article class="catalog-card">
  <header class="card-top">
    <h2><a href="{esc(src['site_path'])}">{esc(src['title'])}</a></h2>
    <span class="badge badge-{esc(src.get('status', 'stable'))}">{esc(src.get('status', 'stable'))}</span>
  </header>
  <p class="card-sub">{esc(src.get('subtitle', ''))} · {entry_count:,} статей · {esc(src.get('format', 'jsonl'))}</p>
  <p class="card-desc">{esc(src['description'])}</p>
  <p class="card-source"><span class="muted">источник:</span> {esc(src.get('based_on', ''))}</p>
  {documents_links}
  <div class="card-actions">
    <a class="btn btn-primary" href="{esc(src['site_path'])}">читать</a>
    <a class="btn btn-ghost" href="{esc(src['data_path'])}" download>скачать {esc(src['format'])}</a>
  </div>
</article>""")

    sources_block = "\n".join(items)

    all_downloads = []
    all_downloads.append('<li><a href="sources.json"><code>sources.json</code></a> — реестр всех источников</li>')
    for src in catalog["sources"]:
        all_downloads.append(
            f'<li><a href="{esc(src["data_path"])}"><code>{esc(src["data_path"])}</code></a> — {esc(src["title"])}</li>'
        )
        for doc in src.get("documents", []):
            all_downloads.append(
                f'<li><a href="{esc(doc["path"])}" target="_blank" rel="noopener"><code>{esc(doc["path"])}</code></a> — '
                f'{esc(doc.get("title", "PDF"))}</li>'
            )

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
    проверяйте, замечайте неточности — и пишите в чат
    <a href="{TELEGRAM_CHAT}">@avarme_chat</a>. Поправим, и обновлённые исходники
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
      <li><strong>Пишут в чат</strong> <a href="{TELEGRAM_CHAT}">@avarme_chat</a>: «слово такое-то — там опечатка / неверный перевод».</li>
      <li><strong>Админ правит</strong> строку в <code>data/&lt;source&gt;.jsonl</code> и пушит в репозиторий.</li>
      <li><strong>Сайт пересобирается</strong> автоматически (GitHub Actions).</li>
      <li><strong>Зависимые проекты</strong> (avar.me, forms, corrector …) подтянут обновлённый jsonl при своей следующей сборке.</li>
    </ol>
  </section>

  <section class="downloads">
    <h2 class="section-title">Прямые ссылки</h2>
    <ul class="downloads-list">
      {''.join(all_downloads)}
    </ul>
  </section>
</main>

{footer_html()}
"""


# ---------- Dictionary index ----------

def render_dictionary_index(
    src: dict,
    alphabet: list[str],
    letter_counts: dict[str, int],
    letter_prefixes: dict[str, list[tuple[str, int, str]]],
    total: int,
) -> str:
    title = f"{src['title']} — sources.avar.me"

    # Alphabet grid (top, sticky-ish via app.js scroll-spy if needed)
    nav_cells = []
    for letter in alphabet:
        count = letter_counts.get(letter, 0)
        if count == 0:
            nav_cells.append(
                f'<span class="alpha-cell empty"><span class="alpha-char">{esc(letter)}</span></span>'
            )
        else:
            nav_cells.append(
                f'<a class="alpha-cell" href="#letter-{url_quote(letter)}">'
                f'<span class="alpha-char">{esc(letter)}</span>'
                f'<span class="alpha-count">{count:,}</span></a>'
            )

    # Per-letter sections with 3-letter-prefix sub-buckets. Each letter is a
    # collapsible <details> so the index doesn't dump thousands of prefixes
    # on screen at once.
    sections = []
    for letter in alphabet:
        if not letter_counts.get(letter):
            continue
        prefixes = letter_prefixes.get(letter, [])
        prefix_links = "".join(
            f'<a class="prefix-cell" href="{esc(file)}">'
            f'<span class="prefix-text">{esc(prefix)}</span>'
            f'<span class="prefix-count">{count:,}</span></a>'
            for prefix, count, file in prefixes
        )
        count = letter_counts.get(letter, 0)
        sections.append(
            f'<details class="letter-section" id="letter-{url_quote(letter)}">'
            f'<summary class="letter-section-h">'
            f'<span class="letter-section-name">{esc(letter)}</span>'
            f'<span class="letter-section-count">{count:,}</span>'
            f'</summary>'
            f'<div class="prefix-grid">{prefix_links}</div>'
            f'</details>'
        )

    documents_links = ""
    if src.get("documents"):
        for doc in src["documents"]:
            documents_links += (
                f'<a class="btn btn-ghost" href="../{esc(doc["path"])}" target="_blank" rel="noopener">'
                f'скачать оригинал ({esc(doc.get("kind", "PDF").upper())})</a>'
            )

    return f"""{page_head(title, src['description'], asset_prefix='../')}
<header class="hero hero-dict">
  <div class="hero-inner">
    <p class="hero-tag"><a href="../">sources.avar.me</a> / {esc(src['id'])}</p>
    <h1>{esc(src['title'])}</h1>
    <p class="hero-lead">{esc(src['subtitle'])} · {total:,} статей</p>
    <p class="hero-source">{esc(src.get('based_on', ''))}</p>
    <div class="hero-actions">
      <a class="btn btn-ghost" href="../{esc(src['data_path'])}" download>скачать {esc(src['format'])}</a>
      {documents_links}
    </div>
  </div>
</header>

<main class="container">
  <section class="dict-intro">
    <p>Перейдите к нужной букве в алфавите, затем — к 3-буквенному фрагменту слов.
    Заметили опечатку или неверный перевод? Под каждой статьёй ссылка
    «сообщить о неточности» открывает <a href="{TELEGRAM_CHAT}">@avarme_chat</a>
    с готовым сообщением.</p>
  </section>

  <section>
    <h2 class="section-title">Алфавит</h2>
    <nav class="alphabet">{''.join(nav_cells)}</nav>
  </section>

  <section>
    <h2 class="section-title">Указатель по 3-буквенным фрагментам</h2>
    <div class="letter-toc">{''.join(sections)}</div>
  </section>
</main>

{footer_html()}
"""


# ---------- Prefix page (entries) ----------

def render_prefix_page(
    src: dict,
    prefix: str,
    letter: str,
    page_index: int,
    page_count: int,
    page_entries: list[dict],
    bucket_total: int,
    alphabet: list[str],
    letter_counts: dict[str, int],
    sibling_prefixes_in_letter: list[tuple[str, int, str]],
    prev_page: str | None,
    next_page: str | None,
    page_file: str,
) -> str:
    page_suffix = f" · стр. {page_index + 1}/{page_count}" if page_count > 1 else ""
    title = f"{prefix}{page_suffix} — {src['title']} — sources.avar.me"
    description = f'Статьи на «{prefix}» в словаре {src["title"]}'

    seen_anchors: dict[str, int] = defaultdict(int)
    entries_html_parts: list[str] = []
    toc_parts: list[str] = []
    for entry in page_entries:
        anchor = anchor_for(entry.get("word", ""), seen_anchors)
        entries_html_parts.append(
            render_entry(entry, anchor, src["id"], page_file)
        )
        toc_parts.append(
            f'<li><a href="#word-{url_quote(anchor)}">{esc(entry.get("word", ""))}</a></li>'
        )
    entries_html = "\n".join(entries_html_parts)
    toc_html = "".join(toc_parts)

    alphabet_nav = "".join(
        (
            f'<a class="alpha-mini{" current" if l == letter else ""}" '
            f'href="index.html#letter-{url_quote(l)}">{esc(l)}</a>'
        )
        if letter_counts.get(l)
        else f'<span class="alpha-mini empty">{esc(l)}</span>'
        for l in alphabet
    )

    sibling_nav = "".join(
        (
            f'<a class="prefix-mini{" current" if p == prefix else ""}" '
            f'href="{esc(file)}">{esc(p)}</a>'
        )
        for p, _, file in sibling_prefixes_in_letter
    )

    page_pagination = ""
    if page_count > 1:
        page_links = "".join(
            f'<a class="page-num{" current" if i == page_index else ""}" '
            f'href="{esc(prefix)}{("" if i == 0 else f"-{i + 1}")}.html">{i + 1}</a>'
            for i in range(page_count)
        )
        page_pagination = (
            f'<nav class="letter-paging" aria-label="Страницы фрагмента «{esc(prefix)}»">'
            f'<span class="paging-label">страницы:</span>{page_links}</nav>'
        )

    prev_link_compact = (
        f'<a class="page-nav-arrow" href="{esc(prev_page)}" title="Предыдущий фрагмент" aria-label="назад">←</a>'
        if prev_page else '<span class="page-nav-arrow stub" aria-hidden="true">←</span>'
    )
    next_link_compact = (
        f'<a class="page-nav-arrow" href="{esc(next_page)}" title="Следующий фрагмент" aria-label="вперёд">→</a>'
        if next_page else '<span class="page-nav-arrow stub" aria-hidden="true">→</span>'
    )

    prev_link_bottom = (
        f'<a class="page-nav prev" href="{esc(prev_page)}">← назад</a>'
        if prev_page else '<span class="page-nav-stub"></span>'
    )
    next_link_bottom = (
        f'<a class="page-nav next" href="{esc(next_page)}">вперёд →</a>'
        if next_page else '<span class="page-nav-stub"></span>'
    )

    return f"""{page_head(title, description, asset_prefix='../')}
<header class="letter-header">
  <div class="letter-header-inner">
    <div class="letter-bar">
      {prev_link_compact}
      <div class="letter-bar-title">
        <p class="letter-tag"><a href="../">sources.avar.me</a> / <a href="index.html">{esc(src['id'])}</a></p>
        <h1 class="letter-h1">{esc(prefix)}<span class="letter-h1-suffix">{esc(page_suffix)}</span></h1>
        <p class="letter-count">{bucket_total:,} статей{(' · ' + str(len(page_entries)) + ' на странице') if page_count > 1 else ''}</p>
      </div>
      {next_link_compact}
    </div>
    {page_pagination}
    <details class="nav-details">
      <summary>Навигация по словарю</summary>
      <div class="nav-details-body">
        <div class="nav-group">
          <p class="nav-group-h">Алфавит</p>
          <nav class="alphabet-mini" aria-label="Алфавит">{alphabet_nav}</nav>
        </div>
        <div class="nav-group">
          <p class="nav-group-h">Фрагменты буквы «{esc(letter)}»</p>
          <nav class="prefix-bar" aria-label="Фрагменты внутри «{esc(letter)}»">{sibling_nav}</nav>
        </div>
        <p class="nav-group-h"><a href="index.html#letter-{url_quote(letter)}">→ к указателю</a></p>
      </div>
    </details>
  </div>
</header>

<main class="container">
  <details class="toc">
    <summary>Оглавление страницы ({len(page_entries):,})</summary>
    <ul class="toc-list">{toc_html}</ul>
  </details>

  <div class="entries">
    {entries_html}
  </div>

  <nav class="page-nav-bar">
    {prev_link_bottom}
    <a class="page-nav up" href="index.html#letter-{url_quote(letter)}">к указателю</a>
    {next_link_bottom}
  </nav>
</main>

{footer_html()}
"""


# ---------- Build ----------

def build_dictionary(src: dict) -> dict:
    sid = src["id"]
    language = src.get("language_from", "ru")
    tokenize = make_tokenizer(language)
    alphabet = make_alphabet(language)
    rank = make_rank(alphabet)
    sort_key = make_sort_key(rank, tokenize)

    entries = load_jsonl(ROOT / src["data_path"])
    print(f"    loaded {len(entries):,} entries")

    # First letter (token) per entry; "?" if word is empty
    def letter_of(word: str) -> str:
        toks = tokenize(word)
        return toks[0] if toks else "?"

    def prefix_of(word: str) -> str:
        toks = tokenize(word)
        if not toks:
            return "?"
        return "".join(toks[: min(3, len(toks))])

    # Bucket by 3-letter prefix
    prefix_buckets: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        word = entry.get("word", "")
        prefix_buckets[prefix_of(word)].append(entry)

    # Sort entries inside each bucket
    for prefix in prefix_buckets:
        prefix_buckets[prefix].sort(key=lambda e: sort_key(e.get("word", "")))

    # Group prefixes by their letter
    letter_to_prefixes: dict[str, list[str]] = defaultdict(list)
    for prefix in prefix_buckets:
        toks = tokenize(prefix)
        letter = toks[0] if toks else "?"
        letter_to_prefixes[letter].append(prefix)

    # Sort prefixes inside each letter using same sort key
    for letter in letter_to_prefixes:
        letter_to_prefixes[letter].sort(key=sort_key)

    # Letter counts
    letter_counts: dict[str, int] = {
        letter: sum(len(prefix_buckets[p]) for p in prefs)
        for letter, prefs in letter_to_prefixes.items()
    }

    # Letter order: alphabet first, then any unknown leftovers sorted by their sort key
    known = [l for l in alphabet if l in letter_to_prefixes]
    extras = sorted(
        [l for l in letter_to_prefixes if l not in alphabet],
        key=lambda x: (10_000, x),
    )
    letters_in_order = known + extras

    # Compute page files per prefix bucket (split big ones)
    prefix_pages: dict[str, list[tuple[str, list[dict]]]] = {}
    for prefix, ents in prefix_buckets.items():
        chunks = [ents[i : i + PAGE_SIZE] for i in range(0, len(ents), PAGE_SIZE)] or [[]]
        pages: list[tuple[str, list[dict]]] = []
        for idx, chunk in enumerate(chunks):
            file_name = f"{prefix}.html" if idx == 0 else f"{prefix}-{idx + 1}.html"
            pages.append((file_name, chunk))
        prefix_pages[prefix] = pages

    # Linear page order for prev/next nav
    linear_pages: list[tuple[str, str, int, int, list[dict], int]] = []
    for letter in letters_in_order:
        for prefix in letter_to_prefixes[letter]:
            pages = prefix_pages[prefix]
            for idx, (file_name, chunk) in enumerate(pages):
                linear_pages.append(
                    (letter, prefix, idx, len(pages), chunk, len(prefix_buckets[prefix]))
                )

    # ---- write ----
    dict_dir = DOCS / sid
    dict_dir.mkdir(parents=True, exist_ok=True)

    # Letter → prefix tuples for the dict index
    letter_prefixes_for_index: dict[str, list[tuple[str, int, str]]] = {}
    for letter in letters_in_order:
        items: list[tuple[str, int, str]] = []
        for prefix in letter_to_prefixes[letter]:
            file_name = prefix_pages[prefix][0][0]
            items.append((prefix, len(prefix_buckets[prefix]), file_name))
        letter_prefixes_for_index[letter] = items

    (dict_dir / "index.html").write_text(
        render_dictionary_index(
            src,
            letters_in_order,
            letter_counts,
            letter_prefixes_for_index,
            len(entries),
        ),
        encoding="utf-8",
    )

    pages_written = 0
    for global_idx, (letter, prefix, page_idx, page_count, chunk, bucket_total) in enumerate(
        linear_pages
    ):
        file_name = prefix_pages[prefix][page_idx][0]
        prev_page = linear_pages[global_idx - 1][1]  # prefix only for label, need file
        if global_idx > 0:
            prev_l, prev_p, prev_i, prev_pc, _, _ = linear_pages[global_idx - 1]
            prev_file = prefix_pages[prev_p][prev_i][0]
        else:
            prev_file = None
        if global_idx < len(linear_pages) - 1:
            next_l, next_p, next_i, next_pc, _, _ = linear_pages[global_idx + 1]
            next_file = prefix_pages[next_p][next_i][0]
        else:
            next_file = None

        html_text = render_prefix_page(
            src,
            prefix,
            letter,
            page_idx,
            page_count,
            chunk,
            bucket_total,
            letters_in_order,
            letter_counts,
            letter_prefixes_for_index[letter],
            prev_file,
            next_file,
            file_name,
        )
        (dict_dir / file_name).write_text(html_text, encoding="utf-8")
        pages_written += 1

    print(
        f"    wrote {pages_written:,} pages across "
        f"{sum(len(p) for p in letter_to_prefixes.values()):,} 3-letter buckets "
        f"in {len(letters_in_order)} letters"
    )

    return {
        "entry_count": len(entries),
        "letter_count": len(letters_in_order),
        "bucket_count": sum(len(p) for p in letter_to_prefixes.values()),
        "page_count": pages_written,
    }


def build() -> None:
    print("=== sources.avar.me build ===")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)

    # Shared assets
    for asset in ("styles.css", "app.js"):
        src_path = TEMPLATES / asset
        if src_path.exists():
            shutil.copy2(src_path, DOCS / asset)

    # Catalog
    shutil.copy2(CATALOG, DOCS / "sources.json")

    # Raw data + original documents (PDFs)
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    seen_doc_paths: set[str] = set()
    for src in catalog["sources"]:
        data_file = ROOT / src["data_path"]
        target = DOCS / src["data_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(data_file, target)
        for doc in src.get("documents", []):
            doc_rel = doc["path"]
            if doc_rel in seen_doc_paths:
                continue
            seen_doc_paths.add(doc_rel)
            src_doc = ROOT / doc_rel
            dst_doc = DOCS / doc_rel
            if not src_doc.exists():
                print(f"    !! missing document: {doc_rel}", file=sys.stderr)
                continue
            dst_doc.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_doc, dst_doc)

    # Dictionaries
    stats: dict[str, dict] = {}
    for src in catalog["sources"]:
        print(f"--- {src['id']} ({src['title']}) ---")
        stats[src["id"]] = build_dictionary(src)

    # Catalog landing page
    (DOCS / "index.html").write_text(render_catalog(catalog, stats), encoding="utf-8")

    # Build meta
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

    total = sum(s["entry_count"] for s in stats.values())
    pages = sum(s["page_count"] for s in stats.values())
    print(f"=== done: {total:,} entries → {pages:,} pages ===")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        raise
