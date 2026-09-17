# Четвёртый батч требований по парсингу словаря Саидова 1967 года

Дата ревью: 2026-09-17  
Проверенная ветка: `av-ru-1967-parsing`  
Проверенный коммит: `3fc324a`  
Отчёт разработчиков: `scripts/av-ru-1967/report.md`  
Предыдущее ревью: `av-ru-1967-review-batch-3-2026-09-17.md`  
Статус: инфраструктурный этап существенно продвинут; следующий этап — исправление данных

## Краткий вывод

Последний апдейт — сильнейший с начала работы над веткой. Появились именно те
архитектурные артефакты, которых раньше не хватало:

- независимый accepted-only checker;
- committed provenance 1:1 с accepted;
- per-page ledger на все 597 страниц;
- persistent decision ledger;
- exact-value baseline sync;
- разделение ссылок по origin/destination;
- HTML review queue;
- bbox и crop generation.

Заявленные цифры отчёта воспроизводятся. Committed JSONL и provenance
совпадают с независимой полной регенерацией byte-for-byte.

Но этот прогресс в основном завершает tooling. Качество данных пока почти не
изменилось:

- accepted: 9 858;
- review: 3 632;
- accepted order regressions: 408;
- suspicious accepted headwords: 27;
- accepted → missing links: 495;
- review → missing links: 399;
- draft order regressions: 900;
- 105 необъяснённых candidate→article drops;
- ни одна из 3 632 review-карточек ещё не разобрана.

Поэтому четвёртый батч должен быть не очередным раундом инфраструктуры, а
первым измеримым **data correction sprint**.

## Что проверено независимо

В чистом snapshot коммита `3fc324a` с pinned Python environment выполнены
geometry reuse, segmentation, parsing, dataset build и все gates.

### Воспроизводимость

```text
data/av-ru.1967.jsonl:             byte-identical
data/av-ru.1967.provenance.jsonl:  byte-identical
accepted rows:                     9 858
provenance rows:                   9 858
review rows:                       3 632
```

### Gates

```text
schema violations:                 0
duplicate lines:                   0
soft hyphens:                      0
empty av/ru examples:              0
self-loops:                        0
quality_scan findings:             0
accepted missing provenance:       0 по текущей слабой проверке page+word
```

### Draft/order/links

```text
draft articles:                    13 516
draft order regressions:           900
draft high/high:                   131
ledger-confirmed regressions:      13
draft unresolved links:            1 204
```

### Accepted-only checker

```text
accepted order regressions:        408
suspicious headwords:              27
accepted oversized spans:          7
accepted -> accepted links:        1 980
accepted -> review links:          407
accepted -> missing links:         495
accepted -> OCR-invalid links:     0
review -> accepted links:          568
review -> review links:            607
review -> missing links:           399
review -> OCR-invalid links:       0
```

### Page ledger

```text
pages:                              597/597
zero-draft pages:                   [551], объяснена
candidate-drop status pages:        103
unexplained candidate drops:        105
unclosed-bracket signals:           96 на 60 страницах
```

## Что принимается

### Accepted-only gate — принято как инфраструктура

`check_accepted.py` действительно независимо читает публикуемый файл и
измеряет его собственный порядок, provenance, крупные spans и ссылки.
Число 408 совпадает с независимым подсчётом предыдущего ревью.

### Page ledger — принято частично

Ledger содержит ровно 597 страниц и полезные агрегаты по стадиям. Страница
551 визуально исследована: объяснение, что это продолжение большой статьи
`цебё` с p.550 до p.552, выглядит правдоподобно и согласуется с raw text.

Но ledger пока не выполняет точный per-candidate accounting: 105 drops —
это разность счётчиков, смешивающая реальные потери и ожидаемое поглощение.

### Decision ledger — принят как основа

Решения коммитятся, имеют id/hash и конфликтуют при изменении проверяемых
фактов. Это правильная архитектура.

Но несколько текущих решений семантически неверно используют `allowlisted`
для известных ошибок данных. Подробнее ниже.

### Baseline exact sync — принят как локальный механизм

Missing baseline и любое несовпадение теперь завершают build ошибкой. Это
лучше прежнего ceiling.

