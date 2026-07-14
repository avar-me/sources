# Protocol: compiling the expert-review rejected file

**Audience:** the agent (or human) that drafts / appends
`expert-review-av-ru-issues-*-rejected.md` after maintainers review open RFIs.

**Consumer:** `python tools/expert_review.py prepare|apply` — the file is
**machine-parsed**. Free-form prose that a human can read is not enough.

**Status of this document:** normative, evergreen — read it **before**
writing or appending to `expert-review-av-ru-issues-*-rejected.md` in every
RFI round, not just once. Referenced from `CLAUDE.md` §«RFI». Round 7
(2026-07-13) violated it (see §8 for the concrete mistakes); do not repeat
them. Prefer the canonical block in §2 over any “convenience” grouping.

---

## 1. Purpose of the file

Maintainers reject some `llm-flagged-source-issue` RFIs as **false positives**
(Russian source is fine). This file records those rejections so the
multilang pipeline can:

1. mark matching RFIs `ignored` with `maintainer_response`;
2. have a competent reader (Claude, **not** gemma) check whether the
   **English translation** of the same passage is also wrong.

The file does **not** itself fix translations. `apply` only uses decisions
JSON for that. Your job is a **parseable rejection list**.

---

## 2. Canonical item shape (REQUIRED)

One rejected RFI = **exactly one** markdown block in this form:

```markdown
## #NNN — <exact word from RFI>

- поле: `<exact field path from RFI>`
- текст: «<Russian text; may be a short quote of a longer field>»
- почему отклонено: <one paragraph, why the Russian source is fine>
```

### Hard rules

| Rule | Detail |
|---|---|
| Heading | Must match `## #digits — word` (em dash `—`, spaces as shown). |
| `word` | **Exactly** `RFI.word` from `reports/request-for-improvement.jsonl`. No appendages. |
| `поле` | **Exactly** `RFI.field` in backticks, alone on its line. |
| `текст` | Alone on its line, in Russian «guillemets». Prefer full `RFI.current`; a short quote is OK if the field is long. |
| `почему отклонено` | Alone on its line (continuation lines without a new `- ` bullet are OK). |
| One RFI per block | Never merge two RFIs into one heading or one `поле` line. |
| Only false positives | If the RFI was **correct** and source was **fixed** upstream, do **not** invent a “отклонено” story — use a separate **fixed** appendix (see §5). |

### Forbidden in the heading

Do **not** put any of this in `## #NNN — …`:

- `(RFI-xxxxxxxxxxxx)`
- `, омоним 2`
- `и <other word>`
- `не ложное срабатывание → исправлено`
- `, частично исправлено`
- free commentary

Wrong:

```markdown
## #048 — бер (RFI-4b7e28b9de30)
## #062 — кьо, омоним 2 (RFI-fa25b2968722)
## #076 — роххногӏоркь и лъен (RFI-c7edf187d8e8, RFI-4272c9c5ff04)
## #054 — ичӏгояв (RFI-19c19a27d822, не ложное срабатывание → исправлено)
```

Right:

```markdown
## #048 — бер

- поле: `senses[0].examples[36].comment`
- текст: «гулгун кумган»
- почему отклонено: аварский ответ на загадку; поле помечено comment_lang=av.
```

Optional **body** line (not in the heading), if useful for humans:

```markdown
- rfi: RFI-4b7e28b9de30
```

`expert_review.py` matches on `(word, field)`, not on the `#NNN` number and
not on the RFI id in the heading. Numbers may collide across rounds; that is
fine.

---

## 3. Round headers (optional)

You may group blocks under:

```markdown
## Раунд N (YYYY-MM-DD) — <human summary>
```

These headers are ignored by the parser. You may also add a short
“повторяющиеся причины” section **after** all items, with **no** fake
`## #NNN` headings and **no** RFI ids listed only in prose.

---

## 4. One RFI → one block (no batching)

If several RFIs share the same reason (e.g. dictionary pattern `"от X"`),
**still emit one full block per RFI**. Duplicate the reason text. Do not write:

```markdown
## Абстрактные существительные …

RFI #091 (рекордсменлъи, RFI-e26173a04281), #092 (…), #093 (…)
Отклонено: …
```

