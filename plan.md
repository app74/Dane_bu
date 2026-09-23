# Plán implementácie – Generovanie úhrad pre dane

## Cieľ a hranice MVP

Cieľom je lokálna webová aplikácia, ktorá z používateľom potvrdeného OÚD, vybraného druhu dane, obdobia a sumy pripraví kontrolovateľnú platobnú inštrukciu. MVP platby nevykonáva a automaticky nezískava OÚD cez CAPTCHA.

Stavové značky: `[ ]` nezačaté, `[~]` rozpracované, `[x]` hotové, `[!]` blokované.

## 0. Overenie vstupov a zdrojov

- [x] Overiť aktuálne oficiálne dokumenty Finančnej správy SR pre účty a variabilné symboly.
- [x] Zostaviť prvú maticu: druh dane × typ platby × obdobie × predčíslie účtu × formát VS × splatnosť.
- [x] Ku každému pravidlu zapísať URL, dátum overenia a obdobie platnosti.
- [x] Označiť nejasné alebo nepotvrdené kombinácie ako nepodporované.
- [x] Pripraviť schválené testovacie vektory bez reálnych citlivých údajov.

Výstup etapy: `docs/rules-sources.md` a prvá verzia dátového číselníka pravidiel.

## 1. Základ repozitára

- [x] Vytvoriť adresáre `backend`, `frontend`, `docs` a koreňové pomocné súbory.
- [x] Inicializovať FastAPI, React/TypeScript/Vite, SQLite a migrácie Alembic.
- [x] Nastaviť Ruff, pytest, ESLint, Prettier, Vitest a typové kontroly.
- [x] Pridať `.env.example`; žiadne tajomstvá necommitovať.
- [x] Pridať Docker Compose a health check.
- [x] Vytvoriť README so spustením cez Docker aj bez neho.

Akceptácia: čistý checkout sa spustí podľa README a backend aj frontend majú prechádzajúci smoke test.

## 2. Doménové jadro

- [x] Implementovať normalizáciu a syntaktickú validáciu IČO, DIČ a IČ DPH.
- [x] Implementovať model OÚD bez pokusu odvodiť ho z identifikátora.
- [x] Implementovať zostavenie domáceho bankového účtu z predčíslia, OÚD a kódu banky.
- [x] Implementovať prevod na slovenský IBAN a validáciu MOD 97.
- [x] Implementovať hodnotové objekty pre obdobie, sumu v EUR a VS.
- [x] Načítať verziované pravidlá a vybrať pravidlo podľa dátumu/obdobia.
- [x] Pri chýbajúcom pravidle vrátiť bezpečnú doménovú chybu, nie odhad.

Akceptácia: doménové unit testy pokrývajú platné, chybné a hraničné prípady; logika nevyžaduje HTTP ani databázu.

## 3. Dátový model a API

- [x] Navrhnúť tabuľky subjektov, verzií pravidiel a platobných inštrukcií.
- [x] Ukladať čísla účtov a identifikátory ako text, sumy presne bez `float`.
- [x] Vytvoriť CRUD pre lokálnu evidenciu subjektov.
- [x] Vytvoriť endpoint pre zoznam skutočne podporovaných platieb.
- [x] Vytvoriť endpoint na náhľad inštrukcie bez uloženia.
- [x] Vytvoriť endpoint na uloženie a zobrazenie histórie.
- [x] Nezapisovať citlivé hodnoty do aplikačných logov.

Akceptácia: integračné testy overia úspešný výpočet, validačné chyby, nepodporované pravidlo a prácu s databázou.

## 4. Používateľské rozhranie

- [x] Vytvoriť slovenský sprievodca: subjekt → daň → obdobie → suma → kontrola.
- [x] Umožniť pridať/upraviť subjekt a potvrdiť OÚD.
- [x] Zobrazovať iba podporované kombinácie alebo ich jasne označiť.
- [x] Na výsledku zobraziť IBAN, VS, sumu, splatnosť, zdroj a verziu pravidla.
- [x] Pridať kopírovanie jednotlivých údajov a tlačiteľný pohľad.
- [x] Zreteľne zobraziť upozornenie na overenie pred platbou.
- [x] Odlíšiť syntakticky platný identifikátor od úradne overeného údaja.

