# av-ru: грамматический RFI — 2026-10-16, уточнения 2026-10-17

124 замечания: 108 исправлено, 16 отклонено, нерешённых нет. Изменено 103 статьи.

Рабочий av-ru-grammar-rfi.jsonl сохранён без изменения. Номера — порядок строк.

Протокол: expert-review-protocol.md; каждый отказ содержит исходный вопрос и отдельный ответ.

Сверка: текстовый слой books/Full-Avar-Urus-dictionary.pdf; визуально просмотрены страницы файла 949, 1087 и 851. Подтверждения мейнтейнера: пенщола, дательное какие и остальные перечисленные ниже уточнения.

## Исправлено в источнике (не false positive)

### #001 — апрелалда

- RFI: RFI-avru-grammar-32dd3f37bdfe
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: Redundant case suffix in 'апрелалдалда': contains both locative suffix -да and superessive suffix -да.
- `senses[0].examples[0].av`: "щуабилеб апрелалдалда" → "щуабилеб апрелалда"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #002 — апрелалда

- RFI: RFI-avru-grammar-e6aae4e57f81
- поле RFI: `senses[0].examples[1].av`
- исходный вопрос реквестера: Redundant case suffix in 'апрелалдалда': contains both locative suffix -да and superessive suffix -да.
- `senses[0].examples[1].av`: "апрелалдалда гьаюна дир яс" → "апрелалда гьаюна дир яс"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #003 — араб-хвараб

- RFI: RFI-avru-grammar-0e31e85cffbb
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: Genitive form 'араб-хвараул' appears inconsistent with stem 'араб-хвара' and standard case suffix.
- `senses[0].examples[0].av`: "араб-хвараул бицине" → "араб-хваралъул бицине"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #004 — арбагӏалъ

- RFI: RFI-avru-grammar-06ce89319071
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: Adverbial form 'арбагӏалъалъ' has a doubled case/suffix extension that is morphologically irregular.
- `senses[0].examples[0].av`: "арбагӏалъалъ вачӏа" → "арбагӏалъ вачӏа"
- `senses[0].examples[1].av`: "тӏаде арбагӏалъалъ" → "тӏаде арбагӏалъ"
- `senses[0].examples[2].av`: "щибаб арбагӏалъалъ" → "щибаб арбагӏалъ"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #005 — армия

- RFI: RFI-avru-grammar-6eaf11cbf6eb
- поле RFI: `senses[0].examples[2].av`
- исходный вопрос реквестера: possible typo in genitive suffix: 'армияул' should likely be 'армиялъул' to match standard noun inflection
- `senses[0].examples[2].av`: "армияул штаб" → "армиялъул штаб"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #006 — багъарахъдизабизе

- RFI: RFI-avru-grammar-d74df5b076ab
- поле RFI: `senses[0].examples[1].ru`
- исходный вопрос реквестера: Wrong noun number: 'ржи' is genitive singular or plural, but the context requires plural nominative 'рожь' or 'ржи' (fields of rye), or better 'колышет рожь' (mass noun).
- `senses[0].examples[1].ru`: "ветер колыхает ржи" → "ветер колышет рожь"
- решение: По решению мейнтейнера: ветер колышет рожь.

### #010 — болъонил

- RFI: RFI-avru-grammar-1238d738a297
- поле RFI: `senses[1].examples[1].comment`
- исходный вопрос реквестера: preposition 'о' requires prepositional case, but 'обескультурье' is in genitive or accusative (should be 'об обескультурье').
- `senses[1].examples[1].comment`: "о обескультурье" → "о бескультурье"
- решение: Исправлено полное слово: о бескультурье. Предыдущее об обескультурье было ошибкой разбора.

### #011 — босизе

- RFI: RFI-avru-grammar-87ec0fb8cbb2
- поле RFI: `senses[7].text`
- исходный вопрос реквестера: missing conjunction or punctuation between verbs: should be 'потерять что-либо, лишиться чего-либо', not missing a comma.
- `senses[7].text`: "потерять что-либо лишиться чего-либо" → "потерять что-либо; лишиться чего-либо"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #012 — бульвар

- RFI: RFI-avru-grammar-4ea150677736
- поле RFI: `senses[0].examples[2].av`
- исходный вопрос реквестера: spacing error: 'бульвар алде' should be written as one word 'бульваралде'
- `senses[0].examples[2].av`: "бульвар алде рахъине" → "бульваралде рахъине"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #013 — бухӏунчӏикӏ

- RFI: RFI-avru-grammar-bb342f88f230
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: unnecessary semicolon breaking the sentence structure after 'изготавливаемое'
- `senses[0].text`: "национальное блюдо, изготавливаемое; перемешиванием толокна на кипячёном молоке или сыворотке" → "национальное блюдо, изготавливаемое перемешиванием толокна на кипячёном молоке или сыворотке"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #014 — газет

- RFI: RFI-avru-grammar-b115a33ecb8d
- поле RFI: `senses[0].comment`
- исходный вопрос реквестера: parenthetical note '(о)публиковать в газете' is semantically disconnected from the headword 'газета'
- `senses[0].comment`: "(о)публиковать в газете" → null
- `senses[0].examples`: [{"av": "къадал газет", "ru": "стенная газета"}, {"av": "газет биччазе", "ru": "выпускать, издавать газету"}, {"av": "газет цӏализе", "ru": "(про)читать газету"}, {"av": "газеталъул гьурмазда", "ru": "на страницах газеты"}, {"av": "газеталда бахъизе газеталда цӏализе", "ru": "(про)читать в газете"}, {"av": "газеталде макъала битӏизе", "ru": "отправить статью в газету"}, {"av": "газетал хъвазе", "ru": "подписываться на газеты, выписывать газеты"}] → [{"av": "къадал газет", "ru": "стенная газета"}, {"av": "газет биччазе", "ru": "выпускать, издавать газету"}, {"av": "газет цӏализе", "ru": "(про)читать газету"}, {"av": "газеталъул гьурмазда", "ru": "на страницах газеты"}, {"av": "газеталда бахъизе", "ru": "(о)публиковать в газете"}, {"av": "газеталда цӏализе", "ru": "(про)читать в газете"}, {"av": "газеталде макъала битӏизе", "ru": "отправить статью в газету"}, {"av": "газетал хъвазе", "ru": "подписываться на газеты, выписывать газеты"}]
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #015 — гьуинлъизе

