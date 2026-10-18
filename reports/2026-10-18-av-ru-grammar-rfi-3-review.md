> Раунд завершён по апруву мейнтейнера: 79 исправленных RFI, 7 отклонённых, нерешённых нет.
> Исходные предложения ниже сохранены для истории; это не итоговые решения.
> Пункты 044/045 исправлены на зангалмачуяз/зангалмачуязул; 021/026 — pos/form «—»;
> 053 — икъунатал; 075 — рукӏкӏбузул; 086 — хӏуцӏихарица.
> Итоговые решения и точные изменения: [changelog](../changelog/2026-10-18-av-ru-grammar-rfi-3.md).

# av-ru: grammar RFI, партия 3 — 2026-10-18

Статус: предложения; словарь ещё не изменён. Номера — строки входного av-ru-grammar-rfi.jsonl.

72 предложений исправить; 9 отклонений; 5 вопросов мейнтейнеру.

После одобрения: править data/av-ru.2006.jsonl и пересобрать data/av-ru.jsonl. Входной RFI не менять и не коммитить.

## Предлагаю исправить

### #001 — алжан

- поле: `senses[0].examples[5].ru`
- сейчас: «да станет он из, тех кому предначертано попасть в рай»
- исходный вопрос реквестера: unnecessary comma before 'тех'
- решение: да станет он из тех, кому предначертано попасть в рай
- rfi: RFI-avru-grammar-0d3b2460f199

### #002 — бакъвачӏагӏа

- поле: `pos`
- сейчас: «прилагательное»
- исходный вопрос реквестера: The headword means 'thick buza' (a noun) and is inflected with noun cases in the 'forms' field, so pos should be существительное instead of прилагательное.
- решение: pos: существительное; form: именительный
- rfi: RFI-avru-grammar-c390b8dc4b22

### #004 — беэнлъизабизе

- поле: `senses[1].text`
- сейчас: «(с)делать (землю) тучным; удобрять, удобрить»
- исходный вопрос реквестера: gender agreement error: 'тучным' should be feminine 'тучной' to agree with 'землю'
- решение: (с)делать (землю) тучной; удобрять, удобрить
- rfi: RFI-avru-grammar-ca953d573a78

### #005 — биччанте

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: part of speech is incorrectly labeled as noun for a particle
- решение: pos: частица; form: —
- rfi: RFI-avru-grammar-dac0b32c983a

### #006 — буран

- поле: `senses[0].examples[3].av`
- сейчас: «бурананалъ гӏи гъурана»
- исходный вопрос реквестера: malformed form in example: 'бурананалъ' appears to have a duplicated suffix sequence compared to headword 'буран'.
- решение: бураналъ гӏи гъурана
- rfi: RFI-avru-grammar-ef9c98e512a0

### #007 — ва

- поле: `senses[0].examples[0].ru`
- сейчас: «о, этого я давно видел!»
- исходный вопрос реквестера: wrong case: verb 'видеть' with a direct object requires the accusative case ('этого' is genitive/accusative animate, should be inanimate accusative 'это').
- решение: о, это я давно видел!
- rfi: RFI-avru-grammar-ae1dac9854b5

### #008 — варани

- поле: `senses[0].examples[3].av`
- сейчас: «варанялтӏасаса рещтӏине»
- исходный вопрос реквестера: malformed suffix repetition: 'варанялтӏасаса' contains a duplicated superessive-elative suffix.
- решение: вараниялтӏаса рещтӏине
- rfi: RFI-avru-grammar-88c2f2352728

### #009 — вас

- поле: `senses[0].examples[3].ru`
- сейчас: «да вырастут мальчики, да становятся учёными»
- исходный вопрос реквестера: mismatched verb tense/aspect in coordinate clauses; 'становятся' should be 'станут' to match the imperative/future sense of 'гӏеги'.
- решение: да вырастут мальчики, да станут учёными
- rfi: RFI-avru-grammar-87cd291d7bf6

### #012 — гачигвенд

- поле: `forms[4]`
- сейчас: «гачигвндил»
- исходный вопрос реквестера: spelling typo in form: missing vowel -а- in -гвндил
- решение: гачигвандил (отдельная статья PDF, с. 343)
- rfi: RFI-avru-grammar-1022783beb43

### #013 — гел

