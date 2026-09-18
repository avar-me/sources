# Пятый батч требований по парсингу словаря Саидова 1967 года

Дата ревью: 2026-09-18  
Проверенная ветка: `av-ru-1967-parsing`  
Проверенный коммит: `1be5534`  
Предыдущее ревью: `av-ru-1967-review-batch-4-2026-09-17.md`  
Статус: Batch 4 существенно выполнен, но обнаружены два новых P0-дефекта воспроизводимости и CI

## Краткий вывод

Команда действительно закрыла большую часть четвёртого батча. В чистом detached
worktree полный `build_all.sh` успешно воспроизвёл основные артефакты и метрики:

- 9 836 accepted;
- 3 632 review;
- 13 516 draft articles;
- 13 619 segment candidates;
- 0 unaccounted candidates;
- 0 unaccounted draft articles;
- 383 accepted order regressions (было 408);
- 2 suspicious accepted headwords (было 27);
- 228 accepted-origin missing links (было 495);
- 278 review-origin missing links (было 399);
- 464 unresolved draft links (было 1 204);
- 0 schema/quality/provenance/bbox hard-gate findings.

Это реальный прогресс. Особенно полезны outcome ledger, corrections layer,
`source_pages`, 100% bbox coverage и stress-insensitive reference matching.

Однако статус «воспроизводимо» пока нельзя принять полностью:

1. чистая полная сборка изменяет committed `page_ledger.jsonl`;
2. monotonic CI policy не защищает основной сценарий merge в `main` и уже не
   проходит при сравнении с предыдущим review-коммитом;
3. 33 corrections помечены как исправленные только automated reviewer, хотя
   документация называет их hand-verified;
4. реальная вычитка очереди из 3 632 элементов всё ещё не начата.

Следующий батч должен сначала восстановить честную воспроизводимость, затем
перейти к измеримому ручному разбору данных.

## Что проверено независимо

Проверка выполнялась в новом detached worktree коммита `1be5534`, с полной
повторной экстракцией страниц 23–619 и запуском документированной команды:

```bash
scripts/av-ru-1967/build_all.sh
```

Сборка завершилась с кодом 0. `data/av-ru.1967.jsonl` и
`data/av-ru.1967.provenance.jsonl` совпали с committed версиями. Полученный
SHA-256 accepted-файла:

```text
9b7571be858073563064b7f059af92438355b32bc4ca1eecc2011bae61df0c17
```

Но `data/av-ru.1967.page_ledger.jsonl` не совпал с committed версией:

```text
438 insertions, 438 deletions
```

Почти весь diff — поле `order_regressions`: committed ledger содержит старый
результат `tmp/av-ru.1967/order_check.jsonl`, а чистая сборка получает нули.

## Что сделано хорошо

### 1. Outcome accounting теперь настоящий

`candidate_outcomes.jsonl` содержит 13 619 строк:

- 13 516 `own-article`;
- 103 `merged-into:*`.

`draft_outcomes.jsonl` содержит ровно 13 516 строк:

- 9 858 `accepted` до corrections layer;
- 3 632 `review`;
- 14 `dropped-bare-stub-duplicate`;
- 12 `duplicate-of:*`.

Неучтённых кандидатов и draft articles нет. Прежняя проблема 26 исчезнувших
draft entries и 105 наивно вычисленных drops устранена на уровне модели учёта.

### 2. Corrections layer воспроизводим технически

Все 33 correction rows применяются без hash conflict. После них accepted
снижается с 9 858 до 9 836. Accepted и provenance остаются 1:1, порядок слов
совпадает, bbox coverage равен 100%.

### 3. Основные метрики реально улучшились

Исправления подозрительных русских заголовков и нормализация stress notation
дали существенное снижение известных ошибок. Это уже изменение самих данных,
а не только новая отчётность.

### 4. Multi-page carry теперь представлен структурно

Draft/review entry `цебё` имеет `source_pages: [550, 551, 552]`, а p.551
структурно объясняется через `absorbed_by: ["цебё"]`. Это лучше прежнего
hardcoded исключения.

