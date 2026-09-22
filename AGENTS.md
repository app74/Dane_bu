# AGENTS.md

## Projekt

Vytvor webovú aplikáciu na prípravu platobných údajov pre slovenské dane. Používateľ vyberie daň, obdobie a zadá daňový subjekt; aplikácia vytvorí cieľový IBAN, variabilný symbol, splatnosť a zrozumiteľný rozpis výpočtu.

Primárne podporované platby MVP:

- DPH (mesačný a štvrťročný platiteľ),
- daň z príjmov právnickej osoby,
- daň z príjmov fyzickej osoby,
- preddavky na daň z príjmov,
- daň z motorových vozidiel,
- zrážková daň,
- ostatné druhy iba vtedy, keď je pravidlo potvrdené oficiálnym zdrojom.

## Povinné bezpečnostné zásady

Toto je finančne citlivá aplikácia. Nevymýšľaj predčíslia účtov, formáty VS, lehoty ani mapovanie identifikátorov. Každé produkčné pravidlo musí mať:

- názov a verziu,
- dátum platnosti `valid_from` a voliteľne `valid_to`,
- URL oficiálneho zdroja Finančnej správy SR alebo právneho predpisu,
- dátum posledného overenia,
- automatické testovacie príklady.

Ak pravidlo nie je potvrdené, označ ho ako nepodporované. Neprodukuj odhadovaný účet ani VS. V UI vždy zobraz upozornenie, že používateľ má údaje pred úhradou porovnať s oficiálnymi platobnými inštrukciami Finančnej správy.

Neimplementuj obchádzanie CAPTCHA, automatizované získavanie OÚD zo služby, ktorá ho chráni, ani scraping v rozpore s podmienkami služby. V MVP používateľ zadá OÚD ručne alebo ho vyberie z lokálne uloženej evidencie. IČO, DIČ ani IČ DPH samy osebe nepovažuj za zdroj, z ktorého možno OÚD vypočítať.

Nevykonávaj bankovú platbu. Aplikácia iba pripravuje a exportuje platobné údaje.

## Technologický základ

- Backend: Python 3.12+, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic.
- Frontend: React + TypeScript + Vite.
- Databáza pre MVP: SQLite; návrh musí umožniť neskorší prechod na PostgreSQL.
- Testy backendu: pytest; testy frontendu: Vitest + Testing Library; aspoň jeden end-to-end smoke test v Playwright.
- Formátovanie a kontroly: Ruff pre Python, ESLint/Prettier pre TypeScript.
- Lokálne spustenie: Docker Compose a zároveň dokumentované spustenie bez Dockeru.
- Jazyk rozhrania a používateľskej dokumentácie: slovenčina. Identifikátory v kóde: angličtina.

Ak repozitár už obsahuje zvolený kompatibilný stack, rešpektuj ho a neprerábaj ho bez dôvodu.

## Architektúra

Oddeľ doménovú logiku od API, databázy a UI. Výpočet musí byť deterministická čistá doménová služba, ktorú možno testovať bez servera a databázy.

Odporúčané moduly backendu:

- `domain/identifiers` – normalizácia a syntaktická validácia IČO, DIČ a IČ DPH,
- `domain/iban` – zostavenie slovenského účtu/IBAN a kontrola MOD 97,
- `domain/payment_symbols` – tvorba a validácia VS,
- `domain/tax_rules` – výber verzie pravidla podľa druhu platby a obdobia,
- `domain/due_dates` – výpočet splatnosti iba pre overené pravidlá,
- `application/payment_instructions` – orchestrace prípadu použitia,
- `infrastructure` – databáza, import/export a konfigurácia,
- `api` – HTTP rozhranie bez doménových výpočtov v routach.

Daňové pravidlá ukladaj dátovo (verziované YAML/JSON alebo seedované tabuľky), nie ako roztrúsené podmienky v UI. Historické pravidlá nemaž; pridaj novú verziu s obdobím platnosti.

## Doménové požiadavky

Model daňového subjektu minimálne obsahuje voliteľné `ico`, `dic`, `ic_dph`, povinné používateľom overené `oud` a názov subjektu. Umožni evidovať viac subjektov. Citlivé údaje neloguj.

Platobná inštrukcia musí obsahovať minimálne:

- subjekt a použitý OÚD,
- druh dane a typ platby,
- zdaňovacie obdobie,
- sumu a menu EUR,
- číslo účtu v domácom tvare, výsledný IBAN a výsledok kontroly IBAN,
- variabilný symbol,
- dátum splatnosti, ak je bezpečne určiteľný,
- verziu, zdroj a dátum overenia každého použitého pravidla,
- čas vytvorenia a upozornenie na kontrolu.

Suma sa počíta typom `Decimal`, nikdy `float`. Čísla účtov, OÚD, VS a identifikátory ukladaj ako text, aby sa nestratili úvodné nuly.

Validácia formátu identifikátora nie je potvrdenie jeho existencie. V UI tieto dva pojmy jasne odlišuj.

## API a UI MVP

Navrhni stabilné API aspoň pre:

- správu lokálnej evidencie subjektov,
- zoznam podporovaných druhov daní a verzií pravidiel,
- náhľad platobnej inštrukcie bez uloženia,
- uloženie a zobrazenie histórie vytvorených inštrukcií,
- health check.

UI má obsahovať sprievodcu: subjekt → druh dane/platby → obdobie → suma → kontrolný náhľad. Výsledok musí ísť skopírovať a vytlačiť. QR PAY by square pridaj až po overení použitej knižnice a formátu testovacími vektormi; nesmie blokovať základné MVP.

## Testovanie

Pre každé pravidlo vytvor:

- pozitívny príklad z oficiálneho zdroja, ak je dostupný,
- hraničné obdobia platnosti,
- chybné alebo neúplné vstupy,
- kontrolu dĺžky a formátu VS,
- kontrolu IBAN cez MOD 97 a aspoň jeden nezávislý testovací vektor.

Testy nesmú iba zopakovať rovnaký algoritmus ako implementácia. Pri opravách najprv pridaj regresný test. Pred odovzdaním spusti lint, typovú kontrolu, unit testy, integračné testy a produkčný build frontendu.

## Pracovný postup pre Codex

1. Najprv si prečítaj tento súbor a `plan.md`, potom skontroluj existujúci repozitár a lokálne pokyny.
2. Pred implementáciou pravidiel vyhľadaj aktuálne oficiálne zdroje. Do kódu zapisuj iba potvrdené údaje; sekundárny zdroj používaj nanajvýš na orientáciu.
3. Postupuj po malých, overiteľných vertikálnych rezoch a po každej etape aktualizuj stav v `plan.md`.
4. Nerob veľké prepisy nesúvisiace s aktuálnou etapou. Zachovaj zmeny používateľa.
5. Každú zmenu zakonči spustením relevantných testov a stručným zápisom výsledku.
6. Ak chýba údaj, ktorý mení finančný výsledok, zastav sa a vyžiadaj rozhodnutie alebo označ funkciu ako nepodporovanú; nepouži domnienku.

## Kritériá hotového MVP

MVP je hotové iba vtedy, keď sa dá lokálne spustiť podľa README, používateľ vie ručne uložiť subjekt s OÚD, vytvoriť inštrukciu pre všetky deklarované podporované platby, vidí zdroj/verziu pravidla a upozornenie, vstupy sú validované a všetky povinné kontroly prejdú. Deklarovaný zoznam podporovaných daní musí presne zodpovedať implementovaným a overeným pravidlám.