- поле: `senses[0].text`
- сейчас: «половник, поварёшка разливательная ложка (больших размеров); черпак; ковш; ушат»
- исходный вопрос реквестера: missing conjunction or punctuation between synonyms 'поварёшка' and 'разливательная ложка'
- решение: половник, поварёшка, разливательная ложка (больших размеров); черпак; ковш; ушат
- rfi: RFI-avru-grammar-9ea1faf123dc

### #014 — гургинлъизе

- поле: `senses[1].examples[1].av`
- сейчас: «кьаралъиялъ гургинлълъун руго бачал»
- исходный вопрос реквестера: typographical cluster 'лълъ' in 'гургинлълъун' is malformed
- решение: кьаралъиялъ гургинлъун руго бачал
- rfi: RFI-avru-grammar-a9e1bc472dfa

### #015 — гуржи

- поле: `pos`
- сейчас: «частица»
- исходный вопрос реквестера: The word functions as an adjective/noun modifier ('грузинский') rather than a particle; pos should be прилагательное.
- решение: pos: прилагательное; form: —
- rfi: RFI-avru-grammar-6a70963af40d

### #016 — гуро

- поле: `pos`
- сейчас: «глагол»
- исходный вопрос реквестера: The word 'гуро' is a negative particle/copula particle, not a verb, despite being listed with pos='глагол'.
- решение: pos: частица; form: —; только статья гуро «нет, не»
- rfi: RFI-avru-grammar-7d2d32901703

### #017 — гъапусик

- поле: `senses[0].examples[0].ru`
- сейчас: «у входа в пещеру голубь снесла два яйца»
- исходный вопрос реквестера: gender agreement error: noun 'голубь' is masculine, so the verb should be 'снесло' or the subject should be feminine ('голубка')
- решение: у входа в пещеру голубка снесла два яйца
- rfi: RFI-avru-grammar-a32d8cbfc6dc

### #018 — гьатӏаналде

- поле: `senses[0].examples[0].av`
- сейчас: «гьатӏаналдеалде нахъ тӏамун тана бертин»
- исходный вопрос реквестера: malformed or duplicated suffix element in гьатӏаналдеалде
- решение: гьатӏаналде нахъ тӏамун тана бертин
- rfi: RFI-avru-grammar-47ec1269568d

### #019 — гӏабид

- поле: `forms[2]`
- сейчас: «гӏабидсул»
- исходный вопрос реквестера: Genitive form contains a metathesis or incorrect suffix order; expected гӏабидасул.
- решение: гӏабидасул — также в sense.forms
- rfi: RFI-avru-grammar-986463e4e4ce

### #020 — гӏадат

- поле: `senses[0].examples[2].ru`
- сейчас: «готовность пожертвовать себя за кунака превратилась у горцев в обычай»
- исходный вопрос реквестера: wrong case governance: reflexive pronoun 'себя' should be in instrumental case ('собой') after 'пожертвовать', not accusative
- решение: готовность пожертвовать собой за кунака превратилась у горцев в обычай
- rfi: RFI-avru-grammar-b02a87c47fc8

### #022 — гӏалимчӏужу

- поле: `forms[3]`
- сейчас: «гӏалимчӏужугӏалимзаби»
- исходный вопрос реквестера: The listed plural form is a concatenation of two different words instead of a proper plural paradigm.
- решение: гӏалимзаби
- rfi: RFI-avru-grammar-37cebfc2aeb8

### #023 — гӏарзахъдизабизе

- поле: `senses[0].text`
- сейчас: «способствовать тому, чтобы часто жаловался на кого-что-либо; заставлять, заставить кого-либо чтобы часто жаловался»
- исходный вопрос реквестера: missing comma before 'чтобы' in the subordinate clause
- решение: способствовать тому, чтобы часто жаловался на кого-что-либо; заставлять, заставить кого-либо, чтобы часто жаловался
- rfi: RFI-avru-grammar-ed57aa7b3be0

### #024 — гӏасилъизе

- поле: `senses[0].examples[1].av`
- сейчас: «инсул насихӏатазде гӏасилъана он»
- исходный вопрос реквестера: Mixing the Russian pronoun 'он' into an Avar example sentence creates a hybrid structure ungrammatical in standard Avar.
- решение: инсул насихӏатазде гӏасилъана — убрать русское «он», попавшее из перевода; не придумывать аварское местоимение
- rfi: RFI-avru-grammar-3a8df2a5012f

