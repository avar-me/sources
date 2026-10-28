# av-ru.1936: проверка алфавита аварских полей

Статей: 7023. Полей с кириллицей: 0. Полей с графемами вне алфавита: 17 в 11 статьях.

Проверяются word, forms, spelling_forms, gender_forms, examples[].av и see_also[].target. Русские переводы, labels и комментарии не транслитерируются. Разрешены 39 исторических букв, регистр, пунктуация и ударение на гласной. Цифры допустимы в обозначениях; предупреждение не служит командой удаления.

Каноническая запись не доказывает правильность чтения: подмена одной допустимой буквы другой здесь не обнаруживается. Особенно важны контекстная проверка ɫ и различение x/x̨/x̵.

Воспроизведение: `python3 src/audit_zhirkov_1936_alphabet.py --report review/av-ru.1936-alphabet.md --json review/av-ru.1936-alphabet.json`.

| Строка | Скан | Слово | Поле | Значение | Кириллица | Вне алфавита |
|---:|---:|---|---|---|---|---|
| 1556 | 41 | gamiẍan | word | gamiẍan |  | ẍ |
| 1556 | 41 | gamiẍan | forms[0] | gamiẍan |  | ẍ |
| 1556 | 41 | gamiẍan | forms[1] | gamiẍabi |  | ẍ |
| 1604 | 42 | geni | senses[0].examples[0].av | hozzọ-gen |  | ọ |
| 2405 | 57 | ḩaʿa(t)lize | word | ḩaʿa(t)lize |  | ʿ |
| 2405 | 57 | ḩaʿa(t)lize | forms[0] | ḩaʿa(t)lize |  | ʿ |
| 3039 | 68 | kkeze | senses[2].examples[1].av | kį-kį kkun |  | į |
| 3585 | 79 | maçab | see_also[0].target | maʒab |  | ʒ |
| 3660 | 80 | mamlakat | forms[1] | mamlakatȧ |  | ȧ |
| 4263 | 92 | penzak | forms[1] | penzaḱal |  | ḱ |
| 4537 | 97 | qeda-biql̇ | word | qeda-biql̇ |  | l̇ |
| 4537 | 97 | qeda-biql̇ | forms[0] | qeda-biql̇ |  | l̇ |
| 4537 | 97 | qeda-biql̇ | see_also[1].target | biql̇ |  | l̇ |
| 5053 | 107 | rix̵ | forms[1] | rix̵ȧ |  | ȧ |
| 5289 | 111 | sordo-barṣadļi | word | sordo-barṣadļi |  | ṣ |
| 5289 | 111 | sordo-barṣadļi | forms[0] | sordo-barṣadļi |  | ṣ |
| 6285 | 129 | xaļq | senses[0].examples[0].av | xaļqaļu raq́ |  | q́ |