- RFI: RFI-avru-grammar-afaa55111250
- поле RFI: `senses[1].examples[0].ru`
- исходный вопрос реквестера: Adjective agreement error: 'вкусным' should be feminine/neuter 'вкусной' or noun 'вкусной' to agree with 'еда' (or phrased as 'еда становится вкусной').
- `senses[1].examples[0].ru`: "голодному еда становится вкусным" → "голодному еда становится вкусной"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #016 — гӏалимчи

- RFI: RFI-avru-grammar-e1f67485f56f
- поле RFI: `forms[3]`
- исходный вопрос реквестера: corrupted plural form containing a duplicated prefix/string 'гӏалимчгӏалимзаби'
- `forms[2]`: "гӏалимчясул" → "гӏалимчиясул"
- `forms[3]`: "гӏалимчгӏалимзаби" → "гӏалимзаби"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #017 — гӏехьеллъизе

- RFI: RFI-avru-grammar-1a9c2af83b89
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: verb form error: 'становится' is misspelled and should be 'становиться' (or 'становится' without soft sign if intended as third-person singular, but here it follows an infinitive pattern 'становится, стать').
- `senses[0].text`: "становится, стать отяжелевшим, тучным" → "становиться, стать отяжелевшим, тучным"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #018 — гӏинтӏамизе

- RFI: RFI-avru-grammar-bca1dd5691a7
- поле RFI: `senses[1].text`
- исходный вопрос реквестера: wrong case: verb прислушаться requires genitive with 'к' (прислушаться к кому-чему-либо), not direct genitive
- `senses[1].text`: "прислушаться кого-чего-либо, повиноваться кому-чему-либо" → "прислушаться к кому-чему-либо, повиноваться кому-чему-либо"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #019 — дализабизе

- RFI: RFI-avru-grammar-44718b0e0c43
- поле RFI: `senses[0].examples[1].ru`
- исходный вопрос реквестера: wrong verb form: 'пусть повесить' should use the imperative/subjunctive form 'пусть повесит'.
- `senses[0].examples[1].ru`: "если жалко, пусть повесить на свою шею" → "если жалко, пусть повесит на свою шею"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #020 — даран

- RFI: RFI-avru-grammar-5b6f4efe48d7
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: spelling error: 'в слепую' should be written as one word ('вслепую' adverb).
- `senses[0].examples[0].ru`: "торговля в слепую; кота в мешке купить" → "торговля вслепую; купить кота в мешке"
- решение: Вслепую слитно; по решению мейнтейнера нейтральный порядок слов: купить кота в мешке.

### #021 — дваргъи-дванкиялда

- RFI: RFI-avru-grammar-eada612f0806
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: malformed Avar word form: duplicated suffix 'ялдаялда'
- `senses[0].examples[0].av`: "дваргъи-дванкиялдаялда къана дос дида хадуб нуцӏа" → "дваргъи-дванкиялда къана дос дида хадуб нуцӏа"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #022 — декабралда

- RFI: RFI-avru-grammar-08f99097577a
- поле RFI: `senses[0].examples[1].av`
- исходный вопрос реквестера: Redundant case suffix repetition inside the form 'декабралдалдаса'.
- `senses[0].examples[1].av`: "декабралдалдаса байбихьун" → "декабралдаса байбихьун"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #023 — доклад

- RFI: RFI-avru-grammar-a166fdc56453
- поле RFI: `senses[0].examples[5].av`
- исходный вопрос реквестера: broken word division in Avar example: 'доклад алъухъ' should be written as one word or corrected.
- `senses[0].examples[5].av`: "доклад алъухъ гӏенеккизе" → "докладалъухъ гӏенеккизе"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #024 — жив

- RFI: RFI-avru-grammar-39be901a112f
- поле RFI: `senses[0].examples[1].ru`
- исходный вопрос реквестера: incorrect subordinate clause construction: 'что не увидел ли' mixes conjunctions improperly, should be 'не увидел ли'
- `senses[0].examples[1].ru`: "Курбан спросил чабана, что не увидел ли он его кобылу" → "Курбан спросил чабана, не увидел ли он его кобылу"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #025 — жилд

- RFI: RFI-avru-grammar-20d41ce5f1de
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: missing conjunction or comma between homogeneous Russian nouns 'переплёт' and 'том'
- `senses[0].text`: "переплёт том" → "переплёт; том"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #026 — жужахӏалъул

- RFI: RFI-avru-grammar-02ee963b5ab8
- поле RFI: `senses[1].examples[6].ru`
- исходный вопрос реквестера: wrong gender agreement with 'полымя' (neut.), which requires 'адское' instead of 'адскую'.
- `senses[1].examples[6].ru`: "не оставлю я тебя, хоть ты кинешься в адскую полымя" → "не оставлю я тебя, хоть ты кинешься в адское полымя"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #027 — изолятор

- RFI: RFI-avru-grammar-05d6cc6d994f
- поле RFI: `senses[1].examples[1].ru`
- исходный вопрос реквестера: wrong preposition: should be 'из' instead of 'с' with 'изолятор'
- `senses[1].examples[1].ru`: "его перевели с изолятора в другую палату" → "его перевели из изолятора в другую палату"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #029 — капитанасул

- RFI: RFI-avru-grammar-6e9b32722df1
- поле RFI: `senses[1].examples[0].av`
- исходный вопрос реквестера: malformed suffixed genitive form in Avar example: 'капитанасуласул' contains a redundant case suffix.
- `senses[1].examples[0].av`: "капитанасуласул погонал" → "капитанасул погонал"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #030 — кинабго

- RFI: RFI-avru-grammar-1c372814182b
- поле RFI: `pos`
- исходный вопрос реквестера: 'кинабго' is a determinative pronoun (местоимение), not a noun (существительное).
- `pos`: "существительное" → "местоимение"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #031 — колхозчи

- RFI: RFI-avru-grammar-4456c561f151
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: misspelled oblique form 'колхозчясул'; standard genitive is 'колхозчиясул'
- `senses[0].examples[0].av`: "колхозчясул захӏматкъоял" → "колхозчиясул захӏматкъоял"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #032 — кунчӏ-кунчӏизе

- RFI: RFI-avru-grammar-c76c5bf0b469
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: Spelling error in Russian alternating root: 'блестать' should be 'блестеть' or 'блистать'.
- `senses[0].text`: "сверкать, блестать, блистать" → "сверкать, блестеть, блистать"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #033 — курсал

- RFI: RFI-avru-grammar-ac57e55c2e7d
- поле RFI: `senses[0].examples[2].av`
- исходный вопрос реквестера: Typographical error in Avar spelling: duplicated vowel letter in 'курсаазда' instead of 'курсазда'.
- `senses[0].examples[2].av`: "курсаазда цӏализе" → "курсазда цӏализе"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #034 — къадан