### #025 — гӏезе

- поле: `senses[0].examples[1].ru`
- сейчас: «дерево ещё вырастит»
- исходный вопрос реквестера: Wrong verb aspect/form: intransitive verb 'вырасти' cannot be in the active future form 'вырастит' here; it should be intransitive 'вырастет'.
- решение: дерево ещё вырастет
- rfi: RFI-avru-grammar-ab21ab71f6ba

### #027 — гӏунгутӏи

- поле: `forms[1]`
- сейчас: «гӏунгутӏииялъ»
- исходный вопрос реквестера: Malformed stem extension with double 'ii' before the case suffix.
- решение: гӏунгутӏиялъ; также гӏунгутӏииялъул → гӏунгутӏиялъул; только статья «нехватка чего-либо»
- rfi: RFI-avru-grammar-bcbd991a96ae

### #028 — дарагун

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: The word has an adjective meaning 'драгунский' but is incorrectly labeled as a noun.
- решение: pos: прилагательное; form: —
- rfi: RFI-avru-grammar-937272a759e4

### #029 — дие

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: Форма местоимения 'дун' ('мне') ошибочно помечена как существительное вместо местоимения.
- решение: pos: местоимение; form: дательный сохранить
- rfi: RFI-avru-grammar-bc1a9bdb6d37

### #030 — добго

- поле: `senses[0].comment`
- сейчас: «о имени существительном Ⅲ грамматического класса»
- исходный вопрос реквестера: Preposition error: 'об' should be used before a vowel instead of 'о' ('об имени').
- решение: об имени существительном Ⅲ грамматического класса
- rfi: RFI-avru-grammar-b46dba9af3e1

### #031 — добегӏан

- поле: `senses[0].text`
- сейчас: «в стороне, в отдалении; на определённом расстоянии; по близости там, поближе туда (к указанному месту)»
- исходный вопрос реквестера: Spelling error: the adverb 'поблизости' should be written as one word.
- решение: в стороне, в отдалении; на определённом расстоянии; поблизости там, поближе туда (к указанному месту)
- rfi: RFI-avru-grammar-f13326bfd755

### #032 — долда

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: Слово является падежной формой указательного местоимения (доб/дой), а не существительным; часть речи должна быть «местоимение».
- решение: pos: местоимение; form: местный сохранить
- rfi: RFI-avru-grammar-779ff2347119

### #033 — дугъдазе

- поле: `senses[1].text`
- сейчас: «не поддаваться, не прислушиваться мнению других; крепко держаться на своём»
- исходный вопрос реквестера: Управление глагола «прислушиваться»: требуется предлог «к» с дательным падежом («прислушиваться к мнению»).
- решение: не поддаваться, не прислушиваться к мнению других; крепко держаться на своём
- rfi: RFI-avru-grammar-8d7d4d193f13

### #034 — дуз

- поле: `pos`
- сейчас: «глагол»
- исходный вопрос реквестера: слово «дуз» является наречием (ср. «дузаб»), а не глаголом в инфинитиве
- решение: pos: наречие; form: —
- rfi: RFI-avru-grammar-baf6c9610322

### #035 — дуниялалъулго

- поле: `senses[0].text`
- сейчас: «вселенская»
- исходный вопрос реквестера: Wrong grammatical gender ending: adjective gloss citation form should be masculine ('вселенский') rather than feminine.
- решение: вселенский
- rfi: RFI-avru-grammar-f9e95c60fa88

### #036 — ечӏчӏарухъан

- поле: `forms[3]`
- сейчас: «реччӏарухъаби»
- исходный вопрос реквестера: Internal spelling contradiction in plural form: 'реччӏарухъаби' uses 'ччӏ' instead of 'чӏчӏ' matching the headword 'ечӏчӏарухъан' and see_also reference.
- решение: речӏчӏарухъаби — начальное р сохранить: множественный грамматический класс
- rfi: RFI-avru-grammar-ebb8a77a92ad

### #037 — жагьил

- поле: `forms[2]`
- сейчас: «жагьилсул»
- исходный вопрос реквестера: mismatched oblique stem suffix: expected 'жагьиласул' following ergative 'жагьилас'
- решение: жагьиласул
- rfi: RFI-avru-grammar-bd955de84eb1

