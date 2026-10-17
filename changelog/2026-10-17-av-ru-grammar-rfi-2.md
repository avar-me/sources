# av-ru: грамматический RFI, серия 2 — 2026-10-17

32 замечания: 28 исправлены в 28 статьях; 4 отклонены; нерешённых нет.

Вход: av-ru-grammar-rfi.jsonl, SHA-256: e53616809a7e0b8f886d9b7d8eb8fd1e40b3e036d5e7daec4cb3c1de0d3e15b4. Вход не изменялся; нумерация по порядку строк.

Протокол: expert-review-protocol.md; в каждом ответе сохранён исходный reason реквестера. Отказы дополнительно записаны нормативными блоками в общем rejected-файле.

Сверка PDF: books/Full-Avar-Urus-dictionary.pdf. Использован текстовый слой; визуально проверены полные страницы файла 367 (грекквартӏа, греккуртӏби) и 952 (лъавуда). Пюре, ламадур и хачадизабизе сверены по контекстам текста и текущим статьям, без заявления о новой полной вычитке.

## Исправлено в источнике (не false positive)

### #001 — -ги

- RFI: RFI-avru-grammar-69feafeef490
- поле: `senses[0].examples[0].ru`
- исходный вопрос реквестера: Typo in Russian translation: 'тям' should be 'там'.
- `senses[0].examples[0].ru`: "и здесь и там, и тям и сям" → "и здесь и там, и там и сям"
- решение: Исправлено подтверждённое несоответствие.

### #002 — арбагӏалъ

- RFI: RFI-avru-grammar-a3c98d1e45ab
- поле: `senses[0].examples[1].ru`
- исходный вопрос реквестера: missing preposition 'в' before the noun phrase 'следующую среду'
- `senses[0].examples[1].ru`: "следующую среду" → "в следующую среду"
- решение: Исправлено подтверждённое несоответствие.

### #003 — бежахине

- RFI: RFI-avru-grammar-d06780536a57
- поле: `senses[0].examples[0].ru`
- исходный вопрос реквестера: mismatch in transitivity/voice: Avar example uses intransitive/passive form 'бежахун буго' (is overbaked), whereas Russian translation uses active past plural 'перепекли' (they overbaked).
- `senses[0].examples[0].ru`: "картофель перепекли" → "картофель перепёкся"
- решение: Исправлено подтверждённое несоответствие.

### #004 — беццлъизабизе

- RFI: RFI-avru-grammar-70cdf7ac9e10
- поле: `senses[0].examples[0].av`
- исходный вопрос реквестера: possible typo in headword stem inside example; expected беццлъизавуна to match беццлъизабизе.
- `senses[0].examples[0].av`: "гӏасияб унтуца бецлъизавуна дов" → "гӏасияб унтуца беццлъизавуна дов"
- решение: Исправлено подтверждённое несоответствие.

### #005 — вай-вай-вай

- RFI: RFI-avru-grammar-55ca6a8428c9
- поле: `senses[0].examples[0].ru`
- исходный вопрос реквестера: missing preposition or particle in Russian translation: 'так теперь быть' should likely be 'как теперь быть'.
- `senses[0].examples[0].ru`: "ой-ой-ой, так теперь быть, видишь какая беда настигла?" → "ой-ой-ой, как теперь быть, видишь, какая беда настигла?"
- решение: Исправлено подтверждённое несоответствие.

### #008 — гъеду

- RFI: RFI-avru-grammar-d9cdb627f9d2
- поле: `senses[0].examples[3].ru`
- исходный вопрос реквестера: gender agreement error: participle 'выклевал' does not agree with feminine subject 'ворона'
- `senses[0].examples[3].ru`: "это — как если бы ворона ворону глаз выклевал" → "это — как если бы ворона ворону глаз выклевала"
- решение: Сказуемое согласовано с ворона: выклевала. Ворону сохранено как дательный от ворон, а не изменено на вороне автоматически.

### #009 — гӏахьаллъизе