- RFI: RFI-avru-grammar-77ca683cc984
- поле RFI: `senses[1].examples[2].ru`
- исходный вопрос реквестера: wrong preposition: 'в обочине' should be 'на обочине' with the preposition 'на'.
- `senses[1].examples[2].ru`: "в обочине леса" → "на обочине леса"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #035 — къадарлъизабизе

- RFI: RFI-avru-grammar-75cc53109789
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: missing syllable in the verbal derivative compared to headword stem
- `senses[0].examples[0].av`: "унтуца къадаръизавун вуго дов" → "унтуца къадарлъизавун вуго дов"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #036 — къваркьиялда

- RFI: RFI-avru-grammar-de37771960c5
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: missing comma before the participle 'топча'
- `senses[0].examples[0].ru`: "они шли с треском топча под ногами сухие листья" → "они шли с треском, топча под ногами сухие листья"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #037 — къосине

- RFI: RFI-avru-grammar-4aa4a467aa2f
- поле RFI: `senses[1].examples[1].ru`
- исходный вопрос реквестера: incorrect participle form; should be 'заблудший' or 'заблудившийся'
- `senses[1].examples[1].ru`: "заблудшийся человек" → "заблудившийся человек"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #038 — къотӏел

- RFI: RFI-avru-grammar-ac9db94262d6
- поле RFI: `forms[4]`
- исходный вопрос реквестера: malformed form concatenation merging 'къотӏел' and 'къотӏалил'
- `forms[4]`: "къотӏелкъотӏалил" → "къотӏалил"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #039 — къуцӏ

- RFI: RFI-avru-grammar-4089616f179a
- поле RFI: `pos`
- исходный вопрос реквестера: pos 'междометие' contradicts the noun senses and declension forms listed.
- `form`: "—" → "именительный"
- `pos`: "междометие" → "существительное"
- решение: Исправлены pos/form. Дополнительно PDF показывает повторный заголовок къуцӏ-къуцӏ; переименование статьи требует отдельного решения и здесь не выполнялось.

### #040 — кьвагьеро

- RFI: RFI-avru-grammar-77aa5258b6e5
- поле RFI: `senses[0].comment`
- исходный вопрос реквестера: Неправильная форма родительного падежа существительного «стебель»: должно быть «из стебля», а не «из стебла».
- `senses[0].comment`: "полая трубочка из стебла шиповника или ореховой ветки" → "полая трубочка из стебля шиповника или ореховой ветки"
- решение: По уточнению мейнтейнера 2026-10-17: полая трубочка из стебля шиповника или ореховой ветки. Стебло существует как лексический вариант, но здесь выбрано нейтральное стебель/стебля; прежний отказ снят.

### #041 — кьвах-кьвахиялда

- RFI: RFI-avru-grammar-fe6fd95b64d0
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: Stylistic awkwardness bordering on tautology ('грохотом громихал'); consider a more natural verb.
- `senses[0].examples[0].ru`: "с грохотом громихал гром" → "с грохотом громыхал гром"
- решение: По уточнению мейнтейнера 2026-10-17: с грохотом громыхал гром. Исправлена буква и → ы в громыхал; прежнее обоснование отказа не учитывало написание самого глагола.

### #042 — кӏиликӏичӏ

- RFI: RFI-avru-grammar-b080e0d77cb5
- поле RFI: `senses[0].comment`
- исходный вопрос реквестера: gender agreement error: 'крючок' is masculine, so it should be 'с помощью которого', not 'которой'.
- `senses[0].comment`: "с помощью которой закрывают дверь и тому подобное" → "с помощью которого закрывают дверь и тому подобное"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #043 — кӏкӏал-хъитӏалда

- RFI: RFI-avru-grammar-b78d01a87f9b
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: spelling error: 'пресечённом' should be 'пересечённом' given the context of terrain.
- `senses[0].text`: "в сильно пресечённом месте" → "в сильно пересечённом месте"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #044 — лагли

- RFI: RFI-avru-grammar-b04fe5fbeb0b
- поле RFI: `forms[2]`
- исходный вопрос реквестера: Malformed paradigm form missing the stem part.
- `forms[2]`: "ялъул" → "лаглиялъул"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #045 — лайикъаб

- RFI: RFI-avru-grammar-4ca7e2cb2078
- поле RFI: `senses[0].examples[2].ru`
- исходный вопрос реквестера: Missing reflexive suffix '-ся' in participle: should be 'не придерживающийся этикета'.
- `senses[0].examples[2].ru`: "человек, не придерживающий этикета" → "человек, не придерживающийся этикета"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #046 — лайлацӏогьор

- RFI: RFI-avru-grammar-b16ab20a00b4
- поле RFI: `forms[2]`
- исходный вопрос реквестера: Internal paradigm contradiction: with ergative 'лайлацӏогьорас', the genitive must be formed from the oblique stem as 'лайлацӏогьорасул'.
- `forms[2]`: "лайлацӏогьорсул" → "лайлацӏогьорасул"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #047 — лилипут

- RFI: RFI-avru-grammar-345513a773a0
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: typographical or morphological error in the genitive plural form of лилипут (extra syllable -ут-)
- `senses[0].examples[0].av`: "лилипутутазул концерталде ун рукӏана ниж" → "лилипутазул концерталде ун рукӏана ниж"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #048 — лъаб-лъаб

- RFI: RFI-avru-grammar-9ad615f4b94d
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: Orthographic error: the preposition and numeral 'по три' should be written separately without a hyphen.
- `senses[0].text`: "по-три" → "по три"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #050 — лъалеб

- RFI: RFI-avru-grammar-2af3c40359f7
- поле RFI: `senses[0].examples[2].av`
- исходный вопрос реквестера: malformed participle suffix inside example phrase
- `senses[0].examples[2].av`: "лъалелев чиясулгун накъит гьуинаб букӏуна" → "лъалев чиясулгун накъит гьуинаб букӏуна"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #051 — лъороб

- RFI: RFI-avru-grammar-b4c4a2509085
- поле RFI: `senses[0].examples[1].ru`
- исходный вопрос реквестера: Wrong case government: 'положить за' requires the accusative ('за пазуху'), not instrumental.
- `senses[0].examples[1].ru`: "положить за пазухой" → "положить за пазуху"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #052 — мацӏ