### #038 — жазаир

- поле: `forms[3]`
- сейчас: «жазаирл»
- исходный вопрос реквестера: Typographical error in plural form: 'жазаирл' is missing the vowel 'а' (should be 'жазаирал').
- решение: жазаирал
- rfi: RFI-avru-grammar-45133f89c387

### #039 — жакъаялде

- поле: `senses[1].examples[0].ru`
- сейчас: «на сегодня хватит эта еда»
- исходный вопрос реквестера: wrong case: 'хватит' requires the genitive ('этой еды'), not the nominative ('эта еда')
- решение: на сегодня хватит этой еды
- rfi: RFI-avru-grammar-17a77585d4f5

### #041 — жубай-бахъи

- поле: `senses[0].examples[0].ru`
- сейчас: «ученик имел способности по сложению и вычитанию»
- исходный вопрос реквестера: Неправильное предложное управление: существительное «способности» требует предлога «к» («способности к сложению»), а не «по».
- решение: ученик имел способности к сложению и вычитанию
- rfi: RFI-avru-grammar-89aa5f90fad4

### #042 — жугьа

- поле: `senses[0].examples[1].ru`
- сейчас: «по-словно, по каждому слову»
- исходный вопрос реквестера: орфографическая ошибка: наречие «пословно» пишется слитно, без дефиса
- решение: пословно, по каждому слову
- rfi: RFI-avru-grammar-a9b0068b5fae

### #043 — загьла

- поле: `senses[0].examples[0].ru`
- сейчас: «измориться; изнемогаться; замаяться; замотаться»
- исходный вопрос реквестера: Non-existent reflexive form 'изнемогаться' (correct verb is 'изнемогать').
- решение: измориться; изнемогать; замаяться; замотаться
- rfi: RFI-avru-grammar-7768d378a2f4

### #046 — занкӏун

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: The word is an adverb meaning 'до отказа, битком', not a noun.
- решение: pos: наречие; form: —
- rfi: RFI-avru-grammar-58a9ca3386c5

### #047 — запас

- поле: `senses[0].examples[2].ru`
- сейчас: «запас сена хватит на зиму»
- исходный вопрос реквестера: Wrong case government with 'хватит': requires genitive ('запаса сена хватит'), not nominative.
- решение: запаса сена хватит на зиму
- rfi: RFI-avru-grammar-ce5754a1dbdc

### #048 — заседание

- поле: `senses[0].examples[2].av`
- сейчас: «заседание ялда гӏахьаллъизе»
- исходный вопрос реквестера: Spurious space and incorrect stem in 'заседание ялда' instead of locative form 'заседаниялда'.
- решение: заседаниялда гӏахьаллъизе
- rfi: RFI-avru-grammar-dfe30a74461b

### #049 — звархун

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: 'звархун' functions as an adverb/intensifier modifying verbs and participles, not a noun.
- решение: pos: наречие; form: —
- rfi: RFI-avru-grammar-cfb9cf8bebc4

### #050 — зирун

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: 'зирун' functions as an adverb meaning 'полностью' (modifying verbs in all examples), not a noun.
- решение: pos: наречие; form: —
- rfi: RFI-avru-grammar-98366cdae77e

### #051 — зурма

- поле: `senses[0].examples[4].av`
- сейчас: «зурмхъ гӏенеккизе»
- исходный вопрос реквестера: Missing oblique stem vowel in 'зурмхъ' (broken cluster), expected 'зурмихъ'.
- решение: зурмихъ гӏенеккизе
- rfi: RFI-avru-grammar-e6203059575f

### #052 — икъбал

- поле: `senses[0].examples[3].comment`
- сейчас: «букв. не имеющий везения, удачу, счастье»
- исходный вопрос реквестера: Case coordination error after negated participle 'не имеющий': coordinated nouns should be in the genitive ('удачи, счастья') matching 'везения', not accusative.
- решение: букв. не имеющий везения, удачи, счастья
- rfi: RFI-avru-grammar-acf3c03e14f9

### #054 — иливаш

- поле: `senses[0].examples[1].av`
- сейчас: «иливашашалда гьоркьоб гӏахьаллъи гьабизе»
- исходный вопрос реквестера: Apparent typographical duplication of the syllable 'ша' in 'иливашашалда' (broken word structure; expected 'иливашалда').
- решение: иливашалда гьоркьоб гӏахьаллъи гьабизе
- rfi: RFI-avru-grammar-898ab244ac28