Akceptácia: používateľ dokončí hlavný scenár bez ručného prepisovania vypočítaných hodnôt; UI má testy chýb a prázdnych stavov.

## 5. Podpora daní po vertikálnych rezoch

Každý rez zahŕňa oficiálny zdroj, dátové pravidlo, backend test, API test a UI scenár.

- [x] DPH – mesačné obdobie (konkrétne potvrdené obdobie marec 2026).
- [x] DPH – štvrťročné obdobie (konkrétne potvrdené obdobie I. štvrťrok 2026).
- [x] Daň z príjmov právnickej osoby a konkrétne potvrdené preddavky DPPO 2026.
- [x] Daň z príjmov fyzickej osoby (priznanie za 2025); preddavky zostávajú samostatné.
- [x] Daň z motorových vozidiel.
- [x] Zrážková daň – iba konkrétny rez dividend vyplatených v máji 2026.
- [ ] Ďalšie dane až po samostatnom overení a testoch.

Akceptácia: verejne deklarovaný zoznam podporovaných platieb sa generuje z aktívnych overených pravidiel, nie z marketingového textu.

## 6. Audit, export a kvalita

- [x] Ku každej inštrukcii uložiť snapshot použitých pravidiel a ich zdrojov.
- [x] Pridať export/tlač do formátu vhodného pre účtovníka; PDF nie je podmienkou MVP.
- [x] Pridať end-to-end smoke test hlavného scenára.
- [x] Overiť prístupnosť formulára, klávesnicové ovládanie a responzívnosť.
- [x] Skontrolovať chybové správy a slovenskú terminológiu.
- [x] Spustiť bezpečnostnú a dependency kontrolu.
- [x] Otestovať zálohu a obnovu lokálnej databázy.

Akceptácia: lint, typové kontroly, všetky testy a produkčný build prejdú; README opisuje limity a zálohovanie.

## 7. Voliteľné rozšírenia po MVP

- [ ] PAY by square QR iba s overenou knižnicou a nezávislými testovacími vektormi.
- [ ] Import/export subjektov v CSV s validáciou a náhľadom.
- [ ] PostgreSQL a viac používateľov s rolami.
- [ ] Bezpečné šifrovanie údajov a správa záloh pre serverové nasadenie.
- [ ] Administrácia číselníka s procesom dvojitého schválenia pravidiel.
- [ ] Notifikácia pri blížiacej sa zmene alebo skončení platnosti pravidla.

## 8. Nasadenie na Vercel (vercel.app)

Cieľ: prevádzka tej istej aplikácie na Verceli bez zmeny lokálneho, Docker a Windows server nasadenia. Postup pre správcu je v `manual.md`, kapitola 11.