- RFI: RFI-avru-grammar-88385234023d
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: case government error: verb 'донести' requires accusative or genitive depending on meaning, but 'донести чего-либо на' is ungrammatical
- `senses[0].examples[0].ru`: "доносить, донести чего-либо на, (с)делать доносы; (по)ябедничать; сплетничать, говорить плохое о человеке; кляузничать, заниматься кляузами; наклеветать, оклеветать кого-либо" → "доносить, донести на кого-либо; (с)делать доносы; (по)ябедничать; сплетничать, говорить плохое о человеке; кляузничать, заниматься кляузами; наклеветать, оклеветать кого-либо"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #053 — михир

- RFI: RFI-avru-grammar-70dc900827b7
- поле RFI: `senses[0].examples[6].comment`
- исходный вопрос реквестера: gender disagreement: participle 'употребляемое' (neuter) does not agree with 'формула' (feminine), should be 'употребляемая'
- `senses[0].examples[6].comment`: "магическая формула, употребляемое слушателем при рассказе кем-либо о своем сновидении" → "магическая формула, употребляемая слушателем при рассказе кем-либо о своем сновидении"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #054 — михъ

- RFI: RFI-avru-grammar-5745760edff1
- поле RFI: `senses[0].examples[18].ru`
- исходный вопрос реквестера: wrong verb form: infinitive 'повиснуть' used instead of 3rd person plural finite verb 'повиснут'
- `senses[0].examples[18].ru`: "да повиснуть твои усы!" → "да повиснут твои усы!"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #055 — моцӏица

- RFI: RFI-avru-grammar-23ceb2bb72d9
- поле RFI: `senses[0].examples[1].av`
- исходный вопрос реквестера: malformed duplicated case suffix inside the word
- `senses[0].examples[1].av`: "тӏубараб моцӏицаица" → "тӏубараб моцӏица"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #056 — мунапикъ

- RFI: RFI-avru-grammar-2b1f348cb5eb
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: Missing conjunction or punctuation between the nouns 'лицемерка' and 'иезуит'.
- `senses[0].text`: "лицемер, лицемерка иезуит" → "лицемер, лицемерка; иезуит"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #057 — нахъ-

- RFI: RFI-avru-grammar-0b0e7ccbcee5
- поле RFI: `pos`
- исходный вопрос реквестера: The entry describes a prefix, but is incorrectly categorized as a verb ('глагол').
- `form`: "инфинитив" → "—"
- `pos`: "глагол" → "—"
- `senses[0].comment`: null → "приставка, образующая сложные глаголы типа"
- `senses[0].text`: "приставка, образующая сложные глаголы типа" → null
- решение: По решению мейнтейнера pos/form — прочерки; морфологическое описание перенесено из text в comment.

### #058 — неграв

- RFI: RFI-avru-grammar-0265f7e15fc9
- поле RFI: `form`
- исходный вопрос реквестера: The headword 'неграв' is singular masculine nominative, not plural ('множественное число').
- `form`: "множественное число" → "именительный"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #059 — ноль

- RFI: RFI-avru-grammar-595fac05475f
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: verb 'равнять' requires the instrumental case ('равняя нолём') or the dative is used with the participle 'равный' ('равный нулю'); 'равняя' as a gerund incorrectly governs the dative.
- `senses[0].examples[0].ru`: "равняя нолю, нулевой" → "равный нолю, нулевой"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #060 — парис

- RFI: RFI-avru-grammar-913f230eac51
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: the word is classified as a noun (существительное) but the glosses are adjectives
- `form`: "именительный" → "—"
- `pos`: "существительное" → "прилагательное"
- решение: Русский перевод сохранён. Исправлены связанные pos/form; формулировка причины RFI о суффиксе не принята как универсальное правило.

### #061 — парсахъ

- RFI: RFI-avru-grammar-687f98a4d819
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: Wrong noun form with numeral: 'верстов' should be 'вёрст'.
- `senses[0].text`: "фарсах, семь верстов" → "фарсах, семь вёрст"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #062 — пенщезе

- RFI: RFI-avru-grammar-7b2c5f356cf3
- поле RFI: `forms[1]`
- исходный вопрос реквестера: Invalid vowel sequence in the verb form.
- `forms[1]`: "пенщоа" → "пенщола"
- решение: Мейнтейнер подтвердил пенщола; исправлена опечатка, присутствующая и в PDF.

### #063 — пионерасул

- RFI: RFI-avru-grammar-48ba3d5a74b2
- поле RFI: `senses[1].examples[0].av`
- исходный вопрос реквестера: malformed or doubly suffixed Avar form 'пионерасуласул'
- `senses[1].examples[0].av`: "пионерасуласул галстук" → "пионерасул галстук"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #064 — рагӏи

- RFI: RFI-avru-grammar-0a52471bdc65
- поле RFI: `senses[0].examples[12].ru`
- исходный вопрос реквестера: case agreement error: 'достаточно' requires genitive case ('достаточно одного слова'), not nominative
- `senses[0].examples[12].ru`: "хорошему человеку достаточно одно слово, доброму коню — один удар кнута" → "хорошему человеку достаточно одного слова, доброму коню — один удар кнута"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #065 — ракӏжубазе

- RFI: RFI-avru-grammar-826661a22458
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: Ошибка глагольного управления: нормативно «войти в доверие к людям» (с предлогом «к»), а не беспредложный родительный падеж.
- `senses[0].examples[0].ru`: "найти общий язык с людьми, войти в доверие людей" → "найти общий язык с людьми, войти в доверие к людям"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #066 — ракӏкъотӏад

- RFI: RFI-avru-grammar-4a100453f28b
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: missing comma before the relative pronoun 'кому'
- `senses[0].text`: "тот кому желают, чтобы сердце вырезали" → "тот, кому желают, чтобы сердце вырезали"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #067 — рахъ-рахъалда

- RFI: RFI-avru-grammar-9450de54263c
- поле RFI: `senses[0].examples[2].ru`
- исходный вопрос реквестера: participle agreement error: 'переселившихся' should be 'переселившихся' modifying 'людьми' requires correct case agreement (людьми, переселившимися).
- `senses[0].examples[2].ru`: "аул, основанный людьми, переселившихся с разных мест" → "аул, основанный людьми, переселившимися с разных мест"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #068 — рахӏат

- RFI: RFI-avru-grammar-bec67510aedf
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: incorrect spelling of 'неспокойный' as separate words
- `senses[0].examples[0].ru`: "беспокойный, не спокойный, тревожный" → "беспокойный, неспокойный, тревожный"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #070 — ректор