### #055 — имгӏаласул

- поле: `senses[1].examples[1].av`
- сейчас: «имгӏаласуласул яс»
- исходный вопрос реквестера: erroneously duplicated genitive suffix '-асул-'; should be 'имгӏаласул яс'
- решение: имгӏаласул яс
- rfi: RFI-avru-grammar-311c87534b95

### #056 — имгӏаласул

- поле: `senses[1].examples[0].av`
- сейчас: «имгӏаласуласул вас»
- исходный вопрос реквестера: erroneously duplicated genitive suffix '-асул-'; should be 'имгӏаласул вас'
- решение: имгӏаласул вас
- rfi: RFI-avru-grammar-9ee754f27b8c

### #057 — ине

- поле: `senses[5].examples[1].ru`
- сейчас: «неходовой двугривенный, не принимающий [в торговых точках] рубль»
- исходный вопрос реквестера: Wrong participle voice: active 'не принимающий' should be passive 'не принимаемый'.
- решение: неходовой двугривенный, не принимаемый [в торговых точках] рубль
- rfi: RFI-avru-grammar-edc02cedf5fa

### #058 — инсухъеяв

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: Слово согласуется по грамматическим классам (инсухъеяв / инсухъеяй), выступает определением и имеет значение свойства («по отцовской линии»), поэтому частью речи должно быть «прилагательное».
- решение: pos: прилагательное; form: —
- rfi: RFI-avru-grammar-1149c9d81768

### #059 — интендантасулаб

- поле: `senses[0].examples[0].av`
- сейчас: «интендантасулабаб хъулухъ»
- исходный вопрос реквестера: Dittography / morphological error in adjective form: 'интендантасулабаб' contains a duplicated neuter agreement suffix '-аб' (expected 'интендантасулаб').
- решение: интендантасулаб хъулухъ
- rfi: RFI-avru-grammar-2ba0e2957653

### #060 — кабинеталъулаб

- поле: `senses[0].examples[2].av`
- сейчас: «кабинеталъулабл столал»
- исходный вопрос реквестера: Typo in the suffix: 'кабинеталъулабл' contains an extra 'л' before the space.
- решение: кабинеталъулал столал — множественная форма из ~л в PDF, с. 704, а не кабинеталъулаб
- rfi: RFI-avru-grammar-b7f3c047bd5b

### #061 — къватӏиракь

- поле: `senses[0].text`
- сейчас: «чужбина чужой край, чужая сторона»
- исходный вопрос реквестера: missing conjunction or punctuation between synonyms in the definition
- решение: чужбина; чужой край, чужая сторона
- rfi: RFI-avru-grammar-1e82dd3a7596

### #062 — кьандиб

- поле: `senses[0].examples[1].ru`
- сейчас: «струсить зажать хвост между ног»
- исходный вопрос реквестера: missing punctuation between consecutive verb phrases
- решение: струсить; зажать хвост между ног
- rfi: RFI-avru-grammar-a0d401c5cb85

### #063 — кьвар-кьвари

- поле: `senses[0].examples[0].ru`
- сейчас: «с неба раздалось трахтанье вертолёта»
- исходный вопрос реквестера: spelling error: 'трахтанье' should be spelled 'тарахтенье'.
- решение: с неба раздалось тарахтенье вертолёта
- rfi: RFI-avru-grammar-c4afcbe035df

### #064 — лъабгоялде

- поле: `senses[0].examples[2].av`
- сейчас: «лъабгоялдеде щвезегӏан рикӏкӏине»
- исходный вопрос реквестера: malformed repetition of the case suffix in 'лъабгоялдеде', should be 'лъабгоялде'.
- решение: лъабгоялде щвезегӏан рикӏкӏине
- rfi: RFI-avru-grammar-c186284bad1a

### #065 — магӏарул

- поле: `pos`
- сейчас: «существительное»
- исходный вопрос реквестера: The word is an adjective ('горный', 'аварский'), but is mislabeled as a noun ('существительное').
- решение: pos: прилагательное; form: —
- rfi: RFI-avru-grammar-8e424192696c

### #066 — манзилхалатав