That is **not** a substitute for per-item blocks. Round 7 did this; the
apply agent had to special-case it. **Do not rely on that.**

Same for multi-field notes (“`examples[1].ru` и `examples[2].ru`”): emit
**two** blocks, each with its own exact `поле`.

---

## 5. True positives (source actually wrong → fixed)

If maintainers **agree** the RFI was right and the source was fixed in
`av-ru`, that is **not** a rejection.

Do **not**:

- put it in the rejected list as “почему отклонено”;
- mix “исправлено” stories into false-positive blocks.

Do:

- fix the source upstream;
- mark the RFI `fixed` in the RFI store (workspace / sync workflow);
- optionally add a short note in a **separate** section, e.g.:

```markdown
## Исправлено в источнике (не false positive)

### алъ — RFI-b23174bb76fe

- поле: `senses[0].text`
- было: «эрг от»
- стало: «она, оно»
- примечание: <optional>
```

These “исправлено” notes are **human-only** unless later given an
explicit machine format. They must **not** look like rejection blocks
(`почему отклонено`).

---

## 6. Where values come from

Before writing a block, read the open RFI from:

`reports/request-for-improvement.jsonl`

and copy:

- `word` → heading word  
- `field` → `поле`  
- `current` → `текст` (or a clear quote of it)  
- `id` → optional `- rfi: …` body line  

Do not invent field paths. Do not paraphrase `word`.

---

## 7. Validation checklist (run before handing off)

1. Every rejected open RFI you claim to cover has its own `## #NNN — word` block.
2. Heading word equals `RFI.word` with no decorations.
3. `поле` and `текст` are **separate** lines (not `поле: …, текст «…»` on one line — that form is tolerated as a fallback only; **do not produce it**).
4. Every block has `почему отклонено:`.
5. No batch prose that lists many RFI ids instead of blocks.
6. No “не ложное → исправлено” items mixed into rejection blocks.
7. File is **append-only** for new rounds; do not rewrite older rounds’ item bodies without need.
8. Spot-check:  
   `python tools/expert_review.py prepare expert-review-av-ru-issues-….md --lang en`  
   stderr should show approximately `N item(s) to review` equal to the number of **still-open** RFIs you just documented as rejected — not `WARNING: skipping … missing поле/текст`.

---

## 8. What Round 7 did wrong (do not repeat)

| Mistake | Example |
|---|---|
| RFI id / commentary in heading | `## #048 — бер (RFI-…)` |
| Combined `поле`+`текст` on one line | `- поле: \`…\`, текст «…»` |
| Missing `текст` line | `#050 — дару` had only `поле` |
| Two RFIs / two words in one heading | `#076 — роххногӏоркь и лъен (RFI-…, RFI-…)` |
| Two fields in one bullet | `поле: \`…\` и \`…\`` |
| Batch rejection by prose | “Абстрактные существительные… RFI #091, #092…” |
| True fixes listed as rejections | `#054 ичӏгояв … не ложное → исправлено` |

Rounds 1–6 largely followed §2. Copy that shape.

---

## 9. Minimal correct examples

```markdown
## Раунд 8 (2026-07-14) — N отклонённых

## #001 — плагиатлъи

- поле: `senses[0].text`
- текст: «плагиатство»
- почему отклонено: нормальное слово; менять на «плагиат» не нужно.

## #002 — рекордсменлъи

- поле: `senses[0].text`
- текст: «от рекордсмен»
- почему отклонено: установленный паттерн словаря «от X» + comment «абстр имя», не грамматическая ошибка.

## #003 — шагӏирлъи

- поле: `senses[0].text`
- текст: «от шагӏир»
- почему отклонено: тот же паттерн «от X», что у рекордсменлъи и ~30 других статей.
```

Same reason twice — that is correct.

---

## 10. Downstream (not your job, for orientation)

After this file is appended:

1. Another agent runs `expert_review.py prepare` → worksheet.
2. That agent (Claude) writes `decisions.json` correcting **translations** where needed.
3. `expert_review.py apply … --model claude-sonnet-5` updates `memory/en.jsonl` and RFIs.

You only supply §2-compliant rejection blocks.