- RFI: RFI-avru-grammar-76afa9845a6e
- поле RFI: `senses[0].examples[3].ru`
- исходный вопрос реквестера: gender agreement error: 'ректор' is masculine, so the past tense verb must be masculine 'удостоился', not feminine 'удостоилась'
- `senses[0].examples[3].ru`: «ректор университета удостоилась награды» → «ректор университета была удостоена награды»
- решение: По решению мейнтейнера: «ректор университета была удостоена награды». Женский референт и аварское ректоралъе сохранены; исходная женская форма не была ошибкой согласования, выполнена редакционная переформулировка.

### #071 — рекӏекълъизе

- RFI: RFI-avru-grammar-c649b531f705
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: incorrect pronoun: should be 'не о чем' instead of 'ни о чём' in the impersonal infinitive construction
- `senses[0].examples[0].ru`: "нет никакого основания нам раскаиваться; нам ни о чём сожалеть" → "нет никакого основания нам раскаиваться; нам не о чем сожалеть"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #072 — рухӏалаби

- RFI: RFI-avru-grammar-b2e1513e26f9
- поле RFI: `forms[2]`
- исходный вопрос реквестера: malformed genitive plural suffix: should be рухӏалабазул instead of рухӏалабзул
- `forms[2]`: "рухӏалабзул" → "рухӏалабазул"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #073 — рухӏел

- RFI: RFI-avru-grammar-d3db895fefdf
- поле RFI: `senses[0].examples[1].ru`
- исходный вопрос реквестера: Missing reflexive postfix '-ся': should be 'проголодаешься' in parallel with 'насытишься'.
- `senses[0].examples[1].ru`: "от горя — проголодаешь, от злобы — насытишься" → "от горя — проголодаешься, от злобы — насытишься"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #075 — свердиро

- RFI: RFI-avru-grammar-9cfb355cd102
- поле RFI: `senses[2].comment`
- исходный вопрос реквестера: gender agreement error: relative pronoun 'которого' does not agree with feminine noun 'палочка'
- `senses[2].comment`: "или металлическая; с помощью которого затягивают поклажу верёвкой" → "или металлическая; с помощью которой затягивают поклажу верёвкой"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #076 — сихӏ

- RFI: RFI-avru-grammar-3bf0df8d3e91
- поле RFI: `pos`
- исходный вопрос реквестера: The entry acts as an interjection/noun meaning 'noise/voice' and is labeled 'не склоняется', so pos='прилагательное' is incorrect.
- `form`: "—" → "именительный"
- `pos`: "прилагательное" → "существительное"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #077 — скобка

- RFI: RFI-avru-grammar-54bc5b9d6bc7
- поле RFI: `senses[0].examples[2].av`
- исходный вопрос реквестера: noun-adjective number/class agreement mismatch: singular adjective modifier with plural head noun
- `senses[0].examples[2].av`: "фигураялъулал скобка" → "фигураялъулал скобкаби"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #078 — союзниклъиялъул

- RFI: RFI-avru-grammar-696a95cccb99
- поле RFI: `senses[1].examples[0].av`
- исходный вопрос реквестера: malformed duplicate suffix sequence in the Avar example word
- `senses[1].examples[0].av`: "союзниклъиялъулялъул гьоркьоблъи" → "союзниклъиялъул гьоркьоблъи"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #079 — спортзал

- RFI: RFI-avru-grammar-3d5c8aded0e6
- поле RFI: `senses[0].examples[5].av`
- исходный вопрос реквестера: malformed locative suffix duplication (-лалалда instead of -лалда)
- `senses[0].examples[5].av`: "спортзалалалда къецал тӏоритӏизе" → "спортзалалда къецал тӏоритӏизе"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #080 — сукно

- RFI: RFI-avru-grammar-762f82b2abec
- поле RFI: `senses[0].examples[3].ru`
- исходный вопрос реквестера: wrong government: 'стелить' requires instrumental on the object being covered ('стелить стол сукном' -> 'стилить сукном стол' or 'покрывать стол сукном', as 'стелить' takes the material as the direct object in instrumental and surface in accusative).
- `senses[0].examples[3].ru`: "стелить стол сукном" → "застилать стол сукном"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #081 — тохалчи

- RFI: RFI-avru-grammar-8fd53300127b
- поле RFI: `pos`
- исходный вопрос реквестера: The entry describes a person noun ('человек', 'наблюдатель') and has human-noun plural forms ('тохалчагӏи'), so pos should be 'существительное' instead of 'прилагательное'.
- `form`: "—" → "именительный"
- `pos`: "прилагательное" → "существительное"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #082 — тӏинкъи-тӏинкъиялда

- RFI: RFI-avru-grammar-64da4adf3da7
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: doubled locative suffix in тӏинкъи-тӏинкъиялдаялда
- `senses[0].examples[0].av`: "тӏинкъи-тӏинкъиялдаялда басандана цӏад рукъзабазул тӏохазда" → "тӏинкъи-тӏинкъиялда басандана цӏад рукъзабазул тӏохазда"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #083 — угьинабизе

- RFI: RFI-avru-grammar-4a1ffba0aba4
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: wrong case government: 'чего-либо' should be in the accusative case ('что-либо') as the direct object of 'вышивать'.
- `senses[0].text`: "дать кому-либо вышивать чего-либо; заставлять, заставить кого-либо заниматься вышиванием" → "дать кому-либо вышивать что-либо; заставлять, заставить кого-либо заниматься вышиванием"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #084 — ункъил

- RFI: RFI-avru-grammar-e67a864b0aaf
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: non-standard word form; usually 'четвёрку' is used for a grade
- `senses[0].examples[0].ru`: "я получил четвёртку" → "я получил четвёрку"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #085 — фермерлъиялъул

- RFI: RFI-avru-grammar-47bd22baef17
- поле RFI: `senses[1].examples[0].av`
- исходный вопрос реквестера: doubled genitive suffix on the modifier noun
- `senses[1].examples[0].av`: "фермерлъиялъулялъул магӏишат" → "фермерлъиялъул магӏишат"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #086 — хъутмаччугӏа

- RFI: RFI-avru-grammar-8c74ff801df9
- поле RFI: `pos`
- исходный вопрос реквестера: The entry is labeled as a verb (глагол) with form 'инфинитив', but the headword 'хъутмаччугӏа' ends in a noun suffix and its forms and see_also reference to a noun 'хъутма' indicate it is a noun, not a verb.
- `form`: "инфинитив" → "именительный"
- `pos`: "глагол" → "существительное"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #087 — цементалъул

- RFI: RFI-avru-grammar-c504ec8e4d91
- поле RFI: `senses[1].examples[0].av`
- исходный вопрос реквестера: unusual or malformed genitive suffix stack in the Avar example compound
- `senses[1].examples[0].av`: "цементалъулалъул завод" → "цементалъул завод"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #088 — штатив

