# av-ru.1936: проверка алфавита аварских полей

Статей: 7023. Полей с кириллицей: 0. Полей с графемами вне алфавита: 37 в 22 статьях.

Проверяются word, forms, spelling_forms, gender_forms, examples[].av и see_also[].target. Русские переводы, labels и комментарии не транслитерируются. Разрешены 39 исторических букв, регистр, пунктуация и ударение на гласной. Цифры допустимы в обозначениях; предупреждение не служит командой удаления.

Каноническая запись не доказывает правильность чтения: подмена одной допустимой буквы другой здесь не обнаруживается. Особенно важны контекстная проверка ɫ и различение x/x̨/x̵.

Воспроизведение: `python3 src/audit_zhirkov_1936_alphabet.py --report review/av-ru.1936-alphabet.md --json review/av-ru.1936-alphabet.json`.

| Строка | Скан | Слово | Поле | Значение | Кириллица | Вне алфавита |
|---:|---:|---|---|---|---|---|
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
| 1556 | 41 | gamiẍan | word | gamiẍan |  | ẍ |
| 1556 | 41 | gamiẍan | forms[0] | gamiẍan |  | ẍ |
| 1556 | 41 | gamiẍan | forms[1] | gamiẍabi |  | ẍ |
| 1604 | 42 | geni | senses[0].examples[0].av | hozzọ-gen |  | ọ |
| 2405 | 57 | ḩaʿa(t)lize | word | ḩaʿa(t)lize |  | ʿ |
| 2405 | 57 | ḩaʿa(t)lize | forms[0] | ḩaʿa(t)lize |  | ʿ |
| 2537 | 59 | ḩazo | senses[0].examples[0].av | ḩazo-xañab |  | ñ |
| 3039 | 68 | kkeze | senses[2].examples[1].av | kį-kį kkun |  | į |
| 3585 | 79 | maçab | see_also[0].target | maʒab |  | ʒ |
| 3660 | 80 | mamlakat | forms[1] | mamlakatȧ |  | ȧ |
| 4134 | 90 | p(a)lašş | word | p(a)lašş |  | š |
| 4134 | 90 | p(a)lašş | forms[0] | p(a)lašş |  | š |
| 4263 | 92 | penzak | forms[1] | penzaḱal |  | ḱ |
| 4537 | 97 | qeda-biql̇ | word | qeda-biql̇ |  | l̇ |
| 4537 | 97 | qeda-biql̇ | forms[0] | qeda-biql̇ |  | l̇ |
| 4537 | 97 | qeda-biql̇ | see_also[1].target | biql̇ |  | l̇ |
| 4614 | 99 | qoẋo(l)-dergo | word | qoẋo(l)-dergo |  | ẋ |
| 4614 | 99 | qoẋo(l)-dergo | forms[0] | qoẋo(l)-dergo |  | ẋ |
| 4614 | 99 | qoẋo(l)-dergo | forms[1] | qoẋo(l)-larkac |  | ẋ |
| 4910 | 104 | razząd | word | razząd |  | ą |
| 4910 | 104 | razząd | forms[0] | razząd |  | ą |
| 5053 | 107 | rix̵ | forms[1] | rix̵ȧ |  | ȧ |
| 5289 | 111 | sordo-barṣadļi | word | sordo-barṣadļi |  | ṣ |
| 5289 | 111 | sordo-barṣadļi | forms[0] | sordo-barṣadļi |  | ṣ |
| 6285 | 129 | xaļq | senses[0].examples[0].av | xaļqaļu raq́ |  | q́ |
| 6559 | 134 | xaħba | senses[0].examples[0].av | bixịn-xaħba |  | ị |