- [x] Overiť aktuálnu dokumentáciu Vercelu (Python runtime, FastAPI, Services, limity funkcií, Deployment Protection, Fair Use) a Neon integrácie.
- [x] `vercel.json` so službami `frontend` (Vite, `frontend/`) a `backend` (FastAPI, `backend/`); prepis `/api/*` na backend, ostatné na frontend.
- [x] `backend/vercel_app.py` pripája API pod `/api`, lebo Services odovzdávajú pôvodnú cestu vrátane prefixu; OpenAPI/docs sú na Verceli vypnuté.
- [x] Build backendu kopíruje `docs/tax-rules.json` do `backend/docs/` (gitignored); `RULES_PATH` hľadá repozitárové/Docker umiestnenie, potom kópiu, alebo `TAX_RULES_PATH`.
- [x] Postgres: závislosť `psycopg[binary]`, normalizácia `postgres://` → `postgresql+psycopg://`, malý pool s `pool_pre_ping`.
- [x] Alembic používa `DATABASE_URL` namiesto pevnej hodnoty v `alembic.ini`; `create_all` beží iba pre SQLite.
- [x] Prístup: spoločné heslo `APP_PASSWORD` + `SESSION_SECRET`, podpísaná HttpOnly/Secure/SameSite=Strict cookie na 8 hodín, zmena hesla zneplatní relácie; na Verceli bez konfigurácie API vracia 503 (fail closed), verejný je iba `/health`.
- [x] Frontend: `VITE_API_URL` (Vercel build `/api`, lokálne pôvodné `http://127.0.0.1:8000`), spoločný `apiFetch`, prihlasovacia obrazovka, odhlásenie, návrat na prihlásenie pri 401.
- [x] Vyhľadanie v exportoch FS vypínateľné cez `FS_LOOKUP_ENABLED`; na Verceli predvolene vypnuté s hlásením o ručnom zadaní OÚD.
- [x] Testy: backend (auth, `/api` mount, fail-closed, URL databázy, prepínač lookupu), frontend (prihlásenie, chybné heslo, vypršanie relácie, 503).
- [x] Dokumentácia: `manual.md` kapitola 11, sekcia Vercel v README, premenné v `.env.example` (bez hodnôt).
- [ ] Vytvoriť Vercel projekt (plán Pro – firemné použitie), Neon databázu v EÚ a nastaviť Environment Variables.
- [ ] Spustiť `alembic upgrade head` proti Neon (priame pripojenie) – migrácia `0002_unique_subjects` zatiaľ nebola overená na živom Postgrese.
- [ ] Prvé nasadenie a kontrola podľa `manual.md` 11.7; overiť, že build backendu vidí `../docs/tax-rules.json`.
- [ ] Preniesť subjekty cez CSV export/import (najprv test na jednom riadku) a CSV súbor zmazať.
- [ ] Voliteľne: rate limit pre `/api/auth/login` vo Vercel Firewall, samostatný Neon branch pre Preview, overenie limitov pred zapnutím `FS_LOOKUP_ENABLED`.

Akceptácia: na `*.vercel.app` sa bez prihlásenia nedajú čítať ani meniť dáta, po prihlásení funguje hlavný scenár, dáta prežijú nové nasadenie a lokálne kontroly (pytest, Ruff, Vitest, build, ESLint, Playwright) prechádzajú.

## Priebežný denník rozhodnutí

Rozšírenie na požiadanie používateľa (2026-09-22): vyhľadanie podľa IČO/DIČ z oficiálneho XML registra FS a doplnenie OÚD z exportu účtov platiteľov DPH. Presné spojenie cez IČO, kontrola IBAN, odmietnutie neaktuálneho exportu a nejednoznačných účtov. Pri chýbajúcich údajoch zostáva ručné zadanie. Bez automatizácie formulára chráneného CAPTCHA. Licencie a prevádzkové limity sú uvedené v README.

Oprava duplicít (2026-09-23): opakované uloženie rovnakého subjektu vracia existujúci záznam (HTTP 200), tlačidlo sa počas požiadavky deaktivuje a backend chráni OÚD/IČO/DIČ/IČ DPH unikátnymi indexmi. Migrácia `0002_unique_subjects` zlúčila tri zhodné záznamy Neopublic a presmerovala ich platobnú históriu bez mazania auditných snapshotov. Konfliktné identifikátory vracajú HTTP 409.

Oprava izolácie testov (2026-09-23): testy už používajú dočasnú SQLite databázu cez `backend/tests/conftest.py`; nesmú zapisovať do `backend/app.db`. Testovacie subjekty boli z aktívnej databázy odstránené, zostali iba Neopublic a CONSULTIA.

Overenie rozšírenia: 43 backendových testov, Ruff, 5 frontendových testov, TypeScript/produkčný build, ESLint, Prettier s `--end-of-line auto` pre Windows checkout a nový Playwright scenár výberu/uloženia cez DIČ prešli. Testovacia databáza bola izolovaná; Playwright používal simulované API bez zápisu do používateľských dát. Reálny export bol overený vyhľadaním cez IČO aj DIČ so zhodným OÚD. Backend bol reštartovaný a `/health` vracia `ok`.

Codex sem pri práci dopĺňa stručné datované záznamy, ktoré ovplyvňujú návrh alebo finančný výsledok.