Для полноценного ratchet всё ещё нужна CI-проверка, запрещающая повышать
значение относительно base branch без отдельного явного approval.

### HTML review — принято как генератор

Генератор карточек существует, включает страницу, crop, raw OCR, proposed
entry, причины и состояние ledger. Bbox найден для 3 623 из 3 632 review
items. Теперь инструмент нужно реально использовать.

## Новые замечания

### P0. Ledger не закрывает conservation/accounting

Сумма стадий не сходится:

```text
draft articles = 13 516
accepted + review = 9 858 + 3 632 = 13 490
не имеют формального исхода = 26
```

При этом `rejected` в page ledger всегда равен 0. Несоответствие встречается
на 23 страницах, например 65, 105, 110, 114, 125, 184, 259, 298, 354, 362,
396, 437, 442, 448, 450, 456, 484, 524, 527, 528, 531, 532, 561.

Возможные причины — дедупликация, удаление bare-stub duplicate, поглощение
омонима/метаданных — должны быть представлены явными outcome, а не исчезать
между счётчиками.

Отдельно `segment_candidates - draft_articles` даёт 105 положительных drops
на 103 страницах, но текущий count-difference не способен установить судьбу
конкретного candidate.

### P0. Известные ошибки нельзя делать allowlisted accepted data

В decision ledger есть решения `allowlisted`, которые сами признают реальную
ошибку:

- `гӏамалкӏодолъи -> высокомерие`: «severely garbled OCR»;
- `каратӏ -> бахъизе`: известная ошибка распознавания `!`/палочки;
- `рехсей -> рехизаби`: явно пропущен отдельный заголовок `рёхи`;
- `лъабнусазаралда -> льабнусазарго`: OCR confusion `ъ/ь`;
- partial stress rescues с заведомо неверным заголовком.

Allowlist допустим для подтверждённой особенности сортировки источника или
безопасного диагностического артефакта. Он недопустим для статьи, о которой
уже известно, что word/граница/content неверны.

Такие решения должны быть `corrected`, `rejected` или `needs_manual_fix`, а
ошибочная статья не должна оставаться accepted.

### P0. Evidence решений пока не воспроизводимо

Decision rows обычно содержат только номера страниц и текстовое объяснение.
Ссылки ведут на `tmp/...png`, который не коммитится. `reviewer` записан как
`session-agent`, то есть решения фактически не подтверждены человеком.

Для решения, объявленного «визуально подтверждённым», нужны:

- PDF SHA-256;
- page;
- bbox/crop coordinates;
- source snippet hash;
- committed crop либо воспроизводимая crop specification;
- статус `automated-review` или реальный human reviewer;
- ожидаемая исправленная структура, если обнаружена ошибка.

### P0. Accepted всё ещё содержит очевидные ложные заголовки

Accepted-only report содержит 408 regressions. Среди них видны русские
фрагменты, которые точно не должны быть самостоятельными аварскими статьями:

```text
голова
начало
устройство
распряжка
лопатка
ложка
зуд
побои
конверт
живо
свя
всё
молча
голодом
любовник
наблюдательным
святой
чудаковатый
наглый
здравствуйте
девочки
расстатьсяс
обман
часто
перейтй
подъём
увы
```

Их число значительно больше 27 `suspicious_headwords`: текущий detector
требует, чтобы русское слово одновременно выглядело bare/fragment, поэтому
пропускает ложный заголовок с поглощённым телом.

### P0. Page 551 объяснена, но provenance carry ей противоречит

Ledger строки p.551 показывают:

```text
draft_articles: 0
carry_in: false
carry_out: false
explanation: continuation from p.550 to p.552
```

То есть текстовое решение может быть верным, но модель ledger не отражает
фактический multi-page span. Страница 551 должна быть связана с accepted или
review article `цебё` через `source_pages`/span mapping, а не просто иметь
hardcoded объяснение.

### P1. Unclosed brackets исчезли из отчёта, но не из ledger

В committed page ledger:

- 96 unclosed-bracket signals;
- 60 затронутых страниц.

