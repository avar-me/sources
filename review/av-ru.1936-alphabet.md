# av-ru.1936: проверка алфавита аварских полей

Статей: 7023. Полей с кириллицей: 0. Полей с графемами вне алфавита: 65 в 38 статьях.

Проверяются word, forms, spelling_forms, gender_forms, examples[].av и see_also[].target. Русские переводы, labels и комментарии не транслитерируются. Разрешены 39 исторических букв, регистр, пунктуация и ударение на гласной. Цифры допустимы в обозначениях; предупреждение не служит командой удаления.

Каноническая запись не доказывает правильность чтения: подмена одной допустимой буквы другой здесь не обнаруживается. Особенно важны контекстная проверка ɫ и различение x/x̨/x̵.

Воспроизведение: `python3 src/audit_zhirkov_1936_alphabet.py --report review/av-ru.1936-alphabet.md --json review/av-ru.1936-alphabet.json`.

| Строка | Скан | Слово | Поле | Значение | Кириллица | Вне алфавита |
|---:|---:|---|---|---|---|---|
| 297 | 15 | baƣcaci | forms[1] | baƣcacah̨t |  | h̨ |
| 458 | 19 | baxi(n) | see_also[0].target | barxįn |  | į |
| 459 | 19 | baxine | see_also[0].target | barxįne |  | į |
| 525 | 20 | beꝗize | see_also[1].target | ẋva-ze |  | ẋ |
| 673 | 23 | boh̄o... | word | boh̄o... |  | h̄ |
| 673 | 23 | boh̄o... | forms[0] | boh̄o... |  | h̄ |
| 673 | 23 | boh̄o... | see_also[0].target | buh̄a |  | h̄ |
| 674 | 23 | boh̄olo | word | boh̄olo |  | h̄ |
| 674 | 23 | boh̄olo | forms[0] | boh̄olo |  | h̄ |
| 674 | 23 | boh̄olo | forms[1] | boh̄oli |  | h̄ |
| 674 | 23 | boh̄olo | forms[2] | boh̄olabi |  | h̄ |
| 735 | 24 | boxx | see_also[0].target | maño |  | ñ |
| 958 | 29 | cex̨ | forms[2] | cax̣al |  | x̣ |
| 1118 | 32 | C(ç)ox̵ | senses[0].examples[0].av | ççoxiϳav |  | ϳ |
| 1264 | 35 | deħen | forms[2] | dūħnul |  | ū |
| 1556 | 41 | gamiẍan | word | gamiẍan |  | ẍ |
| 1556 | 41 | gamiẍan | forms[0] | gamiẍan |  | ẍ |
| 1556 | 41 | gamiẍan | forms[1] | gamiẍabi |  | ẍ |
| 1604 | 42 | geni | senses[0].examples[0].av | hozzọ-gen |  | ọ |
| 2405 | 57 | ḩaʿa(t)lize | word | ḩaʿa(t)lize |  | ʿ |
| 2405 | 57 | ḩaʿa(t)lize | forms[0] | ḩaʿa(t)lize |  | ʿ |
| 2537 | 59 | ḩazo | senses[0].examples[0].av | ḩazo-xañab |  | ñ |
| 3039 | 68 | kkeze | senses[2].examples[1].av | kį-kį kkun |  | į |
| 3120 | 70 | kor | senses[0].examples[0].av | kor b̂orqize |  | b̂ |
| 3141 | 70 | kulak | senses[0].examples[0].av | kulakazul xaluci, kulakazul raçç, kulakazul qorq ̂alupan |  |  ̂ |
| 3171 | 71 | kusize | senses[1].examples[0].av | b̂o kusize |  | b̂ |
| 3585 | 79 | maçab | see_also[0].target | maʒab |  | ʒ |
| 3660 | 80 | mamlakat | forms[1] | mamlakatȧ |  | ȧ |
| 3925 | 86 | mutęħ | word | mutęħ |  | ę |
| 3925 | 86 | mutęħ | forms[0] | mutęħ |  | ę |
| 3925 | 86 | mutęħ | forms[2] | mutęħab |  | ę |
| 3926 | 86 | mutęħli | word | mutęħli |  | ę |
| 3926 | 86 | mutęħli | forms[0] | mutęħli |  | ę |
| 4134 | 90 | p(a)lašş | word | p(a)lašş |  | š |
| 4134 | 90 | p(a)lašş | forms[0] | p(a)lašş |  | š |
| 4189 | 91 | parç̧ad | word | parç̧ad |  | ç̧ |
| 4189 | 91 | parç̧ad | forms[0] | parç̧ad |  | ç̧ |
| 4189 | 91 | parç̧ad | forms[1] | parç̧adal |  | ç̧ |
| 4189 | 91 | parç̧ad | see_also[0].target | maç̧ad |  | ç̧ |
| 4263 | 92 | penzak | forms[1] | penzaḱal |  | ḱ |
| 4537 | 97 | qeda-biql̇ | word | qeda-biql̇ |  | l̇ |
| 4537 | 97 | qeda-biql̇ | forms[0] | qeda-biql̇ |  | l̇ |
| 4537 | 97 | qeda-biql̇ | see_also[1].target | biql̇ |  | l̇ |
| 4614 | 99 | qoẋo(l)-dergo | word | qoẋo(l)-dergo |  | ẋ |
| 4614 | 99 | qoẋo(l)-dergo | forms[0] | qoẋo(l)-dergo |  | ẋ |
| 4614 | 99 | qoẋo(l)-dergo | forms[1] | qoẋo(l)-larkac |  | ẋ |
| 4745 | 101 | quç̇ç̇ | word | quç̇ç̇ |  | ç̇ |
| 4745 | 101 | quç̇ç̇ | forms[0] | quç̇ç̇ |  | ç̇ |
| 4745 | 101 | quç̇ç̇ | forms[1] | quç̇ç̇da |  | ç̇ |
| 4745 | 101 | quç̇ç̇ | senses[1].examples[0].av | quç̇ç̇ab |  | ç̇ |
| 4745 | 101 | quç̇ç̇ | senses[2].forms[0] | quç̇ç̇da |  | ç̇ |
| 4745 | 101 | quç̇ç̇ | see_also[0].target | ç̇çuq |  | ç̇ |
| 4910 | 104 | razząd | word | razząd |  | ą |
| 4910 | 104 | razząd | forms[0] | razząd |  | ą |
| 5053 | 107 | rix̵ | forms[1] | rix̵ȧ |  | ȧ |
| 5229 | 110 | sapar | senses[0].examples[0].av | sapar bux̣ine |  | x̣ |
| 5289 | 111 | sordo-barṣadļi | word | sordo-barṣadļi |  | ṣ |
| 5289 | 111 | sordo-barṣadļi | forms[0] | sordo-barṣadļi |  | ṣ |
| 5513 | 115 | ssuţize | senses[1].examples[1].av | cex̣ ssuţarav |  | x̣ |
| 5651 | 118 | tala | see_also[1].target | max̣i |  | x̣ |
| 6285 | 129 | xaļq | senses[0].examples[0].av | xaļqaļu raq́ |  | q́ |
| 6355 | 130 | xoⱨaze | word | xoⱨaze |  | ⱨ |
| 6355 | 130 | xoⱨaze | forms[0] | xoⱨaze |  | ⱨ |
| 6437 | 131 | x(x)inķ | senses[0].examples[0].av | ẑura xxinķ |  | ẑ |
| 6559 | 134 | xaħba | senses[0].examples[0].av | bixịn-xaħba |  | ị |
