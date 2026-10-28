# av-ru.1936: проверка алфавитного порядка

Статей: 7023. Подозрительных соседних пар: 270.

У 15 пар порядок подтверждён по печати; остальные 255 требуют сверки. Решения хранятся в `review/av-ru.1936-order-reviewed.json`; совпадение проверяется по скану и обоим заголовкам.

Порядок 39 букв взят со сканов 5 и 147. Апострофы, дефисы, регистр и ударения игнорируются; удвоенные согласные сортируются как две буквы. Для внутрисловных скобок проверяются обе формы.

Это кандидаты для сверки, а не список готовых замен. Разные исторические буквы нередко распознаны одинаково (q, s, z); встречаются печатные перестановки, отсылки и повреждённые границы статей. Пересортировывать исходник для устранения предупреждений нельзя.

Воспроизведение: `python3 src/audit_zhirkov_1936_order.py --report review/av-ru.1936-order.md`.

## Графемы вне алфавита и диагностических эквивалентов

`ẍ` × 1, `ʿ` × 1, `l̇` × 1, `ṣ` × 1

## Соседние пары

Номер — текущая строка JSONL; скан — физическая страница PDF.

| Строка | Скан | Предыдущее слово | Текущее слово | Следующее слово | Проверка |
|---:|---:|---|---|---|---|
| 69 | 10 | ahlo | ahadin | aħahize | Требует сверки |
| 81 | 10 | aħţize | ahu-ħinçç | Aħul-goħ | Требует сверки |
| 83 | 10 | Aħul-goħ | aħ | aj | Требует сверки |
| 146 | 12 | antrasit | antologija | antropomorfizm | Требует сверки |
| 199 | 13 | aştronom | astronomija | aşlav | Требует сверки |
| 236 | 14 | avqust | aviasija | a(v)lax | Требует сверки |
| 271 | 14 | azot | azal | Azaristan | Требует сверки |
| 292 | 15 | baqabacarize | baƣar(d)ize | baƣaroļize | Требует сверки |
| 294 | 15 | baƣaroļize | baƣari | baƣarize | Требует сверки |
| 317 | 15 | baħarzal | baħac | baħali | Требует сверки |
| 347 | 16 | baķ | bak | baķabaxxari | Требует сверки |
| 351 | 16 | baķarize | bakgo | bakļi | Требует сверки |
| 396 | 17 | baqvaze | baq | baqada-rax̵i | Требует сверки |
| 430 | 18 | bassma-xana | basra | basraļi | Требует сверки |
| 433 | 18 | basraļize | basize | bass | Требует сверки |
| 437 | 18 | Başqirdistan | başliq | başmaq | Требует сверки |
| 443 | 18 | baţaqla | bataljon | batareja | Требует сверки |
| 458 | 19 | baxxci(n)ze | baxi(n) | baxine | Требует сверки |
| 460 | 19 | baxine | baxi | baxin | Требует сверки |
| 468 | 19 | bazis | baza | bazarize | Требует сверки |
| 471 | 19 | baⱬ | Baçada | baⱬize | Требует сверки |
| 521 | 20 | beļļene | beļabuxize | benzin | Требует сверки |
| 546 | 20 | bessine | besarize | besize | Требует сверки |
| 554 | 21 | beşţin | beştine | beta | Требует сверки |
| 567 | 21 | b:xxe | bexe(r)xize | bezen | Требует сверки |
| 571 | 21 | bezize | bez | bezal | Требует сверки |
| 574 | 21 | beⱬize | bezli | bezļize | Требует сверки |
| 602 | 22 | biꝗize | biha | bihaļi | Требует сверки |
| 614 | 22 | biꝗꝗine | bil | bilet | Требует сверки |
| 624 | 22 | biqize | biqbiqize | biqize | Требует сверки |
| 656 | 23 | bix̵ize | bix̵bix̵ize | bix̵ize | Требует сверки |
| 679 | 23 | Bolqarija | bolnisa | bolo... | Требует сверки |
| 692 | 24 | boq(v)aze | boq | boqaboqize | Требует сверки |
| 728 | 24 | bosse | bosaro | bosin | Требует сверки |
| 768 | 25 | buħuc | buħa | buḩize | Требует сверки |
| 818 | 26 | bussurman | busize | busur | Требует сверки |
| 831 | 26 | bux̨ine | buxarize | buxaro | Требует сверки |
| 852 | 27 | caqir | caḩi | caj | Требует сверки |
| 885 | 28 | canoq... | canixan | canta | Требует сверки |
| 920 | 28 | caxxţ... | cax... | caxma | Требует сверки |
| 952 | 29 | ceroqen | cerma | cerx(x) | Требует сверки |
| 965 | 29 | cijaqo | cijal | cijaq | Требует сверки |
| 986 | 30 | coqondor | cojen | col | Требует сверки |
| 992 | 30 | coroq... | corok | co(r)t | Требует сверки |
| 999 | 30 | coxxţo | cox... | coşoxan | Требует сверки |
| 1000 | 30 | cox... | coşoxan | cu | Требует сверки |
| 1054 | 31 | çaħaļize | çaħa | çalabi | Требует сверки |
| 1062 | 31 | çalquţan | çalo | çalxxine | Требует сверки |
| 1074 | 31 | çanquţan | çanq | çar... | Требует сверки |
| 1106 | 32 | ççikva | C(ç)iqab | ççiqarila-kiliş | Требует сверки |
| 1111 | 32 | ççiqize | ççinţize | ççixize | Требует сверки |
| 1118 | 32 | ç(ç)oqo-borox̵ | C(ç)ox̵ | ç(ç)uq | Требует сверки |
| 1143 | 33 | çinqva | çinq-borox̵ | çinxx... | Требует сверки |
| 1179 | 33 | çuqun | çuq | çurkan | Требует сверки |
| 1196 | 34 | çvarqjeze | çvarqize | çvaze | Требует сверки |
| 1210 | 34 | Daoq_us(s)tan | dah | dahamaq | Требует сверки |
| 1250 | 35 | Daroq_i | darman | darman-ţaħarav | Требует сверки |
| 1327 | 36 | diroqize | dirizabl | diskussija | Требует сверки |
| 1345 | 37 | dohodin | doho | doj | Требует сверки |
| 1354 | 37 | dolgo | dole | dolma | Требует сверки |
| 1375 | 37 | duoql | duoqdaze | duha | Требует сверки |
| 1376 | 37 | duoqdaze | duha | duhbi | Требует сверки |
| 1390 | 37 | duroqize | durhize | durize | Требует сверки |
| 1423 | 38 | eqe | eħedin | ej | Требует сверки |
| 1460 | 39 | eroqax | erken | erkenļi | Требует сверки |
| 1591 | 41 | gazgaz | gaz... | gazac | Требует сверки |
| 1701 | 43 | gulgul-ħeleko | gulgul-ħanķo | gulgun | Требует сверки |
| 1721 | 44 | gurgur-ħinçç | gurgur-ħanķo | gurgurize | Требует сверки |
| 1747 | 44 | gvanzic | gvanzi | gvend | Требует сверки |
| 1771 | 45 | ƣaloqaj | ƣalmaqal | ƣalmaqalcí | Требует сверки |
| 1794 | 45 | ƣaroqar | ƣarim | ƣarinli | Требует сверки |
| 1808 | 46 | ƣazi-ƣumek | ƣaz... | ƣedo | Печатный порядок подтверждён |
| 1816 | 46 | ƣeze | ƣez | ƣez | Печатный порядок подтверждён |
| 1848 | 46 | ƣoļ | ƣoƣ-ļel | ƣo(r)t | Печатный порядок подтверждён |
| 1850 | 46 | ƣo(r)t | ƣo(r)ƣ | ƣorƣ-hobo | Печатный порядок подтверждён |
| 1868 | 47 | ƣuoƣaze | ƣu(j) | ƣuj(i) | Печатный порядок подтверждён |
| 1880 | 47 | ƣunoƣur | ƣuni | Ƣunib | Печатный порядок подтверждён |
| 1895 | 47 | ƣuⱬdul | ƣuzize | ƣvala | Требует сверки |
| 1900 | 47 | ƣvaroƣvadize | ƣvari | ƣvari | Печатный порядок подтверждён |
| 1943 | 48 | haqale | hah... | haha! | Требует сверки |
| 1962 | 48 | Halqaderil-ħor | hali | halize | Требует сверки |
| 2040 | 50 | ħekko | hektar | hektolitr | Требует сверки |
| 2045 | 50 | helize | hel | hemmexxaļ | Требует сверки |
| 2142 | 52 | hozⱬaļ | Hozzaļ | Hozzdaļ | Требует сверки |
| 2149 | 52 | huoqub | huhdul | huin | Требует сверки |
| 2167 | 52 | huru-oļedo | hu'rul | hurzul | Требует сверки |
| 2204 | 53 | ħalisa | -ħalab | ħalaq | Требует сверки |
| 2212 | 53 | ħalisine | ħaliqad | ħaliqa(d)ļi | Требует сверки |
| 2227 | 53 | ħama-oļanq | ħamam | ħamizaz | Требует сверки |
| 2267 | 54 | ħatta | ħat | ħat | Требует сверки |
| 2270 | 54 | ħaţal | ħatgojab | ħaţi... | Требует сверки |
| 2277 | 54 | ħaze | ħaz | ħazat | Требует сверки |
| 2308 | 55 | ħex | ħeşeze | ħez | Требует сверки |
| 2311 | 55 | ħil | ħikmat | ħil(l)a | Печатный порядок подтверждён |
| 2322 | 55 | ħinqize | ħinq | ħinss | Печатный порядок подтверждён |
| 2326 | 55 | ħinssļize | ħinss | ħisab | Печатный порядок подтверждён |
| 2367 | 56 | ħuss(i) | ħur | ħur-al-ħin | Требует сверки |
| 2406 | 57 | ḩaʿa(t)lize | ḩadav | ḩadax̵ | Требует сверки |
| 2431 | 57 | ḩaķa | ḩakda... | Ḩakkvax | Печатный порядок подтверждён |
| 2485 | 58 | ḩanxva | ḩanxize | ḩaqil | Печатный порядок подтверждён |
| 2533 | 59 | Ḩaxvax | Ḩaxuş | ḩazab | Требует сверки |
| 2538 | 59 | ḩazo | ḩazajib | ḩazajibli | Требует сверки |
| 2617 | 61 | ḩodosseb | ḩodosine | ḩokko... | Печатный порядок подтверждён |
| 2682 | 62 | ḩuzru | ḩuz | ḩuzļi | Печатный порядок подтверждён |
| 2685 | 62 | ḩuzruq | ḩuz | ḩvadize | Печатный порядок подтверждён |
| 2769 | 63 | istakan | is | isi | Требует сверки |
| 2772 | 64 | issu(l) | iss(i)ko | -iş | Требует сверки |
| 2800 | 64 | izvoşşik | izara | izaraci | Требует сверки |
| 2812 | 64 | jaoqzijat | jahudijav | jah | Требует сверки |
| 2813 | 64 | jahudijav | jah | -jali | Требует сверки |
| 2824 | 65 | jaqut | jaqad | jaqina | Требует сверки |
| 2852 | 65 | jessaruxan | jesaruxan | jexxe | Требует сверки |
| 2891 | 66 | kaoqat | kahru | Kaħba | Требует сверки |
| 2929 | 67 | kanţl | kanţize | kaparat | Требует сверки |
| 3032 | 68 | kisseb | kisej | kisi | Требует сверки |
| 3108 | 70 | konsul-xana | konsert | konsessija | Требует сверки |
| 3170 | 71 | kustarļize | kus | kusize | Требует сверки |
| 3185 | 71 | kvagize | kvadrat | kvaḩab | Требует сверки |
| 3194 | 71 | kvana-oļvanaj | kvana-heqel | kvana-heqeze | Требует сверки |
| 3216 | 72 | kveqize | kvehab | kvehasa | Требует сверки |
| 3248 | 73 | ķalaqorqe | ķalaķuç | ķalançad | Требует сверки |
| 3253 | 73 | ķaliccaze | ķal-hiqize | ķal-kkvej | Требует сверки |
| 3259 | 73 | ķalţu | kaluş | ķalzi | Требует сверки |
| 3294 | 73 | ķiqez | ķiḩi | ķihan | Требует сверки |
| 3295 | 74 | ķiḩi | ķihan | ķi-ḩarqelab | Требует сверки |
| 3395 | 75 | laqļi | lahlahize | lah | Требует сверки |
| 3396 | 75 | lahlahize | lah | laħto | Требует сверки |
| 3399 | 75 | laħza(t) | laħdeze | laħi | Требует сверки |
| 3429 | 76 | lazza(t)li | lazbar | le! li! | Требует сверки |
| 3431 | 76 | le! li! | lebal | lebalļi | Требует сверки |
| 3454 | 76 | luqat | luħla | lulbi | Требует сверки |
| 3475 | 77 | ļalxize | ļaladize | ļalaj | Требует сверки |
| 3482 | 77 | ļaraħļi | larako | ļa(r)ķ | Требует сверки |
| 3511 | 78 | ļļeder | ļedeze | ļedoxan | Требует сверки |
| 3529 | 78 | ļudbi | ļob | ļoba | Требует сверки |
| 3557 | 78 | łuqur | łuhin | łuhine | Требует сверки |
| 3574 | 79 | łux̵ize | łux̵ | łux̵ļi | Требует сверки |
| 3590 | 79 | madaqadalab | madal | madanijat | Требует сверки |
| 3604 | 79 | maqrib | mah | mahari | Требует сверки |
| 3610 | 79 | maħ | Mahac-Xala | maħi | Требует сверки |
| 3614 | 79 | maħlax̵ | maħlaj | maħo | Требует сверки |
| 3620 | 80 | maħsine | maħ | maħ(a)dan | Требует сверки |
| 3655 | 80 | maļļi | maļjarize | maļjaruxan | Требует сверки |
| 3664 | 81 | manoquşş | manifest | maniħ | Требует сверки |
| 3675 | 81 | maqnaţis | maqixxine | maqo | Требует сверки |
| 3679 | 81 | maroqal | marha | marhaci | Требует сверки |
| 3688 | 81 | marqaço | marmar | mart | Требует сверки |
| 3694 | 81 | marzil | marzan | masailal | Требует сверки |
| 3711 | 81 | maşoqulļize | maşhur | maşin(a) | Требует сверки |
| 3742 | 82 | mazilijav | mazab | mazallat | Требует сверки |
| 3759 | 82 | meqi | mehed | meḩ | Требует сверки |
| 3800 | 83 | miqir | miħi | mikk | Требует сверки |
| 3849 | 84 | mixral | mix | miⱬⱬir | Требует сверки |
| 3867 | 85 | moqro... | moqlo... | moqro... | Требует сверки |
| 3872 | 85 | moxmox | mox | mozoro | Требует сверки |
| 3886 | 85 | muoqdul | muh | muhdul | Требует сверки |
| 3929 | 86 | muxxúla | mux | mux | Требует сверки |
| 3957 | 86 | nako | nakķ | nakķ | Требует сверки |
| 3966 | 86 | naļulav | naļu... | namus | Требует сверки |
| 4024 | 88 | nikkel | nikk | nil | Требует сверки |
| 4027 | 88 | niļo | nil | niļer | Требует сверки |
| 4033 | 88 | nizam-heçoļi | niz | nizer | Требует сверки |
| 4049 | 88 | nuqaj | nuh | nuh | Требует сверки |
| 4064 | 88 | nusi-rec | nusal | nusijav | Требует сверки |
| 4072 | 89 | nuxrulav | nuxa | nuz | Требует сверки |
| 4088 | 89 | oq'o-kver | ojmax | okrug | Требует сверки |
| 4103 | 89 | ostol | os | os-huţ | Требует сверки |
| 4230 | 92 | passţan | pasifist | pasifizm | Требует сверки |
| 4342 | 93 | ponzera | ponqeze | ponzoro | Требует сверки |
| 4418 | 95 | pursuq | purssi | purşina | Требует сверки |
| 4461 | 96 | qaji-ssveri | qajisa | qaji-sadax | Требует сверки |
| 4517 | 97 | qasseļize-ħan | qasandize | qaţ | Требует сверки |
| 4535 | 97 | qeceze | qecç | qed | Требует сверки |
| 4549 | 97 | qeze | qbiqdize | qibla | Требует сверки |
| 4571 | 98 | Qiroqizistan | Qirim | qiriqdize | Требует сверки |
| 4643 | 99 | qurqur | qurqi | qurqize | Требует сверки |
| 4683 | 100 | qvine | qabej | qabeze | Требует сверки |
| 4735 | 101 | qoqen | qoħ | qoħav-ci | Требует сверки |
| 4743 | 101 | qoxxorxxo | Qox | qoz | Требует сверки |
| 4792 | 102 | raoquxan | rahize | rahize | Требует сверки |
| 4805 | 102 | raħmo | raħ | raħad | Требует сверки |
| 4827 | 103 | raķ-buħari | rakine | ra(ķ)qaze | Требует сверки |
| 4848 | 103 | raqvaze | raq | raqa | Требует сверки |
| 4870 | 103 | rasxod | rasabi | rasi | Требует сверки |
| 4891 | 104 | raxxçi(n)ze | raxq | raxan | Требует сверки |
| 4892 | 104 | raxq | raxan | raxdaq | Требует сверки |
| 4894 | 104 | raxdaq | rax | raxas(s) | Требует сверки |
| 4906 | 104 | raziļize | razarize | razi | Требует сверки |
| 4909 | 104 | razul | razize | raⱬⱬad | Требует сверки |
| 4911 | 104 | raⱬⱬad | razţine | razⱬunisa-ħeţe | Требует сверки |
| 4915 | 104 | reccize | reccanx̵(d)ize | reçaze | Требует сверки |
| 4934 | 105 | reqleze | reħaze | reħel | Требует сверки |
| 4938 | 105 | reḩize | reḩel | reḩer | Требует сверки |
| 4957 | 105 | reqine | rekk | rels | Требует сверки |
| 4967 | 105 | reļļen-xvaj | reļ | reqab | Требует сверки |
| 4974 | 105 | req-şink(an) | reqarize | reqaruxabi | Требует сверки |
| 4985 | 105 | restoran | resarize | resaruxabi | Требует сверки |
| 5006 | 106 | rexxunti | rexed | reqen | Требует сверки |
| 5007 | 106 | rexed | reqen | rexe(r)xize | Требует сверки |
| 5013 | 106 | rezolusija | rezissor | rezize | Требует сверки |
| 5015 | 106 | rezize | reqen | reqize | Требует сверки |
| 5018 | 106 | rezz | reqzarize | reqqize | Требует сверки |
| 5019 | 106 | reqzarize | reqqize | ricel | Требует сверки |
| 5025 | 106 | riqvel | rih | rihin | Требует сверки |
| 5040 | 106 | Rissi-baqal | risarduxabi | rişşaruxabi | Требует сверки |
| 5046 | 106 | riţel | riti | ri(ţ)muç | Требует сверки |
| 5058 | 107 | rizli | rizaliqab | rizi | Требует сверки |
| 5071 | 107 | rokkel | rokka... | rokkel | Требует сверки |
| 5078 | 107 | roqob | roqi | roqize | Требует сверки |
| 5110 | 108 | rosţ... | rosen | rosine | Требует сверки |
| 5129 | 108 | rox̨ine | roxo | roⱬⱬen | Требует сверки |
| 5186 | 109 | rus(s)un | rusize | ruşbat | Требует сверки |
| 5191 | 109 | ruxize | ruxa... | rux̨bi | Требует сверки |
| 5197 | 109 | rux̨ine | ruxarize | ruxize | Требует сверки |
| 5202 | 109 | ruzmal-qo | ruzize | ruⱬⱬalago | Требует сверки |
| 5211 | 109 | saoq | sahviļize | salaħ | Требует сверки |
| 5261 | 110 | siqar | sijasat | sijasi(jab) | Требует сверки |
| 5321 | 111 | ssaoqri | ssaħ | ssaħir | Требует сверки |
| 5324 | 111 | ssaħirļi | s(s)aħat | ssajaq | Требует сверки |
| 5381 | 112 | ssuoqur | ssuḩmat | ssuj(i) | Требует сверки |
| 5457 | 114 | svaz | sa | sadax | Требует сверки |
| 5463 | 114 | saqur | salal | saqu | Требует сверки |
| 5488 | 115 | sooqro... | soħo | sojal | Требует сверки |
| 5646 | 118 | tahi | tahankize | taħzir | Требует сверки |
| 5687 | 118 | tarha | tarh... | tarix | Требует сверки |
| 5770 | 120 | toxxļuqe | toxxļize | tox(x)ter | Требует сверки |
| 5776 | 120 | tul | tujze | tukan | Требует сверки |
| 5850 | 121 | ţaoqur-karo | ţaoqral | ţahan | Требует сверки |
| 5851 | 121 | ţaoqral | ţahan | ţaḩel | Требует сверки |
| 5864 | 122 | ţaliih | ţaliḩ | ţali | Требует сверки |
| 5865 | 122 | ţaliḩ | ţali | ţalize | Требует сверки |
| 5903 | 123 | ţaxxel | ţaxal | ţaxdi | Требует сверки |
| 5909 | 123 | ţeḩ | Ţeħ-nusal | ţeħ-ⱬzun | Требует сверки |
| 5948 | 123 | ţinoq... | ţink | ţinķarize | Требует сверки |
| 5956 | 123 | ţiqva | ţiqal | ţiraqize | Требует сверки |
| 5969 | 124 | ţooqro... | ţohel | ţohib | Требует сверки |
| 5992 | 124 | ţorļize | ţorax̵ | ţoraze | Требует сверки |
| 6036 | 125 | uqdul | uhdize | uhi | Требует сверки |
| 6072 | 126 | uroqize | urhib | urhimes | Требует сверки |
| 6107 | 126 | vaqize | vahize | vahvahize | Требует сверки |
| 6109 | 126 | vahvahize | vah! | vahşi | Требует сверки |
| 6119 | 126 | vaqavaxxarize | vaķine | valahize | Требует сверки |
| 6126 | 126 | vaqvaze | vaqad | vaqan | Требует сверки |
| 6155 | 127 | vaxxcarize | vaxin | vaxine | Требует сверки |
| 6189 | 127 | vessaruxan | vesaruxan | vessize | Требует сверки |
| 6193 | 127 | vexxe | vex | vexe(r)xize | Требует сверки |
| 6202 | 127 | vioqize | vihine | viķize | Требует сверки |
| 6204 | 127 | viķize | vikķine | vilize | Требует сверки |
| 6211 | 128 | vistavka | vissad | vişşaruxan | Требует сверки |
| 6218 | 128 | vixxe | vixa-ļaze | vixa-rahize | Требует сверки |
| 6242 | 128 | voxxize | voqine | vsadnik | Требует сверки |
| 6405 | 131 | xxalaţ | xxala(t)ļi | xxala(t)ļize | Требует сверки |
| 6460 | 132 | Xxunzax | x(x)unzal | xxunzrul | Требует сверки |
| 6555 | 134 | x̵ahil | xahilļi | xahilļize | Требует сверки |
| 6583 | 134 | xanzar | xanza | xap | Требует сверки |
| 6591 | 134 | x̵arax̵ | xarbuz | xarccioƣa | Требует сверки |
| 6602 | 134 | x̵arx̵... | xasdeze | xasize | Требует сверки |
| 6616 | 135 | x̵azax̵ | xazix | xeberxize | Требует сверки |
| 6624 | 135 | xeroƣu | xerize | xerseze | Требует сверки |
| 6722 | 136 | zaqal | zahir | zahirļi | Требует сверки |
| 6728 | 137 | zaħmat-ħaq | zaħip | zaħipļi | Требует сверки |
| 6771 | 137 | zinqize | zinkķarize | zinkķize | Требует сверки |
| 6794 | 138 | zvaroqeze | zvari | zvarize | Требует сверки |
| 6796 | 138 | zvarize | za | zabgo | Требует сверки |
| 6802 | 138 | zaqallize | zahil | zahilli | Требует сверки |
| 6853 | 139 | zobaoqobaze | zobaj | zobaze | Требует сверки |
| 6865 | 139 | zuroqize | zuri | zurnal | Требует сверки |
| 6894 | 140 | ⱬiķize | ⱬikⱬikize | ⱬil | Требует сверки |
| 6897 | 140 | ⱬili-qverq | ⱬili | ⱬilize | Требует сверки |
| 6916 | 140 | ⱬuⱬdul | zⱬabuzⱬanxdize | zⱬabuzⱬdize | Требует сверки |