- RFI: RFI-avru-grammar-231dd28d9e78
- поле: `senses[0].examples[0].ru`
- исходный вопрос реквестера: wrong preposition with съезд: should be 'в съезде', not 'на съезде'
- `senses[0].examples[0].ru`: "участвовать на съезде" → "участвовать в съезде"
- решение: Исправлено подтверждённое несоответствие.

### #010 — къурбан

- RFI: RFI-avru-grammar-035550ac4064
- поле: `senses[1].examples[0].comment`
- исходный вопрос реквестера: case agreement error: numeral 7 requires the genitive plural 'человек' instead of singular 'человека'
- `senses[1].examples[0].comment`: "напр. крупный рогатый скот можно делить на 7 человека" → "напр. крупный рогатый скот можно делить на 7 человек"
- решение: Исправлено подтверждённое несоответствие.

### #011 — кӏочонтезабизе

- RFI: RFI-avru-grammar-613ede1fc927
- поле: `form`
- исходный вопрос реквестера: the entry is a causative form ending in -забизе, which should be labeled as понудительная форма instead of инфинитив
- `form`: "инфинитив" → "понудительная форма"
- `see_also`: [{"target": "кӏоченабизе", "kind": "see"}] → [{"target": "кӏоченабизе", "kind": "see"}, {"target": "кӏочонтезе", "kind": "from"}]
- `senses[0].labels`: null → ["понудительная форма"]
- решение: Form исправлено на понудительная форма; добавлены существующая метка и связь from на имеющийся непонудительный глагол кӏочонтезе. Прежняя ссылка see сохранена.

### #012 — ламарт

- RFI: RFI-avru-grammar-435a7652753b
- поле: `form`
- исходный вопрос реквестера: entry is labeled as plural, but the headword, gloss, and paradigm (ergative 'ламартица', genitive 'ламартил') represent a singular noun
- `form`: "множественное число" → "именительный"
- решение: Исправлено подтверждённое несоответствие.

### #013 — лъавуда

- RFI: RFI-avru-grammar-542ff2f28156
- поле: `senses[0].examples[3].av`
- исходный вопрос реквестера: stem spelling mismatch with headword 'лъавуда' (expected 'лъавудаса')
- `senses[0].examples[3].av`: «гъов лъавудса ана» → «гъов лъавудаса ана»
- решение: Мейнтейнер подтвердил исправление печатного варианта: лъавудса → лъавудаса. Восстановлена а; остальные формы и второй омоним не менялись.

### #014 — магӏишат

- RFI: RFI-avru-grammar-5db1e5c36892
- поле: `senses[1].examples[3].av`
- исходный вопрос реквестера: internal reduplication/suffix error in 'магӏишататалда' compared to headword 'магӏишат'
- `senses[1].examples[3].av`: "жиндирго магӏишататалда хадув чӏун вуго дов" → "жиндирго магӏишаталда хадув чӏун вуго дов"
- решение: Исправлено подтверждённое несоответствие.

### #015 — муъминчӏужу

- RFI: RFI-avru-grammar-ed5e9e2dcea8
- поле: `forms[3]`
- исходный вопрос реквестера: Malformed form string containing a concatenated duplicate word.
- `forms[3]`: "муъминчӏужумуъминзаби" → "муъминзаби"
- решение: Исправлено подтверждённое несоответствие.

### #016 — официантка

- RFI: RFI-avru-grammar-5441b76ddbac
- поле: `senses[0].examples[1].ru`
- исходный вопрос реквестера: mismatch with headword: headword is 'официантка', but Russian translation uses masculine 'официант' instead of feminine 'официантка'.
- `senses[0].examples[1].ru`: "официант подала нам чай" → "официантка подала нам чай"
- решение: Исправлено подтверждённое несоответствие.

### #017 — парз

- RFI: RFI-avru-grammar-5802cee1a82a
- поле: `senses[0].text`
- исходный вопрос реквестера: missing conjunction or comma between 'обязанность' and 'требование'
- `senses[0].text`: "долг, обязанность требование, предписание" → "долг, обязанность; требование, предписание"
- решение: Исправлено подтверждённое несоответствие.