- RFI: RFI-avru-grammar-303c1d7f4eea
- поле RFI: `senses[0].examples[1].av`
- исходный вопрос реквестера: Redundant syllable duplication in 'фотоаппаратараталъул'.
- `senses[0].examples[1].av`: "фотоаппаратараталъул штатив" → "фотоаппараталъул штатив"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #089 — январалда

- RFI: RFI-avru-grammar-1015966d7a9d
- поле RFI: `senses[0].examples[0].av`
- исходный вопрос реквестера: Internal suffix repetition in 'январалдалда' violates standard locative formation.
- `senses[0].examples[0].av`: "январалдалда гьавуна дов" → "январалда гьавуна дов"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #090 — январалда

- RFI: RFI-avru-grammar-12e54b4516db
- поле RFI: `senses[0].examples[3].av`
- исходный вопрос реквестера: Internal suffix repetition in 'январалдалдаса' and 'январалдалде' violates standard case formation.
- `senses[0].examples[3].av`: "январалдалдаса январалдалде" → "январалдаса январалде"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #091 — январалда

- RFI: RFI-avru-grammar-178131811e02
- поле RFI: `senses[0].examples[2].av`
- исходный вопрос реквестера: Internal suffix repetition in 'январалдалдаса' violates standard ablative formation.
- `senses[0].examples[2].av`: "январалдалдаса бахъараб" → "январалдаса бахъараб"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #092 — январалда

- RFI: RFI-avru-grammar-cdf4587f7e20
- поле RFI: `senses[0].examples[1].av`
- исходный вопрос реквестера: Internal suffix repetition in 'январалдалде' violates standard lative formation.
- `senses[0].examples[1].av`: "январалдалде щвезегӏан" → "январалде щвезегӏан"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #093 — банкет

- RFI: RFI-avru-grammar-90aab7159876
- поле RFI: `senses[0].examples[3].ru`
- исходный вопрос реквестера: Wrong preposition/case government: in Russian, one participates 'в банке' (preposition 'в' with prepositional case), not 'на банке'.
- `senses[0].examples[3].ru`: "участвовать на банкете" → "участвовать в банкете"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #094 — габанидул

- RFI: RFI-avru-grammar-e91c812ba0b5
- поле RFI: `pos`
- исходный вопрос реквестера: pos is listed as послелог, but the entry is a genitive case form and adjective meaning derived from 'габани'
- `form`: "—" → "родительный"
- `pos`: "послелог" → "существительное"
- `senses[0].genitivefrom`: null → "габани"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #096 — гъалмагъир

- RFI: RFI-avru-grammar-9c4cfc5baccc
- поле RFI: `senses[2].examples[1].ru`
- исходный вопрос реквестера: Verb 'учреждать' usually takes a direct object in the accusative (мятеж), not a separate noun form requiring a different collocation; 'поднимать мятеж' or 'организовывать мятеж' is the standard idiom in Russian.
- `senses[2].examples[1].ru`: "учреждать мятеж" → "организовывать мятеж"
- решение: В RFI отсутствует current; значение «учреждать мятеж» прочитано из текущей статьи и исправлено на «организовывать мятеж».

### #097 — гъира

- RFI: RFI-avru-grammar-255c37d350a1
- поле RFI: `senses[0].examples[3].ru`
- исходный вопрос реквестера: wrong aspect of the Russian infinitive 'покупать' (imperfective) instead of perfective 'купить' after past desire context
- `senses[0].examples[3].ru`: "у него было страстное желание покупать коня" → "у него было страстное желание купить коня"
- решение: По уточнению мейнтейнера 2026-10-17: у него было страстное желание купить коня.

### #100 — какичури

- RFI: RFI-avru-grammar-3f90dca07118
- поле RFI: `senses[1].examples[0].ru`
- исходный вопрос реквестера: wrong case: instrumental 'кем-либо' is inappropriate for the instrument of violation here; should be locative or instrumental of cause.
- `senses[1].examples[0].ru`: "нарушить омовение кем-либо" → "нарушить омовение"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #101 — кинабго

- RFI: RFI-avru-grammar-2aa7aac5db4a
- поле RFI: `forms[2]`
- исходный вопрос реквестера: Typo in form: duplicated vowel 'аа' in 'кинаалъулго' instead of 'киналъулго'.
- `forms[2]`: "кинаалъулго" → "киналъулго"
- `senses[1].forms[1]`: "кинаалъулго" → "киналъулго"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #102 — кинотеатр

- RFI: RFI-avru-grammar-a067b447092d
- поле RFI: `senses[0].examples[2].ru`
- исходный вопрос реквестера: Spelling error in the corresponding Avar example 'кинотеатр алде ине' with a split word, though the Russian translation itself is grammatically fine.
- `senses[0].examples[2].av`: "кинотеатр алде ине" → "кинотеатралде ине"
- решение: Указанный ru корректен; реальная ошибка находится в av того же примера и исправлена там.

### #103 — кунчӏ-кунчӏизабизе

- RFI: RFI-avru-grammar-24c3765139e7
- поле RFI: `forms[1]`
- исходный вопрос реквестера: The forms listed are noun case declensions instead of verb conjugation forms for an infinitive headword.
- `forms`: ["кунчӏ-кунчӏизабизе", "кунчӏ-кунчӏизабас", "кунчӏ-кунчӏизабалъ", "кунчӏ-кунчӏизабасул", "кунчӏ-кунчӏизабалъул", "кунчӏ-кунчӏизабал"] → ["кунчӏ-кунчӏизабизе", "кунчӏ-кунчӏизабула", "кунчӏ-кунчӏизабила", "кунчӏ-кунчӏизабуна", "кунчӏ-кунчӏизабе"]
- решение: В PDF ошибочно напечатаны именные окончания при глагольном заголовке; восстановлена понудительная глагольная парадигма по аналогичной кунчӏизабизе.

### #104 — къвалакьбакӏ

- RFI: RFI-avru-grammar-34332cc87617
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: wrong preposition with 'подмышки': should be 'из подмышек' instead of 'с подмышек'.
- `senses[0].examples[0].ru`: "выдёргивать волосы с подмышек" → "выдёргивать волосы из подмышек"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #105 — лахӏбакьулъ

- RFI: RFI-avru-grammar-86e223996582
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: verb aspect mismatch with the past tense context: 'попадал' is imperfective, whereas a single completed shot in the past ('речӏчӏана') calls for the perfective 'попал'.
- `senses[0].examples[0].ru`: "он попадал из ружья точно в цель" → "он попал из ружья точно в цель"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #106 — къула-ворхизе

