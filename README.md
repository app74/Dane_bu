# Platobné údaje pre slovenské dane

MVP aplikácie pripravuje platobné údaje; platby nevykonáva. OÚD možno zadať ručne alebo doplniť zo zverejneného účtu správcu dane v oficiálnom exporte FS.

## Vyhľadanie subjektu a OÚD

Zadajte celé IČO (8 číslic) alebo DIČ (10 číslic), kliknite na **Vyhľadať subjekt** a vyberte výsledok podľa názvu a adresy. Aplikácia doplní dostupné identifikátory a OÚD. Skontrolujte údaje a kliknite na **Uložiť subjekt**.

Názov a DIČ pochádzajú z registra subjektov registrovaných na daň z príjmov. Účet sa pripája cez presnú zhodu IČO s exportom účtov správcu dane pre platiteľov DPH. OÚD sa preberá z posledných 10 číslic overeného slovenského IBAN-u banky 8180 s predčíslím 500240; nikdy sa nepočíta z IČO alebo DIČ. Pri chýbajúcom IČO, chýbajúcom účte alebo nejednoznačných účtoch ostáva ručné zadanie. DIČ sa neodvodzuje z IČ DPH.

Prvé vyhľadanie stiahne približne 65 MB a vytvorí lokálny index v dočasnom priečinku `dane-bu-fs-exports`. Ďalšie vyhľadania používajú index; exporty sa obnovujú po 24 hodinách. Export s dátumom starším než 3 dni sa odmietne. Potrebné je internetové pripojenie pri obnove. Identifikátor sa odosiela iba lokálnemu backendu v tele POST požiadavky, FS dostáva iba požiadavky na celé exporty.

Zdroj a autor: [Finančné riaditeľstvo SR – exporty informačných zoznamov](https://www.financnasprava.sk/sk/danovi-a-colni-specialisti/technicke-informacie/podklady-pre-tvorcov-sw/exporty-informacnych-zoznamov). Register daňových subjektov je zverejnený pod CC0; export účtov pod **CC BY-NC-ND**, teda s obmedzením komerčného použitia. Táto integrácia nemení licenciu zdrojových dát. Na komerčné použitie treba zabezpečiť zodpovedajúce oprávnenie k dátam.

Pri subjekte mimo exportu použite [ručné overenie OÚD na FS](https://www.financnasprava.sk/sk/elektronicke-sluzby/verejne-sluzby/overenie-prideleneho-oud). Aplikácia neautomatizuje tento formulár ani neobchádza CAPTCHA.

## Spustenie bez Dockeru

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

V druhom termináli:

```powershell
cd frontend
npm install
npm run dev
```

Health check: `http://localhost:8000/health`.

Databázové migrácie:

```powershell
cd backend
alembic upgrade head
```

Lokálna SQLite databáza je súbor `backend/app.db`. Pred zálohou zastavte
backend a skopírujte súbor na bezpečné miesto. Obnova spočíva v jeho spätnom
skopírovaní pred opätovným spustením migrácií; záloha má obsahovať aj aktuálny
číselník `docs/tax-rules.json`, ak chcete zachovať auditnú reprodukovateľnosť.

## Docker

```powershell
docker compose up --build
```

Po úspešnom štarte otvorte aplikáciu na `http://localhost:5173`.
Stav backendu overíte na `http://localhost:8000/health`. Bežiace kontajnery
zastavíte príkazom `docker compose stop`; opätovný štart je `docker compose start`.

## Vercel

Aplikáciu možno nasadiť aj na Vercel (frontend na `/`, FastAPI na `/api`, databáza Neon Postgres). Postup, premenné prostredia, migrácie a kontrolu po nasadení opisuje [manual.md – kapitola 11](manual.md#11-nasadenie-na-vercel). Na Verceli je API chránené heslom (`APP_PASSWORD`, `SESSION_SECRET`) a vyhľadanie v exportoch FS je predvolene vypnuté (`FS_LOOKUP_ENABLED`). Lokálne spustenie bez hesla sa nemení.

Zdroje pravidiel: [docs/rules-sources.md](docs/rules-sources.md). Číselník: [docs/tax-rules.json](docs/tax-rules.json).

Kontroly po inštalácii závislostí:

```powershell
cd backend; python -m pytest; python -m ruff check .
cd ..\frontend; npm run build; npm test; npm run lint; npm run format:check
cd ..; npx playwright test
```

Testy backendu používajú dočasnú izolovanú SQLite databázu a nemenia lokálnu databázu `backend/app.db`.

E2E závislosť sa inštaluje z koreňa projektu (`npm install`).