### #018 — протез

- RFI: RFI-avru-grammar-b2ec55e5f12e
- поле: `senses[0].examples[3].av`
- исходный вопрос реквестера: duplicated verb 'гьабизе'
- `senses[0].examples[3].av`: "квералъе протез гьабизе гьабизе" → "квералъе протез гьабизе"
- решение: Исправлено подтверждённое несоответствие.

### #020 — ракӏхӏалакин

- RFI: RFI-avru-grammar-8e5e2376ed17
- поле: `senses[1].examples[0].ru`
- исходный вопрос реквестера: verb aspect mismatch with context: 'закрывать' (imperfective) should be 'закрыть' (perfective) when referring to a completed single action of shutting the doors
- `senses[1].examples[0].ru`: "из-за спешки забыли закрывать двери" → "из-за спешки забыли закрыть двери"
- решение: Исправлено подтверждённое несоответствие.

### #021 — ревизорлъи

- RFI: RFI-avru-grammar-75b15070510b
- поле: `senses[0].examples[0].av`
- исходный вопрос реквестера: double suffixation on noun derivation 'ревизорлъилъи' is likely a typographical error for 'ревизорлъи гьабизе'
- `senses[0].examples[0].av`: "ревизорлъилъи гьабизе" → "ревизорлъи гьабизе"
- решение: Исправлено подтверждённое несоответствие.

### #022 — секретарь

- RFI: RFI-avru-grammar-294bad0276ea
- поле: `senses[0].examples[5].av`
- исходный вопрос реквестера: typo in Avar form: extra syllable '-ра-' in 'секретарарасул', should be 'секретаразул'.
- `senses[0].examples[5].av`: "секретарарасул хъулухъ" → "секретарасул хъулухъ"
- решение: Убрано повторное ра: секретарарасул → секретарасул. Предложенное в RFI секретаразул — множественное число и не принято: в парадигме указан родительный единственного секретарасул.

### #023 — серия

- RFI: RFI-avru-grammar-d6fa2b095c7c
- поле: `forms[2]`
- исходный вопрос реквестера: Typo in form: double ъ in 'сериялъъул' should be single ъ.
- `forms[2]`: "сериялъъул" → "сериялъул"
- решение: Исправлено подтверждённое несоответствие.

### #024 — сериялъул

- RFI: RFI-avru-grammar-dc4902d3df20
- поле: `senses[1].examples[0].av`
- исходный вопрос реквестера: Typo with double ъ in 'сериялъулъул'.
- `senses[1].examples[0].av`: "ункъо сериялъулъул фильм" → "ункъо сериялъул фильм"
- решение: Исправлено подтверждённое несоответствие.

### #025 — собрание

- RFI: RFI-avru-grammar-72bc9cfd30e3
- поле: `senses[0].examples[8].ru`
- исходный вопрос реквестера: wrong preposition/case combination: in Russian, 'участвовать' takes preposition 'в' with the prepositional case ('участвовать в собрании'), not 'на'.
- `senses[0].examples[8].ru`: "участвовать на собрании" → "участвовать в собрании"
- решение: Исправлено подтверждённое несоответствие.

### #026 — тӏадегӏанаб

- RFI: RFI-avru-grammar-7a354df21930
- поле: `senses[1].examples[4].ru`
- исходный вопрос реквестера: Spelling error in Russian word: 'всевышный' should be 'всевышний'.
- `senses[1].examples[4].ru`: "всевышный, бог; господь" → "всевышний, бог; господь"
- решение: Исправлено подтверждённое несоответствие.

### #027 — форум

- RFI: RFI-avru-grammar-5000e9d96e6f
- поле: `senses[0].examples[4].ru`
- исходный вопрос реквестера: incorrect prepositional government with 'участвовать': should take the preposition 'в' with the prepositional case ('участвовать в форуме'), not 'на'.
- `senses[0].examples[4].ru`: "участвовать на форуме" → "участвовать в форуме"
- решение: Исправлено подтверждённое несоответствие.