- RFI: RFI-avru-grammar-c5a2e200ed6d
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: case government error: 'приученный' requires preposition 'к' ('приученный к хорошим манерам')
- `senses[0].examples[0].ru`: "не приученный хорошим манерам; не умеющий ни поклоняться ни выпрямляться" → "не приученный к хорошим манерам; не умеющий ни поклоняться, ни выпрямляться"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #107 — маскарад

- RFI: RFI-avru-grammar-fe0a01e9df65
- поле RFI: `senses[0].examples[1].ru`
- исходный вопрос реквестера: wrong preposition/case: verb 'участвовать' requires preposition 'в' with prepositional case ('участвовать в маскараде'), not 'на'.
- `senses[0].examples[1].ru`: "участвовать на маскараде" → "участвовать в маскараде"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #108 — митинг

- RFI: RFI-avru-grammar-6f7c02944c5a
- поле RFI: `senses[0].examples[2].ru`
- исходный вопрос реквестера: Wrong preposition: 'участвовать' governs 'в', not 'на' ('участвовать в митинге').
- `senses[0].examples[2].ru`: "участвовать на митинге" → "участвовать в митинге"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #109 — мехтел

- RFI: RFI-avru-grammar-3b200e6771fe
- поле RFI: `senses[1].examples[0].ru`
- исходный вопрос реквестера: incorrect comma placement before 'не употреблять'
- `senses[1].examples[0].ru`: "я поклялся, не употреблять спиртных напитков" → "я поклялся не употреблять спиртных напитков"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #110 — микьир

- RFI: RFI-avru-grammar-1e32e5740b1f
- поле RFI: `senses[0].examples[1].ru`
- исходный вопрос реквестера: Wrong grammatical number: object of 'собирать' should be in plural ('собирать персики') or with a partitive meaning corresponding to the plural/mass sense.
- `senses[0].examples[1].ru`: "собирать персик" → "собирать персики"
- решение: По уточнению мейнтейнера 2026-10-17: собирать персики.

### #111 — микьиркурак

- RFI: RFI-avru-grammar-799db1a56e9f
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: Wrong case and number form for the noun after 'сорт': should be genitive plural ('сорт абрикосов').
- `senses[0].text`: "сорт абрикос" → "сорт абрикосов"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #112 — налбек

- RFI: RFI-avru-grammar-66df8749fb2f
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: preposition 'на' is required instead of 'в' with the noun 'блюдечко'.
- `senses[0].examples[0].ru`: "поставь стакан в блюдечко" → "поставь стакан на блюдечко"
- решение: По уточнению мейнтейнера 2026-10-17: поставь стакан на блюдечко.

### #114 — партконференция

- RFI: RFI-avru-grammar-e5c0533bb16d
- поле RFI: `senses[0].examples[2].ru`
- исходный вопрос реквестера: wrong case government: 'участвовать' requires preposition 'в' with prepositional case, not 'на'.
- `senses[0].examples[2].ru`: "участвовать на партконференции" → "участвовать в партконференции"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #115 — партсобрание

- RFI: RFI-avru-grammar-1e2927f5d4cb
- поле RFI: `senses[0].examples[1].ru`
- исходный вопрос реквестера: wrong case government: 'участвовать' requires preposition 'в' with prepositional case, not 'на'.
- `senses[0].examples[1].ru`: "участвовать на партсобрании" → "участвовать в партсобрании"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #117 — румын

- RFI: RFI-avru-grammar-b0e62e2d1673
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: pos is 'существительное', but the sense is an adjective meaning 'румынский'
- `form`: "именительный" → "—"
- `pos`: "существительное" → "прилагательное"
- решение: Русский перевод сохранён. Исправлены связанные pos/form; формулировка причины RFI о суффиксе не принята как универсальное правило.

### #118 — семинар

- RFI: RFI-avru-grammar-c6f211d777a0
- поле RFI: `senses[0].examples[3].ru`
- исходный вопрос реквестера: wrong preposition/case: 'участвовать в семинаре' requires preposition 'в' with prepositional case, not 'на'.
- `senses[0].examples[3].ru`: "участвовать на семинаре" → "участвовать в семинаре"
- решение: Подтверждённое несоответствие; исправлено в источнике.

### #120 — хӏелеко

- RFI: RFI-avru-grammar-8868fe6ad608
- поле RFI: `senses[0].examples[0].ru`
- исходный вопрос реквестера: typographical/grammatical error in Russian translation: 'покукарекал' is not a standard Russian word (should be 'покукарекал' -> 'прокукарекал' or 'закукарекал').
- `senses[0].examples[0].ru`: "петух покукарекал" → "петух прокукарекал"
- решение: По уточнению мейнтейнера 2026-10-17: петух прокукарекал.

### #121 — цӏогьормахӏав

- RFI: RFI-avru-grammar-32450957acfb
- поле RFI: `senses[0].text`
- исходный вопрос реквестера: headword is a noun form (indicated by noun suffix -ав), but glossed as an adjective 'вороватый'
- `form`: "именительный" → "—"
- `pos`: "существительное" → "прилагательное"
- решение: Русский перевод сохранён. Исправлены связанные pos/form; формулировка причины RFI о суффиксе не принята как универсальное правило.

## Отклонено

### #007 — байгъуш

- поле: `senses[0].examples[0].av`
- текст: «кидалъизегӏан мун байгъушлъун вукӏинев?»
- исходный вопрос реквестера: potential agreement or participial suffix discrepancy in the Avar sentence 'кидалъизегӏан мун байгъушлъун вукӏинев?'
- ответ: Форма вукӏинев согласована с мужским классом и употреблена в вопросительной конструкции. Замечание не указывает конкретной доказанной ошибки и не предлагает корректной замены; оснований менять пример нет.

### #008 — басра

- поле: `senses[0].examples[4].ru`
- текст: «Долгой тебе жизни, Алил Магомед, Не издевайся оттого, что я в руках твоих»
- исходный вопрос реквестера: wrong preposition with 'издеваться': should be 'издеваться над', not 'издеваться от'
- ответ: Оттого, что — причинная конструкция «потому, что», а не управление «издеваться от». Текст — перевод фольклорной строки; обязательного дополнения «над кем» здесь нет.

### #009 — бегизабизе

- поле: `senses[1].examples[0].ru`
- текст: «больного уложили в больницу»
- исходный вопрос реквестера: Missing preposition 'в': should be 'уложили в больницу', not 'уложили больницу'.
- ответ: Предлог в уже присутствует в точном тексте RFI: «больного уложили в больницу». Требуемая реквестером формулировка совпадает с текущей; исправлять нечего.