## P0. Исправить невоспроизводимый page ledger

### Проблема

Текущий порядок в `build_all.sh`:

```text
check_accepted
build_page_ledger
check_order
```

При этом `build_page_ledger.py` читает:

```text
tmp/av-ru.1967/order_check.jsonl
```

Этот файл создаётся только следующим шагом. Поэтому результат зависит от того,
остался ли `order_check.jsonl` от предыдущего запуска:

- в рабочем каталоге разработчика ledger получил старые regression counts;
- в чистом worktree файла ещё нет, и все regression counts стали нулевыми;
- build завершился успешно и молча переписал committed ledger.

Это классическая зависимость от stale tmp state и нарушение главного обещания
pipeline — byte-for-byte reproducibility.

### Требование

1. Запускать `check_order.py` до `build_page_ledger.py`, либо перестать читать
   его output из ledger stage.
2. В начале полной сборки удалять все regenerable intermediate outputs, а не
   только `geometry/`.
3. Добавить чистый reproducibility test:
   - удалить `tmp/av-ru.1967/`;
   - выполнить полный build;
   - сохранить hashes committed artifacts;
   - выполнить второй build;
   - проверить отсутствие diff и совпадение hashes.
4. CI после build должен выполнять `git diff --exit-code` минимум для:
   - `data/av-ru.1967.jsonl`;
   - `data/av-ru.1967.provenance.jsonl`;
   - `data/av-ru.1967.page_ledger.jsonl`.
5. Исправленный committed ledger должен быть сгенерирован именно чистым
   pipeline, а не текущим загрязнённым `tmp/`.

### Критерий приёмки

Два последовательных запуска из чистого состояния дают нулевой git diff по
всем committed generated artifacts.

## P0. Переделать monotonic baseline CI policy

### Проблема 1: PR в main получает пустую защиту

Workflow передаёт PR base SHA. В `main` файла
`scripts/av-ru-1967/baselines.json` ещё нет. `check_ci_policy.py` в этом случае
пишет «brand-new file, nothing to compare, ok». Следовательно, при финальном
PR из feature branch в `main` можно одновременно поднять любые baselines —
никакого исторического эталона CI не проверит.

### Проблема 2: policy уже не проходит историю ветки

Независимый запуск:

```bash
python3 scripts/av-ru-1967/check_ci_policy.py --base-ref 05fb50e
```

завершается ошибкой:

```text
FAIL: page_ledger.unexplained_drops existed at 05fb50e but is missing from HEAD
```

Метрика была удалена раньше добавления CI, поэтому сравнение только с `HEAD~1`
не обнаружило исчезновение. Это показывает, что direct-push policy защищает
лишь последний маленький шаг, но не весь review interval.

### Проблема 3: approval недостаточно строгий

Один trailer `baseline-regression-approved: <reason>` в HEAD разрешает сразу
все выросшие metrics. Это самодекларация автора коммита, а не отдельный approval,
и reason не привязан к конкретной метрике и значениям before/after.

### Требование

1. Определить committed policy base, который существует и на feature branch,
   и после merge в main. Возможные варианты:
   - отдельный `baseline_history.json` с предыдущими принятыми значениями;
   - сравнение с последним merge-base/тегом, где parser baselines существовали;
   - immutable reviewed snapshot, обновляемый отдельным approved commit.
2. Миграцию/удаление метрики оформлять явно, а не считать обычным исчезновением.
   Для `page_ledger.unexplained_drops` записать замену на outcome-accounting
   metrics и сохранить audit trail.
3. Approval regression должен перечислять каждую метрику, старое/новое значение
   и причину. Предпочтительно требовать отдельный reviewed policy file или
   GitHub approval, а не только commit-message автора.
4. Добавить negative CI tests для сценариев:
   - PR base не содержит baselines;
   - метрика удалена за несколько коммитов до HEAD;
   - две метрики выросли, approved только одна;
   - baseline понижен, но build metric ему не соответствует;
   - committed generated artifact изменился после build.