| Dátum | Rozhodnutie | Dôvod / zdroj |
| --- | --- | --- |
| 2026-09-22 | Pravidlá a zdroje sa vedú v `docs/rules-sources.md` a `docs/tax-rules.json`; nepotvrdené kombinácie negenerujú údaje. | Overené iba na oficiálnych stránkach Finančnej správy SR. |
| 2026-09-22 | Etapa 1 má vytvorený základ FastAPI, React/Vite, SQLite/Alembic konfiguráciu, Compose a README. | Lokálne overenie je zatiaľ blokované: v prostredí nie je dostupný `python` ani `npm`. |
| 2026-09-22 | Etapa 1 obsahuje aj Vitest, Playwright smoke test, ESLint/Prettier konfiguráciu a Alembic template. | Testy sú pripravené, ale ich vykonanie čaká na dostupné runtime nástroje. |
| 2026-09-22 | Doménový rez validácie identifikátorov a IBAN je čistý Python bez HTTP/databázy; OÚD sa nikdy neodvodzuje z IČO/DIČ. | Bezpečnostná zásada z `AGENTS.md`; testovací OÚD je syntetický. |
| 2026-09-22 | Po inštalácii runtime bol opravený setuptools discovery konflikt medzi balíkmi `app` a `alembic`. | Prvý test odhalil chybu pri `pip install -e ".[dev]"`. |
| 2026-09-22 | Backend: 7 testov prešlo a Ruff je čistý. Frontend: produkčný build, Vitest, ESLint a Prettier prešli. | Opravené typy Reactu, Vitest setup a Vite CSS deklarácia. |
| 2026-09-22 | Po inštalácii Pythonu a Node.js prešli backendové testy/lint a frontend build/test/lint/format check. | Playwright E2E zatiaľ nebol spustený, pretože nebol nainštalovaný browser runtime. |
| 2026-09-22 | Chromium runtime je nainštalovaný; E2E konfigurácia bola presunutá na koreňový npm projekt a doplnený automatický Vite web server. | Prvé spustenie odhalilo chýbajúci koreňový `@playwright/test`. |
| 2026-09-22 | Playwright E2E smoke test prešiel: 1 test, 1 worker. | Overený štart frontendu a zobrazenie úvodnej obrazovky s upozornením. |
| 2026-09-22 | Pravidlá sa načítavajú z JSON s platnosťou, stavom, zdrojom a dátumom overenia; neoverené pravidlá výber odmietne. | Bezpečnostná zásada: finančný výsledok sa nesmie odhadovať. |
| 2026-09-22 | Pridané Decimal sumy, jednoznačné obdobie a 10-miestne VS pre potvrdené mesačné/štvrťročné vzory. | Vzory vychádzajú z oficiálneho zoznamu VS Finančnej správy SR; iné prefixy sa odmietnu. |
| 2026-09-22 | Endpoint `/tax-rules` zobrazuje iba pravidlá so stavom `supported` a vracia zdroj, platnosť a dátum overenia. | Verejný zoznam nesmie deklarovať neoverené kombinácie. |
| 2026-09-22 | Pridaná SQLite evidencia subjektov s textovým OÚD a syntaktickou validáciou identifikátorov. | OÚD sa ukladá ručne zadané; žiadne odvodzovanie ani logovanie citlivých hodnôt. |
| 2026-09-22 | CRUD subjektov je kompletný: vytvorenie, zoznam, detail, úprava a odstránenie. | Všetky operácie používajú rovnakú syntaktickú validáciu a OÚD ostáva textový údaj. |
| 2026-09-22 | Náhľad inštrukcie podporuje iba potvrdené pravidlá DPPO/FO z priznania 2025 a DMV 2025; vracia IBAN, MOD-97 výsledok, VS, splatnosť, zdroj a upozornenie. | Nepotvrdené DPH a preddavkové kombinácie endpoint odmieta. |
| 2026-09-22 | Frontend bol napojený na CRUD subjektov a endpoint náhľadu; produkčný build, Vitest, ESLint a Prettier prešli. | CORS je obmedzený iba na lokálne Vite originy. |
| 2026-09-22 | Pridané uloženie platobnej inštrukcie ako JSON snapshot a endpointy `/payment-instructions` pre uloženie/históriu. | História uchováva použité pravidlo a výsledné údaje nezávisle od budúcich zmien číselníka. |
| 2026-09-22 | Frontend načítava históriu, umožňuje uložiť aktuálny náhľad a zobrazuje posledné uložené inštrukcie. | Uloženie je explicitná akcia používateľa. |
| 2026-09-22 | Pridaná prvá Alembic migrácia pre subjekty a snapshoty platobných inštrukcií; Alembic používa SQLAlchemy metadata. | Databázová schéma je opakovateľná aj bez `create_all`. |
| 2026-09-22 | Alembic offline SQL a Docker Compose konfigurácia prešli kontrolou bez zásahu do existujúcej databázy. | Overená generovaná schéma oboch tabuliek a `alembic_version`. |
| 2026-09-22 | Backendový Docker štart vykoná `alembic upgrade head` pred Uvicorn serverom; pridaný `.dockerignore`. | Kontajner tak inicializuje schému opakovateľne pri čistom volume. |
| 2026-09-22 | Kompletná nedockerová regresia prešla: backend 23 testov/Ruff, frontend build/2 testy/lint/format a Playwright 1 smoke test. | Docker image stále čaká na spustený Docker Desktop engine. |
| 2026-09-22 | VS a splatnosť podporovaných pravidiel sú uložené v `docs/tax-rules.json`; API ich už neobsahuje ako hardcoded hodnoty. | Pravidlá zostávajú dátové, verziované a auditovateľné. |
| 2026-09-22 | Pridané potvrdené DPH pravidlá pre marec 2026 a I. štvrťrok 2026 vrátane účtu `500240`, VS a splatnosti. | Oficiálny zoznam VS Finančnej správy SR za II. štvrťrok 2026. Ostatné obdobia ostávajú nepodporované. |
| 2026-09-22 | DPH mesačný aj štvrťročný rez má samostatný API pozitívny test a dokumentačný riadok. | Overenie chráni pred zámenou VS `1100032026` a `1100412026`. |
| 2026-09-22 | Pridané samostatné pravidlá FO rezident/nerezident za 2025 s predčíslím `500208`/`500216`. | Oficiálna informácia Finančnej správy SR 5/FO/2026/IM. |
| 2026-09-22 | FO rezident aj nerezident majú samostatný API pozitívny test. | Znižuje riziko zámeny účtov pri rovnakom VS. |
| 2026-09-22 | Pridané konkrétne DPPO preddavky za január a I. štvrťrok 2026; suma sa iba zadáva, nevypočítava. | Oficiálny zoznam VS Finančnej správy SR za I. štvrťrok 2026. |
| 2026-09-22 | Po rozšírení číselníka prešla kompletná regresia: backend 28 testov/Ruff, frontend build/2 testy/lint/format, E2E 1 test, npm audit 0 zraniteľností. | `tax-rules.json` je validný JSON. |
| 2026-09-22 | Vývojová závislosť `httpx` je obmedzená na `<0.28`; backend 28 testov a Ruff opäť prešli. | Kompatibilnejšie testovanie FastAPI TestClient; upstream Starlette stále vydáva deprecation warning. |
| 2026-09-22 | Zdrojová matica bola zosúladená s číselníkom pre FO rezidenta/nerezidenta a DPPO preddavky. | Každé aktuálne podporované pravidlo má samostatný dokumentačný riadok. |
| 2026-09-22 | Načítanie číselníka kontroluje auditné minimum každého podporovaného pravidla: oficiálny FS zdroj, platnosť, VS a predčíslie účtu. | Chybný číselník sa odmietne pred výpočtom. |
| 2026-09-22 | Pridané negatívne API testy pre zápornú/nepresnú/nečíselnú sumu a neexistujúci subjekt. | Neplatný alebo neúplný vstup nevytvorí inštrukciu. |
| 2026-09-22 | Frontend dopĺňa úpravu a odstránenie vybraného subjektu cez existujúce CRUD endpointy; build, testy, lint a formátovanie prešli. | OÚD sa pri úprave znovu validuje backendom. |
| 2026-09-22 | Pridaný detail historickej inštrukcie `GET /payment-instructions/{id}`, ktorý vracia uložený snapshot bez prepočtu. | História ostáva stabilná aj pri neskoršej zmene číselníka. |
| 2026-09-22 | Playwright E2E spúšťa frontend aj backend a testuje hlavný scenár vytvorenia náhľadu, nie iba statické načítanie stránky. | Reálne overenie lokálneho API pre používateľský tok. |
| 2026-09-22 | E2E hlavný scenár prešiel spolu s úvodným testom: 2 testy, frontend + FastAPI backend. | Test overuje uloženie subjektu, zadanie sumy a zobrazenie 10-miestneho VS v náhľade. |
| 2026-09-22 | Prvý Docker štart odhalil chýbajúci `PYTHONPATH` pri Alembic importe; Dockerfile doplnený o `PYTHONPATH=/app`. | Backend image sa zostavil, oprava je pripravená na opakovaný štart. |
| 2026-09-22 | Docker Compose po oprave úspešne beží; backend health check vrátil `ok` a frontend odpovedal HTTP 200. | Overené kontajnery backend/frontend a štart Alembic migrácie. |
| 2026-09-22 | `pip check` a npm audit backendového/frontendového aj koreňového projektu prešli bez nájdených problémov; Playwright smoke test opäť prešiel. | Základná dependency a E2E kontrola MVP. |
| 2026-09-22 | Dopĺňa sa test skutočného frontendového sprievodcu s mockovaným API; časové pečiatky subjektov používajú timezone-aware UTC. | Odstránenie placeholder testu a deprecation warningov. |
| 2026-09-22 | Docker image backendu kopíruje `docs/tax-rules.json` do `/docs`; Docker Compose znovu zostavený a `/tax-rules` vracia 8 podporovaných pravidiel. | Opravený Docker-only rozdiel, pri ktorom backend bez číselníka vracal HTTP 500. Docker Playwright smoke test: 2/2 prešli. |
| 2026-09-22 | Aktualizovaný stav etáp 3–5 podľa implementácie; kompletná lokálna regresia prešla: backend 31 testov, Ruff, frontend build/2 testy/lint/format. | Zostávajú len finálne auditné/exportné kontroly a doplnenie zrážkovej dane až po overení oficiálneho pravidla. |
| 2026-09-22 | Pridaný textový export aktuálneho náhľadu pre účtovníka; obsahuje subjekt, OÚD, účet, IBAN, VS, sumu, splatnosť, zdroj, dátum overenia a upozornenie. | Export iba prenáša už vypočítané údaje, nemení doménové pravidlá. Frontend build, testy, lint, formátovanie a E2E 2/2 prešli. |
| 2026-09-22 | Pridané viditeľné focus štýly, responzívne rozloženie pre malé obrazovky a README postup zálohy SQLite. | Statická kontrola formulára a CSS prešla; databázová obnova ostáva rozpracovaná, aby sa nezasiahlo do aktívneho súboru. |
| 2026-09-22 | Záloha `backend/app.db` bola vytvorená do dočasného umiestnenia a overená zhodou SHA-256 s originálom; postup obnovy je spätné skopírovanie súboru po zastavení backendu. | Aktívna databáza nebola menená. Dočasný testovací súbor je v `C:\Users\PC\AppData\Local\Temp\danove-platby-app.db.backup-test`. |
| 2026-09-22 | Záverečná regresia prešla: `pip check`, backend 31 testov, Ruff, npm audit pre koreň/frontend, frontend production build a Playwright E2E 2/2. | Kontrolný zoznam MVP je splnený pre aktuálne deklarované pravidlá; zostávajúce rozšírenia (napr. zrážková daň, QR PAY) ostávajú mimo MVP bez samostatného oficiálneho overenia. |
| 2026-09-22 | Pridaný prvý bezpečný rez zrážkovej dane: dividendy vyplatené v máji 2026, predčíslie `500267`, VS `1700052026`, splatnosť `15.06.2026`. | Výhradne oficiálna informácia FS SR 6/PO/2026/IM; API test prešiel a Docker číselník po rebuild-e vracia 9 pravidiel. Všeobecné zrážkové obdobia zostávajú nepodporované. |
| 2026-09-22 | Pridaný E2E scenár zrážkovej dane; Playwright teraz overuje úvodnú stránku, hlavný náhľad a konkrétny VS zrážkovej dane: 3/3 prešli v Dockeri. | Vertikálny rez má pravidlo, API test aj používateľský UI scenár. |
| 2026-09-22 | Docker Compose backend dostal aktívny healthcheck na `/health`; kontajner je po štarte v stave `healthy` a endpoint vracia `ok`. | Compose teraz overuje dostupnosť API, nielen existenciu procesu. |
| 2026-09-22 | Frontend v Compose používa `depends_on` s podmienkou `service_healthy` pre backend. | Pri čistom štarte sa znižuje riziko prvotnej chyby načítania API; oba kontajnery po reštarte ostali dostupné. |
| 2026-09-22 | Regresia po Compose zmene prešla: Docker Playwright 3/3, frontend production build a backend kontajner `healthy`. | Orchestrácia neporušila hlavný tok ani nový rez zrážkovej dane. |
| 2026-09-22 | `docker compose config --quiet` a validácia `docs/tax-rules.json` prešli; Docker backend/frontend ostávajú spustené. | Overená syntaktická reprodukovateľnosť konfigurácie a číselníka. |
| 2026-09-22 | Auditný skript porovnal 9 podporovaných pravidiel v JSON s 9 položkami API a overil oficiálnu doménu zdroja, platnosť, VS a predčíslie účtu každého pravidla. | Katalóg a verejný zoznam pravidiel sú konzistentné. |
| 2026-09-22 | Skontrolované používateľské texty a validačné hlášky MVP; formulár používa slovenskú terminológiu a chybové stavy sú označené `role=alert`. | Kontrola pokrýva nedostupný backend, neplatný OÚD, neplatnú sumu, zlyhanie CRUD a náhľadu/uloženia. |
| 2026-09-22 | Export TXT uvoľňuje objektovú URL až po odovzdaní sťahovania prehliadaču. | Odstránené riziko, že okamžité `revokeObjectURL` preruší sťahovanie; build, lint a formátovanie prešli. |
| 2026-09-22 | Po oprave exportu prešli Vitest 2/2 a Docker Playwright 3/3; backend ostáva `healthy`. | Potvrdené, že hlavný tok a zrážková daň zostali funkčné. |
| 2026-09-22 | Frontendový test overuje vytvorenie náhľadu a spustenie TXT exportu; Vitest teraz prechádza 3/3 testami, ESLint a Prettier tiež. | Export je pokrytý aj izolovaným UI testom, nielen manuálnym kódom. |
| 2026-09-22 | Test exportu izoluje `HTMLAnchorElement.click`, takže Vitest už nevypisuje falošné JSDOM upozornenie o navigácii. | Testy zostávajú 3/3 úspešné bez rušivého výstupu. |
| 2026-09-22 | Playwright E2E overuje aj skutočný download `platobne-udaje.txt`; po reštarte frontendového Vite kontajnera prešli všetky 3 testy. | Reštart bol potrebný na načítanie nového zdrojového kódu v dlhšie bežiacom dev kontajneri. |
| 2026-09-22 | Záverečný Docker smoke: `/health` = `ok`, API poskytuje 9 pravidiel, frontend odpovedá HTTP 200 a oba kontajnery bežia. | Prostredie je pripravené na lokálne používanie MVP. |
| 2026-09-22 | Pridaný frontendový Compose healthcheck na `127.0.0.1:5173`; prvá varianta s `localhost` odhalila IPv6 rozdiel v Alpine a bola opravená. Oba kontajnery sú `healthy`. | Healthcheck teraz overuje reálne IPv4 počúvanie Vite servera. |
| 2026-09-22 | Po oprave frontendového healthchecku prešli Docker Playwright testy 3/3, backend health = `ok` a frontend odpovedá HTTP 200; oba kontajnery sú `healthy`. | Potvrdený čistý stav po recreate kontajnera. |
| 2026-09-23 | Nasadenie na Vercel cez Vercel Services: frontend `/`, FastAPI `/api/*`; backend pripojený pod `/api` v `backend/vercel_app.py`. | Dokumentácia Vercel Services: služba dostáva pôvodnú cestu vrátane prefixu. Services sú Beta. |
| 2026-09-23 | Na Verceli sa nepoužíva SQLite; databáza je Neon Postgres, schému spravuje iba Alembic nad `DATABASE_URL`. | Funkcie Vercelu nemajú trvalý disk. Rozhodnutie používateľa: Neon. |
| 2026-09-23 | Prístup chráni aplikačné heslo (`APP_PASSWORD`, `SESSION_SECRET`); na Verceli bez nich API vracia 503. | Aplikácia dovtedy nemala autentifikáciu; verejná vercel.app adresa by sprístupnila OÚD. Rozhodnutie používateľa: heslo v aplikácii. |
| 2026-09-23 | Vyhľadanie v exportoch FS je na Verceli predvolene vypnuté (`FS_LOOKUP_ENABLED`). | ~65 MB export a index na každej novej inštancii riskujú limit 300 s (Hobby). Rozhodnutie používateľa. |
| 2026-09-23 | Firemné nasadenie vyžaduje plán Vercel Pro/Enterprise. | Vercel Fair Use Guidelines: Hobby iba na nekomerčné osobné použitie. |
| 2026-09-23 | Overenie: backend 63 testov + Ruff, frontend 12 testov + build (aj s `VITE_API_URL=/api`) + ESLint, Playwright 4/4 proti lokálnemu backendu, Alembic na SQLite a offline SQL pre Postgres (0001). Prettier hlási iba pôvodný nesúlad v `src/main.test.tsx`. | Docker nebežal, živý Postgres a samotné nasadenie na Vercel zatiaľ neoverené. |
| 2026-09-23 | Opravená poškodená diakritika v dvoch chybových hláškach frontendu (uloženie subjektu). | Znaky boli nahradené `?`; Vitest 12/12, ESLint a TypeScript po oprave prešli. |
| 2026-09-23 | Sieťový prístup: backend číta doplnkové CORS adresy z `CORS_ORIGINS`; frontend bez `VITE_API_URL` volá backend na porte 8000 hostiteľa stránky, ručná úprava `main.tsx` z manuálu odpadá. Manuál doplnený o rezerváciu IP a obmedzenie firewallu na doménový profil. | Iné PC by inak dostali CORS chybu; lokálna verzia nemá prihlásenie, preto obmedziť sieť. Backend 64 testov, Vitest 12/12. |
| 2026-09-23 | QR PAY by square sa generuje vo formáte 1.1.0 (`src/qr.ts`); meno príjemcu ostáva podľa rozhodnutia používateľa prázdne. | bysquare 4.0.1 vo formáte 1.2.0 prázdne meno odmieta (`Beneficiary name is required`), preto sa QR od commitu `dca2125` nezobrazoval. Nový test používa skutočnú knižnicu vrátane dekódovania; Vitest 14/14, overené aj v prehliadači. |
| 2026-09-23 | `manual.md` doplnený o skúsenosti z lokálnej prevádzky: inštalácia mimo `.venv`, aktivácia v `cmd.exe`, spúšťanie backendu z priečinka `backend`, `CORS_ORIGINS` a pracovný priečinok pri automatickom štarte, lokálne zmeny pred `git pull`, kontrola QR v bankovej aplikácii, presnejší postup importu do Neon a nová kapitola 12 Riešenie problémov. | Problémy zistené pri spúšťaní `C:\Apps\Dane_bu` 2026-09-23. |

## Kontrolný zoznam pred označením MVP za hotové

- [x] Všetky podporované finančné pravidlá majú oficiálny zdroj a dátum platnosti.
- [x] Žiadna nepodporovaná kombinácia negeneruje odhadovaný účet alebo VS.
- [x] IBAN prejde MOD 97 a testovacími vektormi.
- [x] Použitý OÚD je vo výsledku viditeľný a používateľom potvrdený.
- [x] Každá inštrukcia obsahuje auditný snapshot pravidla.
- [x] Testy, lint, typová kontrola a build prechádzajú.
- [x] README presne opisuje spustenie, limity a postup kontroly údajov.