- поле: `senses[0].text`
- сейчас: «терпеливый, сумеющий сдержаться»
- исходный вопрос реквестера: Глагол совершенного вида «суметь» не образует действительного причастия настоящего времени; форма «сумеющий» грамматически неверна.
- решение: терпеливый, умеющий сдержаться — редакционное предложение, без категорического утверждения, что форма «сумеющий» не существует
- rfi: RFI-avru-grammar-2ecc255e8aa7

### #067 — мискинчи

- поле: `senses[0].examples[1].ru`
- сейчас: «раньше, чем о смерти бедняка, услышишь, что у имущественного палец укололся о занозу»
- исходный вопрос реквестера: substantivized adjective 'имущественного' requires a noun head or a plural form like 'имущего' to mean 'the propertied person'.
- решение: раньше, чем о смерти бедняка, услышишь, что у имущего палец укололся о занозу
- rfi: RFI-avru-grammar-817f0468c5a7

### #068 — назир

- поле: `senses[0].text`
- сейчас: «управляющий чего-либо»
- исходный вопрос реквестера: Ошибка падежного управления: существительное «управляющий» управляет творительным падежом («чем-либо»), а не родительным («чего-либо»).
- решение: управляющий чем-либо
- rfi: RFI-avru-grammar-115e764994c5

### #069 — нухтӏадулав

- поле: `senses[0].text`
- сейчас: «посильной»
- исходный вопрос реквестера: incorrect adjective form used as a noun; should be 'посыльный'
- решение: посыльный
- rfi: RFI-avru-grammar-0e397842ddf5

### #070 — питна

- поле: `senses[2].examples[0].ru`
- сейчас: «скандал, (по)скандалить; интриговать; устроить»
- исходный вопрос реквестера: uncoordinated fragment 'устроить' missing a direct object.
- решение: интриговать; устроить скандал, (по)скандалить — восстановить порядок по PDF, с. 1091
- rfi: RFI-avru-grammar-056dffc0c1fd

### #073 — рояль

- поле: `senses[0].examples[0].ru`
- сейчас: «играть, сыграть на рояли»
- исходный вопрос реквестера: Wrong prepositional case form for the inanimate masculine noun рояль: should be 'на рояле', not 'на рояли'.
- решение: играть, сыграть на рояле
- rfi: RFI-avru-grammar-051420d5c044

### #074 — рукъ

- поле: `senses[0].examples[11].av`
- сейчас: «рукъ алда нахъа»
- исходный вопрос реквестера: malformed word spacing: 'рукъ алда' should likely be written as one word or with correct case suffix 'рукъалъул нахъа' or similar.
- решение: рукъалда нахъа — не рукъалъул нахъа
- rfi: RFI-avru-grammar-9735973bd721

### #076 — сверунжо

- поле: `senses[0].text`
- сейчас: «деревянная палочка; с помощью которого затягивают поклажу верёвкой»
- исходный вопрос реквестера: gender agreement error: relative pronoun 'которого' (masculine/neuter) does not agree with its feminine antecedent 'палочка' (should be 'которой')
- решение: деревянная палочка, с помощью которой затягивают поклажу верёвкой; comment «или металлическая» сохранить
- rfi: RFI-avru-grammar-79716fdee732

### #077 — сину

- поле: `forms[2]`
- сейчас: «синусинуца»
- исходный вопрос реквестера: Corrupted duplicated form string inside the paradigm.
- решение: синуца
- rfi: RFI-avru-grammar-e0131b81c9bd

### #078 — сину

- поле: `forms[4]`
- сейчас: «синусинудул»
- исходный вопрос реквестера: Corrupted duplicated form string inside the paradigm.
- решение: синудул; также синусинул → синул (тот же сбой разворачивания варианта)
- rfi: RFI-avru-grammar-e623908bff17

### #079 — сонтӏолълъар

- поле: `senses[0].comment`
- сейчас: «для нюхательного табака, изготавливаемый из роговой кости»
- исходный вопрос реквестера: participle agreement error: 'изготавливаемый' should be feminine ('изготавливаемая') to agree with 'табакерка'.
- решение: для нюхательного табака, изготавливаемая из роговой кости
- rfi: RFI-avru-grammar-59b89ba87460

### #080 — турбаза

