# av-ru.1967 parsing scripts

Tools for turning `books/saidov_m_avarskorusskii_slovar.pdf` into
`data/av-ru.1967.jsonl`. See `../../av-ru-1967-parsing-handoff.md` for the
full plan; this directory only holds the code.

## Environment

```bash
python3 -m venv .venv-av-ru-1967   # from repo root; gitignored
source .venv-av-ru-1967/bin/activate
pip install pdfplumber
```

## extract_geometry.py

Step 1 of the handoff plan: dump per-page word geometry (column, bbox, font,
bold/italic) without attempting article segmentation.

```bash
python3 scripts/av-ru-1967/extract_geometry.py --start 23 --end 25
```

Writes one JSON file per physical PDF page to `tmp/av-ru.1967/geometry/`
(gitignored). Physical page numbers match `pdf.pages[n-1]` — verified against
the handoff doc's page-range table (e.g. page 620 starts the geographic
names list, page 705 starts the grammar essay).