### Критерий приёмки

Нельзя замержить увеличение или удаление существующей quality metric простым
одновременным редактированием `baselines.json` и commit message.

## P0. Сделать freshness отчёта проверяемой

### Проблема

`check_report_freshness()` проверяет только, что `evaluated_commit` является
любым предком HEAD. Старый коммит навсегда остаётся предком, поэтому проверка
не ловит устаревший отчёт.

Это видно уже сейчас:

- заголовок report датирован 2026-09-17;
- вводная часть говорит `as of commit cbbcfa6`;
- Batch-4 указывает `evaluated_commit: 1ad6898`;
- HEAD — `1be5534`;
- старый раздел Current metrics всё ещё показывает 9 858 entries, 408 order
  regressions, 27 suspicious headwords и 495 missing links.

Формальное пояснение «historical snapshot» помогает читателю, но не превращает
отчёт в единый current status.

### Требование

Вместо ancestor-only проверки хранить в отчёте или machine-readable manifest:

- hashes всех committed generated artifacts;
- hash `baselines.json`;
- evaluated tree SHA либо commit SHA, который должен быть `HEAD` или `HEAD^`
  только для чистого documentation-only report commit;
- точные текущие metrics, автоматически сверяемые с baselines/output.

Удалить или явно вынести старый snapshot в секцию History, чтобы одновременно
не существовали два набора «current metrics».

## P1. Не называть automated corrections hand-verified

Все 33 rows в `data/av-ru.1967.corrections.jsonl` имеют:

```text
reviewer_type: automated
reviewer: automated-agent-review (... no human sign-off)
```

При этом `apply_corrections.py` и README называют слой `hand-verified` и
`individually-verified`. Несколько исправлений не просто чинят символ, а
перестраивают sense/example content и объединяют статьи. Source hash доказывает
стабильность входа, но не правильность редакционного решения.

### Требование

1. Переименовать текущий статус в `automated-proposed-and-verified` либо
   `pending_human_signoff`.
2. Для каждого correction сохранить:
   - before entry/entries;
   - after entry;
   - page and bbox/crop;
   - конкретное объяснение каждого смыслового переноса;
   - human reviewer/status после реальной проверки.
3. До human signoff не считать semantic merges окончательно approved.
4. Ввести отдельные классы риска:
   - glyph-only rename;
   - punctuation/markup repair;
   - headword removal/merge;
   - sense/example reconstruction.
5. Семантические изменения данных отразить в специализированном correction
   changelog; при включении источника в общий published dataset выполнить
   требования корневого `CHANGELOG.md`.

## P1. Исправить семантику bracket decision

Bulk row `bracket-anomalies:batch-4-item-6` имеет decision `allowlisted`, хотя
95 из 96 статей всё ещё лежат в review и прямо отложены до будущей вычитки.
Классификация «безопасно не опубликовано» не равна решению «данные корректны».

### Требование

- заменить bulk `allowlisted` на `classified_pending_review` или
  `needs_manual_fix`;
- не использовать resolved decision values для unpublished unresolved items;
- связать каждую из 96 аномалий с устойчивым item id, outcome и будущим review
  decision;
- после correction `шал` accepted anomaly должна исчезнуть из post-correction
  accepted check, а не оставаться статистически accepted в draft report без
  пояснения уровня stage.

## P1. Закрыть оставшиеся suspicious headwords до нуля

Сейчас остаются два findings:

- `во` — признанная ошибка и `needs_manual_fix`; нужно восстановить статью
  `вйхьизе`, удалить ложный headword и проверить переставленные av/ru examples;
- `сундук` — legitimate see-only cross-reference; checker должен понимать
  содержательность корректного `see_also`, чтобы не сохранять известный false
  positive в baseline.

Критерий: `check_accepted.suspicious_headwords = 0`, без blacklist и без
ослабления детектора для реальных ложных заголовков.

## P1. Начать настоящий review sprint