- поле: `senses[0].examples[5].ru`
- сейчас: «они возвратились из турбазы»
- исходный вопрос реквестера: preposition 'из' typically takes the genitive, but with structures like турбаза the preposition 'с' ('вернулись с турбазы') is idiomatic in Russian
- решение: они возвратились с турбазы — для согласования с «на турбазе/на турбазу» в соседних примерах
- rfi: RFI-avru-grammar-e7352cf798ba

### #081 — тӏадагьаб

- поле: `senses[0].examples[6].ru`
- сейчас: «лёгкая рука у»
- исходный вопрос реквестера: incomplete sentence fragment ending with a preposition 'у' without its governed noun
- решение: ru: лёгкая рука у кого-либо; comment: напр. у врача — сохранить пояснение при переносе
- rfi: RFI-avru-grammar-4c0d9b7021de

### #082 — уйищ

- поле: `senses[0].comment`
- сейчас: «частица вопросительное (местоимение)»
- исходный вопрос реквестера: gender agreement error: 'вопросительное' should be feminine ('вопросительная') to agree with 'частица'.
- решение: частица вопросительная (местоимение)
- rfi: RFI-avru-grammar-1f62434c52e3

### #084 — хъулухъ

- поле: `senses[0].examples[9].ru`
- сейчас: «состояться на службе, занимать пост»
- исходный вопрос реквестера: wrong verb aspect: 'состояться' means to take place/materialize, whereas 'состоять' (imperfective) or 'состоять на службе' should be used here.
- решение: состоять на службе, занимать пост
- rfi: RFI-avru-grammar-60abc701049e

### #085 — хьихьи

- поле: `senses[2].examples[0].ru`
- сейчас: «обзаведение собаки»
- исходный вопрос реквестера: wrong case: noun 'собака' should be in the instrumental case ('собакой') after 'обзаведение', not genitive
- решение: обзаведение собакой
- rfi: RFI-avru-grammar-2c7fd0f1914a

## Не менять

### #003 — бетӏераб

- поле: `senses[0].examples[2].ru`
- сейчас: «главные члены»
- исходный вопрос реквестера: Russian linguistic terminology uses 'главные члены предложения', omitting 'предложения' here leaves an incomplete noun phrase.
- решение: «Главные члены» — самостоятельное допустимое терминологическое сочетание; метка «грамматика» уже задаёт контекст. Дополнение «предложения» не обязательно.
- rfi: RFI-avru-grammar-ce9639c0546d

### #010 — гачигамачӏ

- поле: `forms[2]`
- сейчас: «гачиганчӏица»
- исходный вопрос реквестера: stem root mismatch in paradigm form: contains -нчӏ- instead of -мачӏ-
- решение: PDF, с. 343, явно задаёт альтернативную основу гачиганчӏица. Не выравнивать по заголовку.
- rfi: RFI-avru-grammar-54123cd672dc

### #011 — гачигамачӏ

- поле: `forms[4]`
- сейчас: «гачиганчӏил»
- исходный вопрос реквестера: stem root mismatch in paradigm form: contains -нчӏ- instead of -мачӏ-
- решение: PDF, с. 343: гачиганчӏил также вынесено в отдельную родительную статью. Не опечатка.
- rfi: RFI-avru-grammar-edad04c65bea

### #040 — жанахӏ

- поле: `senses[0].examples[2].ru`
- сейчас: «повесить картины на стене коридора»
- исходный вопрос реквестера: wrong case after 'повесить': requires accusative 'на стену' for direction, not prepositional 'на стене'
- решение: «Повесить картины на стене коридора» допустимо: предложный падеж обозначает место размещения. «На стену» не единственный вариант.
- rfi: RFI-avru-grammar-c33db1430481

### #044 — зангалмачуял

- поле: `forms[1]`
- сейчас: «зангалмачуяяз»
- исходный вопрос реквестера: Erroneous duplication of "я": oblique plural of "зангалмачуял" (stem "зангалмачуя-") should be "зангалмачуяз".
- решение: PDF, с. 662: зангалмачуя/л (-яз, -язул). Основа зангалмачуя- + -яз даёт яяз. Не удалять букву лишь из-за её удвоения.
- rfi: RFI-avru-grammar-5fc21017c037

### #045 — зангалмачуял