### #028 — как

- поле: `senses[0].examples[11].av`
- текст: «какие гӏуж щвана»
- исходный вопрос реквестера: possible typographical error in the Avar example, where 'какие' appears instead of 'какил' or 'как'
- ответ: По подтверждению мейнтейнера какие — корректная дательная форма слова как (кому/чему), а не русское местоимение и не опечатка вместо какил. Исходное какие гӏуж щвана восстановлено; русский перевод не менялся.

### #049 — лъаббагьаб

- поле: `senses[0].text`
- текст: «четырёхгодовалый, в возрасте от четырёх до пяти лет»
- исходный вопрос реквестера: Mismatched meaning: the Avar word root starts with 'лъаб-' (three), but the Russian translation says 'четырёхгодовалый' (four-year-old) instead of three.
- ответ: В PDF (страница файла 949) явно напечатаны «четырёхгодовалый, в возрасте от четырёх до пяти лет» и оба примера с четырёхгодовалыми животными. Возрастной термин нельзя переводить заново только по числовому корню лъаб-. Доказательства ошибки источника нет.

### #069 — ревизор

- поле: `senses[0].examples[2].av`
- текст: «дой ревизорлъун хӏалтӏулей йиго»
- исходный вопрос реквестера: possible typo in pronoun 'дой', usually 'дюб' or 'дун' or demonstrative pronoun 'дон'/'дуй' depending on dialect, but likely intended as 'дун' or 'дун яги гьей'.
- ответ: Дой — корректное указательное местоимение женского грамматического класса («она/та»). Оно согласовано с хӏалтӏулей йиго; замена на дун/дов изменила бы лицо или пол референта.

### #074 — сваказабизе

- поле: `senses[0].examples[0].av`
- текст: «берал сваказаризе»
- исходный вопрос реквестера: mismatch between stem 'сваказаб-' and example form 'сваказаризе'
- ответ: В сваказаризе представлен показатель множественного класса р, согласованный с берал («глаза»). Отличие от словарной формы на -забизе не является опечаткой.

### #095 — грек

- поле: `pos`
- текст: «прилагательное»
- исходный вопрос реквестера: Word functions as a noun modifier/noun in examples like 'грек мацӏ', but pos is incorrectly labeled as adjective while lacking adjective morphology.
- ответ: В этой статье грек означает «греческий», употреблено как неизменяемое определение в грек мацӏ. Аварские заимствованные прилагательные не обязаны иметь окончание -аб. Название лица представлено отдельной статьёй грекав.

### #098 — гьудулавчи

- поле: `senses[0].text`
- текст: «мил человек»
- исходный вопрос реквестера: Typo in Russian gloss: 'мил' should be 'милй' or 'милый'.
- ответ: Мил человек — нормативное традиционное обращение с кратким прилагательным, не опечатка вместо милый. Оно подтверждается и примером «послушай-ка, мил человек» в PDF. Справка: https://gramota.ru/poisk?mode=spravka&query=%D0%BC%D1%8E%D1%81%D0%BB .

### #099 — диктатура

- поле: `senses[0].examples[2].ru`
- текст: «народ долго не терпит диктатуру»
- исходный вопрос реквестера: wrong case: verb 'терпеть' with negation typically governs the genitive case ('диктатуры'), not accusative.
- ответ: При отрицании в русском возможны и родительный, и винительный падежи. «Не терпит диктатуру» с конкретным прямым дополнением грамматически допустимо; обязательной замены на «диктатуры» нет.

### #113 — папирос

- поле: `senses[0].text`
- текст: «папироса»
- исходный вопрос реквестера: mismatch with headword: headword is masculine 'папирос', but the sense text is feminine 'папироса'
- ответ: Папирос — аварское заглавное слово; папироса — его русский перевод. Род и окончание заимствованного аварского слова не обязаны совпадать с русским эквивалентом. Это не русско-русский словарь.

### #116 — релълъен

- поле: `senses[0].text`
- текст: «сходство, схожесть, подобие; одинаковость, однородность; тождество, тожество»
- исходный вопрос реквестера: spelling error in Russian: 'тожество' should be spelled 'тождество'
- ответ: Тожество — зафиксированный устаревший вариант слова тождество, а не OCR-пропуск д. В перечислении уже есть и современный вариант; удалять историческую лексику не нужно. Русский орфографический словарь: https://gramota.ru/poisk?dicts%5B0%5D=71&mode=slovari&query=%D1%82%D0%BE%D0%B6%D0%B4%D0%B5%D1%81%D1%82%D0%B2%D0%BE&simple=0 .

### #119 — сухари

- поле: `senses[0].examples[0].ru`
- текст: «затверделые сухари»
- исходный вопрос реквестера: Incorrect adjective form; 'затверделые' should be 'затвердевшие' for this participle.
- ответ: Затверделый — самостоятельное нормативное прилагательное («ставший твёрдым»), а не испорченное причастие затвердевший. Оно фиксируется академическим орфографическим словарём: https://ruslang.ru/sites/default/files/doc/normativnyje_slovari/orfograficheskij_slovar.pdf .

### #122 — чайгъуд

- поле: `senses[0].examples[0].av`
- текст: «чайгъудалъубе тӏун гьекъе дару»
- исходный вопрос реквестера: locative suffix combination in 'чайгъудалъубе' appears malformed for standard case attachment.
- ответ: Чайгъудалъубе — корректная пространственная форма с направлением внутрь; сочетание алъубе само по себе не является повтором падежа. В тексте лекарство наливают в ложку и выпивают; доказанной морфологической ошибки нет.

### #123 — чайдан

- поле: `senses[0].examples[0].av`
- текст: «чайданалъубе лъим тӏе»
- исходный вопрос реквестера: locative suffix combination in 'чайданалъубе' appears malformed for standard case attachment.
- ответ: Чайданалъубе — корректная пространственно-направительная форма «в чайник». Сочетание алъубе не является автоматически ошибочным удвоением суффикса.

### #124 — щвантӏихчи

- поле: `senses[0].text`
- текст: «на дудке игрец»
- исходный вопрос реквестера: unnatural archaic inversion 'на дудке игрец' instead of standard Russian 'играющий на дудке' or 'дудочник'
- ответ: Игрец — существующее слово со значением играющего на музыкальном инструменте; инверсия «на дудке игрец» допустима в краткой словарной дефиниции. Архаичность и стилистическая необычность не делают перевод ошибочным.

## Предложения вне RFI

Морфемы и переименование къуцӏ: reports/2026-10-16-av-ru-morphemes-and-quts-review.md; не применены.