Review queue всё ещё содержит 3 632 записи. Исправления suspicious-headword и
bracket-классификация полезны, но не заменяют разбор очереди.

### Первый обязательный tranche

Разобрать минимум 200 review items, приоритетно:

1. 95 unresolved bracket anomalies;
2. 12 demoted oversized spans;
3. все boundary-high-demoted entries с наиболее коротким/очевидным repair;
4. `цебё` как multi-page high-value entry;
5. записи, на которые ведут accepted links.

Для каждой карточки должен быть устойчивый outcome:

- corrected-and-accepted;
- accepted-after-human-review;
- rejected-not-a-headword;
- merged-into;
- needs-manual-fix с конкретной причиной.

Progress считать не по наличию HTML, а по числу реально закрытых карточек и
изменению accepted/review counts.

## P1. Продолжить снижение order/link backlog

После этого апдейта всё ещё остаются:

- 383 accepted order regressions;
- 900 draft order regressions;
- 228 accepted-origin missing links;
- 278 review-origin missing links;
- 464 unresolved draft links.

Следующий батч должен не только классифицировать, но и уменьшить хотя бы два
из этих показателей.

Минимальная цель:

- разобрать все 228 accepted-origin missing links;
- для каждого сохранить категорию: valid class variant / missing accepted
  entry / target in review / OCR target / truncated target / bad parser split;
- исправить безопасные систематические классы;
- разобрать минимум 100 accepted order regressions, начиная с high-confidence
  и соседей corrections;
- не считать source grouping resolved без визуального подтверждения страницы.

## P2. Довести multi-page provenance до уровня evidence

`source_pages` решает вопрос принадлежности страниц, но пока не даёт точной
геометрии контента на каждой странице. Для `цебё` committed accepted provenance
отсутствует, потому что запись находится в review; bbox относится только к
первой строке p.550.

Добавить для multi-page draft/review/accepted entries:

```json
"source_spans": [
  {"page": 550, "bbox": [...]},
  {"page": 551, "bbox": [...]},
  {"page": 552, "bbox": [...]}
]
```

или эквивалентные token ranges. HTML review должен показывать все страницы
multi-page entry, а не только crop первой строки.

## Критерии приёмки Batch 5

1. Clean build не изменяет ни один committed generated artifact.
2. Повторный build даёт те же hashes.
3. Page ledger не зависит от существования старых tmp files.
4. CI выполняет `git diff --exit-code` после build.
5. Monotonic policy работает при merge в main, даже если base branch раньше
   не содержал baselines.
6. Удаление/миграция metric имеет явный audit trail.
7. Один approval не разрешает неограниченное число несвязанных regressions.
8. Report freshness проверяет конкретное состояние artifacts, а не любого
   предка HEAD.
9. Corrections имеют честный review status; semantic corrections получают
   human signoff.
10. Bulk bracket decision не обозначает unresolved review items как resolved.
11. Suspicious accepted headwords снижены с 2 до 0.
12. Не менее 200 review cards получают устойчивые decisions.
13. Все 228 accepted-origin missing links классифицированы.
14. Не менее 100 accepted order regressions разобраны.
15. Multi-page review UI показывает evidence со всех source pages.
16. Обновлённый отчёт содержит один непротиворечивый current snapshot.

## Обновлённая оценка прогресса

- воспроизводимость pipeline: **75–80%** — accepted/provenance стабильны, но
  page ledger обнаружил stale-tmp dependency;
- tooling и gates: **80–85%** — сильная база, CI policy требует исправления;
- provenance/coverage accounting: **75–80%**;
- фактическая корректность accepted: **40–45%**;
- ручная вычитка review queue: **0–5%**;
- готовность к поисковому публичному preview: **близко после P0 и human audit
  corrections**;
- готовность к публикационному/научному использованию: **пока нет**.

Команда впервые заметно улучшила сами данные. Следующий качественный скачок
теперь зависит не от добавления новых инструментов, а от исправления найденных
P0 и регулярного закрытия review-карточек с человеческим подтверждением.