- поле: `forms[2]`
- сейчас: «зангалмачуяязул»
- исходный вопрос реквестера: Erroneous duplication of "я": genitive plural of "зангалмачуял" (stem "зангалмачуя-") should be "зангалмачуязул".
- решение: Та же парадигма: зангалмачуя- + -язул → зангалмачуяязул. Механическое сокращение не обосновано.
- rfi: RFI-avru-grammar-60e939ce1810

### #071 — рахъ-рахъалда

- поле: `senses[0].examples[2].ru`
- сейчас: «аул, основанный людьми, переселившимися с разных мест»
- исходный вопрос реквестера: prepositional government error: 'переселившимися с разных мест' should be 'переселившимися из разных мест'
- решение: «Переселившимися с разных мест» допустимо; «из разных мест» — стилистический вариант, не обязательная правка.
- rfi: RFI-avru-grammar-1b5f2a3a902d

### #072 — рекӏен

- поле: `forms[2]`
- сейчас: «рекӏадул»
- исходный вопрос реквестера: The oblique form breaks the paradigm stem consistency established by the headword and ergative form.
- решение: PDF, с. 1148: рекӏен¹ (-алъ, рекӏадул). У «езды верхом» особая основа. Не смешивать парадигмы омонимов.
- rfi: RFI-avru-grammar-41606675462a

### #083 — хъахӏаб

- поле: `senses[3].text`
- сейчас: «Кахав»
- исходный вопрос реквестера: Typo in the name gloss: should start with 'Хъахӏав' to match the root and the precomment note.
- решение: Кахав — русская передача личного имени, прямо напечатанная в PDF, с. 1331. Аварская форма Хъахӏав сохранена в forms. Требования совпадать с аварским корнем у русского имени нет.
- rfi: RFI-avru-grammar-a0f07155c917

## Нужно решение мейнтейнера

### #021 — гӏадахъ

- поле: `pos`
- сейчас: «глагол»
- исходный вопрос реквестера: The entry is labeled as a verb (глагол), but the headword 'гӏадахъ' is an adverbial/locative form used in fixed expressions, not a verbal infinitive.
- решение: Глагол здесь босизе, а гӏадахъ — компонент выражения. В PDF, с. 502, нет пометы наречия. Предлагаю pos: —, form: —. Подтверди, либо укажи часть речи.
- rfi: RFI-avru-grammar-79016a5f9e5b

### #026 — гӏудго

- поле: `pos`
- сейчас: «глагол»
- исходный вопрос реквестера: The entry has no verbal senses or examples of an action, but rather defines an adjectival/noun modifier meaning 'adopted' in the example 'adopted son'.
- решение: PDF, с. 576, даёт гӏудго только в диалектном сочетании гӏудго вас. Глагол/инфинитив неверно; для уверенного выбора прилагательного данных мало. Предлагаю pos: —, form: —.
- rfi: RFI-avru-grammar-3d4cb3b4cc36

### #053 — икъунат

- поле: `forms[3]`
- сейчас: «икъунатат»
- исходный вопрос реквестера: Plural form has erroneous suffix '-ат' instead of '-ал' ('икъунатал') expected from the stem and oblique forms.
- решение: PDF, с. 680: икъунат (-алъ, -алъул, -ат). Икъунатат следует источнику, хотя подозрительно. Подтверди: нужно икъунатал?
- rfi: RFI-avru-grammar-a03d845ad255

### #075 — рукӏкӏби

- поле: `forms[2]`
- сейчас: «рукӏкӏбзул»
- исходный вопрос реквестера: malformed consonant cluster in genitive plural form 'рукӏкӏбзул'
- решение: PDF, с. 1175: рукӏкӏб/и (-уз, -зул), откуда текущее рукӏкӏбзул. Подтверди, заменять ли на рукӏкӏбузул: необычный кластер сам по себе не доказательство ошибки.
- rfi: RFI-avru-grammar-9ddca3b6add1

### #086 — хьуцӏихер

- поле: `forms[2]`
- сейчас: «хӏуцӏизарица»
- исходный вопрос реквестера: The form uses an incorrect root 'хӏуцӏиз-' instead of the lemma's root 'хьуцӏих-'.
- решение: PDF, с. 1355, прямо печатает хӏуцӏизарица; рядом родительный хьуцӏихарил. Возможно, опечатка книги, но нужна подтверждённая правильная форма, а не выравнивание по заголовку.
- rfi: RFI-avru-grammar-9d5b7bb73f88