Они не отражены в итоговом report как активный backlog. Поскольку прошлые
массовые склейки начинались именно с forms brackets, этот сигнал нельзя
оставлять без классификации.

### P1. Provenance completeness проверяется слишком слабо

`check_accepted.py` считает provenance полным, если есть `page` и совпадает
`word`. При этом 4 accepted entries не имеют bbox:

- `аспирантура`, p.36;
- `ассистентка`, p.36;
- `варислъи`, p.120;
- `махшел`, p.250.

Если bbox заявлен обязательной частью evidence/review, missing bbox должен
быть отдельной метрикой и gate/decision, а не скрываться за «0 missing
provenance».

### P1. Duplicate provenance всё ещё неполна

Пять accepted representatives имеют duplicate groups, и у всех пяти source
spans различаются. Для проигравших членов хранится только 100-символьный
preview, а не полный raw text/token range. Это недостаточно, чтобы доказать,
что дедупликация не склеила омонимы или разные статьи с одинаковым output.

### P1. Exact baseline sync ещё не гарантирует monotonic CI policy

Разработчик может увеличить число в `baselines.json` в том же коммите, и
локальный exact-check пройдёт. Нужна CI-проверка diff относительно base branch:

- снижение разрешено;
- повышение запрещено по умолчанию;
- повышение требует отдельного documented approval;
- изменение baseline без обновлённого report/decision запрещено.

### P1. Report metadata устаревает

Верхняя часть `report.md` всё ещё ссылается на более ранний commit, хотя ниже
есть новые метрики bbox integration. Отчёт должен генерировать или проверять
`evaluated_commit`, чтобы невозможно было случайно выдать старый report за
описание текущего HEAD.

## Батч 4: обязательные требования

### 1. Ввести per-candidate outcome ledger

Каждый `segment_candidate` получает stable id и ровно один outcome:

```text
accepted
review
rejected
merged-into:<article-id>
consumed-as-homonym-marker:<article-id>
consumed-as-form-metadata:<article-id>
duplicate-of:<candidate-id>
```

Обязательные инварианты:

```text
segment candidates = сумма всех candidate outcomes
draft articles = accepted + review + rejected + duplicate/filtered outcomes
unaccounted candidates = 0
unaccounted draft articles = 0
```

Page ledger должен агрегировать outcome ledger, а не выводить drops разностью
счётчиков.

### 2. Исправить семантику decision ledger

Разделить решения:

- `allowlisted`: данные корректны, срабатывает только диагностический артефакт;
- `corrected`: parser/data исправлены и ожидаемый entry указан;
- `rejected`: кандидат не является статьёй;
- `needs_manual_fix`: ошибка подтверждена, но исправление ещё не сделано;
- `accepted_after_human_review`: скан и итоговая статья проверены человеком.

Все текущие allowlist-строки с признанной OCR/segmentation ошибкой перевести
в корректный статус. `check_order.py` не должен считать
`needs_manual_fix` закрытой regression.

### 3. Сделать evidence воспроизводимым

Для каждого визуального решения сохранять:

- PDF hash;
- page + bbox;
- crop recipe или committed crop;
- полный raw source fragment/hash;
- reviewer type (`automated`/`human`) и identity;
- expected entry/outcome.

Decision source hash должен включать raw source fragment или geometry token
range, а не только words/pages.

### 4. Исправить конкретные известные accepted errors

В этом батче не достаточно их классифицировать. Обязательно исправить или
убрать из accepted:

- `высокомерие`;
- ошибочный `бахъизе` после `каратӏ`;
- пропущенный `рёхи` внутри `рехсей`;
- `льабнусазарго` OCR confusion;
- перечисленные выше русские false-headwords.

Добавить regression fixtures на каждый класс.

### 5. Закрыть все 27 suspicious-headword findings

Для каждого из 27:

- показать crop;
- подтвердить настоящую статью или false headword;
- сохранить decision;
- исправить parser/data при false headword.

Критерий:

```text
check_accepted.suspicious_headwords = 0 необъяснённых
```

Дополнительно расширить структурный detector так, чтобы перечисленные русские
content words попадали в review без бесконечного blacklist.

### 6. Разобрать accounting gaps и bracket anomalies