### #028 — хал

- RFI: RFI-avru-grammar-f5b1c3e60311
- поле: `senses[0].examples[6].ru`
- исходный вопрос реквестера: verb 'надзирать' requires the preposition 'за' with the instrumental case, not the accusative case
- `senses[0].examples[6].ru`: "надзирать кого-либо" → "надзирать за кем-либо"
- решение: Исправлено подтверждённое несоответствие.

### #030 — хъатир

- RFI: RFI-avru-grammar-41589bca786d
- поле: `senses[0].examples[2].ru`
- исходный вопрос реквестера: wrong preposition/case: preposition 'с' requires genitive ('с уважением' or 'из уважения'), but 'уважения' here is grammatically disjoint or incorrect for the intended meaning.
- `senses[0].examples[2].ru`: "с уважения к кому-либо" → "из уважения к кому-либо"
- решение: Исправлено подтверждённое несоответствие.

### #031 — щущазабизе

- RFI: RFI-avru-grammar-64de900bc177
- поле: `senses[3].examples[0].av`
- исходный вопрос реквестера: malformed verb form with a duplicated syllable 'ба'.
- `senses[3].examples[0].av`: "хъала щущазабабизе" → "хъала щущазабизе"
- решение: Исправлено подтверждённое несоответствие.

### #032 — этек

- RFI: RFI-avru-grammar-9f26579fa34f
- поле: `senses[0].examples[0].ru`
- исходный вопрос реквестера: Wrong verb choice: 'одеть' requires a person, use 'обуть' or 'надеть' for a thing like a boot.
- `senses[0].examples[0].ru`: "одеть на ногу сапог" → "надеть на ногу сапог"
- решение: Исправлено подтверждённое несоответствие.

## Отклонено

### #006 — вирулагь

- поле: `senses[0].examples[0].ru`
- текст: «он страдает расстройством желудка»
- исходный вопрос реквестера: Typo in example translation: 'асде' corresponds to 'ем', but the Russian translation uses 'он' instead of 'у него'.
- ответ: Он страдает расстройством желудка и у него расстройство желудка — эквивалентные по смыслу русские конструкции. Дательный участник в аварском не обязывает переводить его русской конструкцией у него. Замечание про асде не доказывает ошибку русского перевода.

### #007 — грекквартӏа

- поле: `forms[5]`
- текст: «греккуртӏби»
- исходный вопрос реквестера: Plural form 'греккуртӏби' drops the syllable 'вартӏ' inconsistently with the stem 'грекквартӏ-'.
- ответ: Греккуртӏби — нерегулярное множественное число, прямо напечатанное в парадигме грекквартӏа и отдельной статье греккуртӏби (PDF, страница файла 367). Та же чередующаяся основа представлена в квартӏа → куртӏби. Это не выпадение слога при OCR.

### #019 — пюре

- поле: `senses[0].examples[0].ru`
- текст: «морковное пюре»
- исходный вопрос реквестера: mismatch between Avar 'ламадуралъул' (carrot) and Russian translation 'морковное': 'ламадур' means tomato, so the translation should be 'томатное пюре'.
- ответ: Ламадур в этом словаре означает морковь, морковка, что подтверждено отдельной статьёй ламадур и примерами посадки, продажи и очистки моркови. PDF в статье пюре также даёт ламадуралъул пюре — морковное пюре. Предлагаемая замена на томатное изменила бы значение.

### #029 — хачадизабизе

- поле: `senses[0].examples[0].ru`
- текст: «не нахожу места от сильной зубной боли»
- исходный вопрос реквестера: mismatch in grammatical person: the Avar example has a third-person participle 'хачадизавулев вуго', whereas the Russian translation uses the first person 'нахожу'
- ответ: Хачадизавулев вуго выражает мужской грамматический класс, а не однозначно третье лицо. Без выраженного местоимения возможен и подразумеваемый говорящий мужчина. Русское не нахожу места не противоречит конструкции; в PDF приведён тот же перевод. Менять лицо без контекста не нужно.