Обязательно:

- классифицировать 26 draft-статей без accepted/review outcome;
- классифицировать 105 candidate drops;
- классифицировать 96 unclosed-bracket signals на 60 страницах;
- внести результаты в outcome/decision ledger;
- исправить систематические классы и добавить fixtures.

### 7. Исправить multi-page provenance

Статья должна иметь:

- `source_pages`;
- bbox/token ranges по каждой странице;
- carry chain;
- начало/конец span.

P.551 должна агрегироваться в provenance статьи `цебё`, чтобы ledger
показывал реальный carry, а не hardcoded исключение с `carry_in: false`.

### 8. Довести bbox до 100%

Либо получить bbox для четырёх missing entries, либо создать явные decisions
с причиной отсутствия. Gate должен отдельно проверять:

```text
accepted provenance rows: 9858/9858
accepted bbox rows: 9858/9858 или decision-backed exceptions
```

### 9. Начать реальный triage review queue

HTML generator уже готов; следующий шаг — использовать его.

Первый обязательный ручной batch:

1. 27 suspicious accepted headwords;
2. 13 ранее ledger-classified high/high;
3. 25 oversized draft spans;
4. 26 accounting gaps;
5. 96 bracket anomalies;
6. минимум первые 100 boundary-high demoted review items.

Отчёт должен показать:

```text
reviewed
accepted_after_review
corrected
rejected
needs_manual_fix
remaining
```

### 10. Разобрать accepted → missing links приоритетным batch

Не требуется сразу закрыть все 495, но нужно:

- классифицировать первые 100 по причине;
- исправить систематические OCR/target parsing классы;
- отделить target, находящийся в rejected/merged outcome;
- сохранить decisions;
- снизить baseline на фактическое улучшение.

### 11. Добавить monotonic baseline policy в CI

CI сравнивает текущие baselines и metrics с base branch:

- metric increase — failure;
- baseline increase — failure без explicit approval marker;
- metric decrease при несниженной baseline — failure;
- missing metric/baseline — failure;
- report evaluated commit должен совпадать с HEAD.

## Что не нужно делать в батче 4

Не расширять пока основную задачу на:

- массовые `gender_forms`;
- полное восстановление stress;
- регистрацию `sources.json`;
- сайт;
- финальную лицензионную публикацию.

Исключение: локальное восстановление stress допустимо, если оно нужно для
исправления конкретной проверяемой regression.

## Критерии приёмки батча 4

1. Reproducible data/provenance остаются byte-identical.
2. Candidate outcome ledger покрывает 100% segment candidates.
3. Draft outcome accounting сходится без остатка.
4. Page ledger больше не использует naive count-difference как drops.
5. Known real errors не имеют статуса `allowlisted`.
6. Все decisions имеют воспроизводимое evidence.
7. 27 suspicious accepted findings разобраны; необъяснённый остаток = 0.
8. 26 исчезнувших draft entries имеют outcomes.
9. 105 candidate drops имеют outcomes.
10. 96 bracket anomalies классифицированы.
11. P.551 отражена как часть multi-page provenance `цебё`.
12. Accepted bbox coverage = 100% либо decision-backed exceptions.
13. Выполнен первый ручной review batch, решения сохранены.
14. Минимум 100 accepted→missing links классифицированы.
15. Accepted order/false-headword/link baselines не ухудшились и снижены там,
    где сделаны исправления.
16. CI запрещает повышение baseline без отдельного approval.
17. `report.md` относится к текущему HEAD и содержит outcome/review progress.

## Оценка прогресса

- воспроизводимость и tooling: **85–90%**;
- provenance/ledger infrastructure: **70–75%**;
- coverage accounting: **50–55%**;
- фактическая корректность accepted: **30–35%**;
- ручная вычитка review queue: **0–5%**;
- готовность к публикации: **нет**.

Команда практически закончила строительство инструментов. Теперь главный
риск — продолжать улучшать отчётность, не исправляя сами статьи. Следующий
успешный отчёт должен показывать уменьшение известных ошибок и рост числа
проверенных accepted, а не только новые способы измерять неизменный backlog.
