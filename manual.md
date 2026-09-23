# Manuál nasadenia aplikácie

Tento manuál popisuje nasadenie aplikácie na Windows server bez Dockeru. Ostatné počítače pristupujú k aplikácii cez webový prehliadač.

## 1. Požiadavky

Na serveri nainštalujte Python 3.12 alebo novší, Node.js 22 alebo novší a Git. Používateľské počítače potrebujú iba Chrome, Edge alebo Firefox.

Na Windows overte Python príkazom `py --version`. Ak príkaz `python` hlási, že Python nebol nájdený, používajte `py`. Ak PowerShell blokuje súbory `npm.ps1` alebo `npx.ps1`, používajte `npm.cmd` a `npx.cmd`.

Ak príkaz `python` nie je dostupný, ekvivalentné príkazy sú:

```powershell
py -m venv .venv
py -m pip install -e .
py -m alembic upgrade head
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Po aktivácii `.venv` možno namiesto `python` použiť aj `.\.venv\Scripts\python.exe`.

Ak `pip install` hlási `Defaulting to user installation`, balíky sa nainštalovali mimo virtuálneho prostredia. Príkazy `alembic` a `uvicorn` potom nemusia byť v PATH (`is not recognized`). Riešením je aktivovať `.venv` podľa kapitoly 3 alebo spúšťať nástroje cez `python -m alembic` a `python -m uvicorn`.

## 2. Stiahnutie projektu

```powershell
git clone https://github.com/app74/Dane_bu.git C:\Apps\Dane_bu
cd C:\Apps\Dane_bu
```

Aktualizácia existujúcej inštalácie:

```powershell
cd C:\Apps\Dane_bu
git pull origin main
```

## 3. Backend

```powershell
cd C:\Apps\Dane_bu\backend
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

V príkazovom riadku `cmd.exe` (nie PowerShell) sa prostredie aktivuje príkazom `.venv\Scripts\activate.bat`.

Backend vždy spúšťajte z priečinka `C:\Apps\Dane_bu\backend`. Cesta k databáze `sqlite:///./app.db` je relatívna. Pri spustení z iného priečinka backend nahlási úspešný štart, ale vytvorí novú prázdnu databázu `app.db` v tom priečinku a uložené subjekty nebude vidieť.

Ak aktiváciu blokuje bezpečnostná politika, použite priamo `.\.venv\Scripts\python.exe` namiesto aktivácie. Ak sa zobrazí chyba `10048`, port 8000 už používa iný proces. Overte ho príkazom `Get-NetTCPConnection -LocalPort 8000 -State Listen`; použite už bežiaci server, zastavte príslušný proces cez `Stop-Process -Id <PID>`, alebo zvoľte iný port.

Kontrola: `http://localhost:8000/health`. Očakávaná odpoveď je `{"status":"ok"}`.

## 4. Frontend pre sieťový prístup

Frontend volá backend na porte 8000 toho počítača, z ktorého sa stránka načítala (`window.location.hostname`). V `frontend/src/main.tsx` preto netreba nič upravovať. Pri otvorení `http://192.168.1.50:5173` sa backend volá na `http://192.168.1.50:8000`.

Vytvorenie frontendu:

```powershell
cd C:\Apps\Dane_bu\frontend
npm.cmd install
npm.cmd run build
npx.cmd vite preview --host 0.0.0.0 --port 5173
```

Produkčné súbory sú v `frontend\dist`. Pre trvalú prevádzku je vhodné servovať tento priečinok cez IIS alebo Nginx.

## 5. Prístup z bežného počítača

Ak aplikáciu spustíte iba na adrese `127.0.0.1:5173`, bude dostupná len na serveri. Pre prístup z ostatných počítačov musí Vite počúvať na všetkých sieťových rozhraniach:

```powershell
cd C:\Apps\Dane_bu\frontend
npm.cmd run dev -- --host 0.0.0.0
```

Rovnako musí backend počúvať na všetkých sieťových rozhraniach:

```powershell
cd C:\Apps\Dane_bu\backend
.\.venv\Scripts\Activate.ps1
$env:CORS_ORIGINS = "http://192.168.1.50:5173"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend štandardne prijíma požiadavky iba zo stránok `http://localhost:5173` a `http://127.0.0.1:5173` (CORS). Adresu, na ktorej používatelia otvárajú aplikáciu, doplňte do `CORS_ORIGINS`: presná schéma, IP alebo DNS meno servera a port, bez lomky na konci. Viac adries oddeľte čiarkou, napríklad `http://192.168.1.50:5173,http://dane-server:5173`. Bez toho sa stránka na inom počítači načíta, ale zobrazí „Backend nie je dostupný“. Premenná `$env:` platí iba v danom okne PowerShellu. Pri automatickom spúšťaní (kapitola 7) ju nastavte v službe alebo v úlohe Task Schedulera.

Adresa `127.0.0.1` označuje vždy aktuálny počítač. Adresa `0.0.0.0` znamená, že služba prijíma pripojenia aj zo siete. Používatelia preto otvárajú IP adresu servera, nie `127.0.0.1`.

Na serveri spustite `ipconfig` a zistite IPv4 adresu, napríklad `192.168.1.50`. Ak ju server dostáva cez DHCP, požiadajte správcu siete o rezerváciu adresy alebo o DNS záznam, inak sa adresa môže zmeniť. Na inom počítači otvorte:

```text
http://192.168.1.50:5173
```

Na bežnom počítači netreba inštalovať Python, Node.js ani Docker.

## 6. Windows Firewall

PowerShell spustite ako správca. Pravidlá otvárajú porty pre všetky počítače v sieti. Aplikácia lokálne nemá prihlásenie, takže každý, kto sa dostane na port 8000, môže čítať aj meniť subjekty. Obmedzte preto prístup na vnútornú sieť, napríklad parametrom `-Profile Domain` alebo `-RemoteAddress 192.168.10.0/24`.

```powershell
New-NetFirewallRule -DisplayName "Dane Bu Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Domain
New-NetFirewallRule -DisplayName "Dane Bu Frontend" -Direction Inbound -Protocol TCP -LocalPort 5173 -Action Allow -Profile Domain
```

## 7. Automatické spúšťanie

Backendový príkaz:

```text
C:\Apps\Dane_bu\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontendový príkaz:

```text
C:\Apps\Dane_bu\frontend\node_modules\.bin\vite.cmd preview --host 0.0.0.0 --port 5173
```

Oba príkazy nastavte vo Windows Task Scheduleri alebo pomocou NSSM ako služby spúšťané po štarte servera. Pre backend nastavte:

- pracovný priečinok (Task Scheduler: **Start in**, NSSM: **Startup directory**) na `C:\Apps\Dane_bu\backend`, inak sa použije iná databáza (kapitola 3),
- premennú prostredia `CORS_ORIGINS`, ak sa k aplikácii pripájajú iné počítače (kapitola 5). V NSSM ju zadajte na karte **Environment**, napríklad `CORS_ORIGINS=http://192.168.1.50:5173`.

## 8. Databáza a zálohy

SQLite databáza je v `backend\app.db`. Pred zálohou zastavte backend a vytvorte kópiu:

```powershell
Copy-Item C:\Apps\Dane_bu\backend\app.db D:\Zalohy\app-$(Get-Date -Format yyyy-MM-dd).db
```

Zálohy ukladajte mimo servera. Pri väčšom počte súčasných používateľov je vhodné prejsť na PostgreSQL.

## 9. Aktualizácia

Pred aktualizáciou zazálohujte databázu. Príkazom `git status` overte, či v inštalácii nie sú ručné úpravy súborov. Ak `git pull` hlási `Your local changes ... would be overwritten`, pozrite si ich cez `git diff`. Ak sú už obsiahnuté v novej verzii, zahoďte ich príkazom `git checkout -- .`. Tento príkaz nemaže databázu `app.db`, lebo tá nie je v Gite. Potom:

```powershell
cd C:\Apps\Dane_bu
git pull origin main
cd backend
.\.venv\Scripts\Activate.ps1
pip install -e .
alembic upgrade head
cd ..\frontend
npm.cmd install
npm.cmd run build
```

Po aktualizácii reštartujte backend a frontendové služby.

## 10. Kontrola po nasadení

Overte:

1. `http://<server>:8000/health` vráti `{"status":"ok"}`.
2. Aplikácia sa otvorí na serveri aj na inom počítači bez hlásenia „Backend nie je dostupný“.
3. Vyhľadanie subjektu a uloženie bez duplicity fungujú.
4. Po vytvorení náhľadu sa zobrazí QR kód PAY by square. Naskenujte ho bankovou aplikáciou, ktorú používate, a porovnajte IBAN, sumu a variabilný symbol s náhľadom. QR kód sa vytvára vo formáte PAY by square 1.1.0 bez mena príjemcu, lebo formát 1.2.0 meno príjemcu vyžaduje. Podpora staršieho formátu sa môže líšiť podľa banky.
5. Text e-mailu sa dá skopírovať.
6. Údaje zostanú zachované po reštarte backendu.

## 11. Nasadenie na Vercel

Aplikácia beží na Verceli ako jeden projekt s dvoma službami ([Vercel Services](https://vercel.com/docs/services), Beta): frontend (Vite) na `/` a FastAPI backend na `/api/*`. Konfigurácia je v `vercel.json`. Lokálne spustenie, Docker a nasadenie na Windows server sa nemenia.

### 11.1 Predpoklady a riziká

- **Plán Vercelu:** plán Hobby je podľa [Fair Use Guidelines](https://vercel.com/docs/limits/fair-use-guidelines) iba na nekomerčné osobné použitie. Firemné použitie vyžaduje plán Pro alebo Enterprise.
- **Services (Beta):** funkcia je v dokumentácii označená ako Beta a môže vyžadovať povolenie pre tím. Ak build hlási nepodporovaný kľúč `services`, overte dostupnosť v nastaveniach tímu.
- **Roly:** vlastník alebo člen tímu Vercel s právom vytvárať projekty a spravovať Environment Variables a integrácie. Na GitHube stačí prístup na čítanie repozitára `app74/Dane_bu`.
- **Citlivé údaje:** databáza obsahuje OÚD a identifikátory subjektov. Heslá a connection stringy zadávajte iba do Vercel Environment Variables. Nevkladajte ich do repozitára, do chatu ani do tiketov.
- **Dáta:** SQLite sa na Verceli nepoužíva, lebo funkcie nemajú trvalý disk. Dáta sú v Neon Postgres.
- **Vyhľadanie v exportoch FS** je na Verceli predvolene vypnuté. Export má približne 65 MB a index sa pri každej novej inštancii stavia nanovo, čo sa nemusí zmestiť do limitu funkcie (Hobby 300 s). OÚD sa zadáva ručne a overuje na portáli FS.

### 11.2 Databáza Neon Postgres

1. Vo Vercel projekte otvorte **Storage** (alebo **Integrations → Neon Postgres**), vytvorte databázu a zvoľte región v EÚ, napríklad Frankfurt.
2. Integrácia pridá do projektu premenné `DATABASE_URL` (pooled, PgBouncer) a `DATABASE_URL_UNPOOLED` (priame pripojenie). Overte ich v **Settings → Environment Variables**.
3. Backend `DATABASE_URL` automaticky prevedie na ovládač `psycopg` (`postgres://` → `postgresql+psycopg://`).

Schému vytvára iba Alembic. Pri Postgrese backend tabuľky sám nevytvára. Migrácie spustite z lokálneho počítača s **priamym** pripojením (`DATABASE_URL_UNPOOLED`). Hodnotu skopírujte z Vercelu, zadajte ju iba do lokálnej premennej prostredia a po skončení ju zmažte:

```powershell
cd C:\Apps\Dane_bu\backend
.\.venv\Scripts\Activate.ps1
pip install -e .
$env:DATABASE_URL = Read-Host "Priamy connection string (DATABASE_URL_UNPOOLED)"
alembic upgrade head
Remove-Item Env:DATABASE_URL
```

Migrácie spúšťajte pred nasadením verzie, ktorá novú schému potrebuje. Pred migráciou produkčnej databázy vytvorte zálohu alebo branch v Neon.

### 11.3 Environment Variables

V **Settings → Environment Variables** nastavte pre prostredia Production a Preview:

| Premenná | Hodnota | Poznámka |
| --- | --- | --- |
| `DATABASE_URL` | pridá integrácia Neon | pooled pripojenie pre aplikáciu |
| `APP_PASSWORD` | spoločné heslo, aspoň 12 znakov (odporúčané 20+) | bez neho API na Verceli vracia 503 |
| `SESSION_SECRET` | náhodný reťazec, aspoň 32 znakov | podpisuje prihlasovaciu cookie |
| `FS_LOOKUP_ENABLED` | nenastavovať (vypnuté) alebo `true` | zapnutie iba po otestovaní limitov |

Náhodný `SESSION_SECRET` vygenerujete lokálne:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Zmena `APP_PASSWORD` alebo `SESSION_SECRET` odhlási všetkých používateľov. Po zmene premenných treba nové nasadenie (Redeploy).

### 11.4 Vytvorenie projektu

1. Vercel → **Add New → Project** → import repozitára `app74/Dane_bu`.
2. Root Directory ponechajte na koreni repozitára. Služby definuje `vercel.json`.
3. Pred prvým nasadením nastavte premenné z 11.3 a spustite migrácie z 11.2.
4. Nasaďte. Každý push do `main` vytvorí produkčné nasadenie, ostatné vetvy vytvoria Preview.

Build backendu skopíruje `docs/tax-rules.json` do `backend/docs/`, lebo služba backendu má koreň `backend/`. Ak build zlyhá na príkaze `cp`, zapnite v projekte zahrnutie súborov mimo Root Directory.

### 11.5 Prístup a bezpečnosť

- Backend chráni celé API spoločným heslom. Po prihlásení dostane prehliadač HttpOnly cookie (`Secure`, `SameSite=Strict`) platnú 8 hodín.
- Ak na Verceli chýba `APP_PASSWORD` alebo `SESSION_SECRET`, API vracia 503 a dáta nesprístupní. Verejný je iba `/api/health`.
- Neúspešné prihlásenie sa spomalí o 1 sekundu. Proti hádaniu hesla používajte dlhé heslo. Voliteľne pridajte pravidlo rate limit vo Vercel Firewall pre `/api/auth/login`.
- Preview nasadenia používajú rovnakú databázu, ak im priradíte rovnaký `DATABASE_URL`. Pre Preview odporúčame samostatný branch databázy v Neon.

### 11.6 Prenos existujúcich subjektov

V pôvodnej inštalácii použite **Exportovať subjekty CSV** alebo `http://localhost:8000/subjects.csv`. Import do Neon urobte po migráciách (11.2) z lokálneho backendu pripojeného na Neon:

```powershell
cd C:\Apps\Dane_bu\backend
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL = Read-Host "Priamy connection string (DATABASE_URL_UNPOOLED)"
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Potom otvorte `http://127.0.0.1:8001/docs` a nahrajte CSV najprv cez `POST /subjects/import/preview` (kontrola), potom cez `POST /subjects/import`. Import najprv otestujte na súbore s jedným riadkom. Backend spúšťajte iba na `127.0.0.1`, lebo lokálne nemá heslo a pracuje s produkčnými dátami. Po skončení ho zastavte a spustite `Remove-Item Env:DATABASE_URL`. História platobných inštrukcií sa takto neprenáša. Súbor CSV obsahuje OÚD, preto ho po prenose zmažte.

### 11.7 Kontrola po nasadení

1. `https://<projekt>.vercel.app/api/health` vráti `{"status":"ok"}`.
2. Úvodná stránka zobrazí prihlásenie. Po zadaní hesla sa načítajú pravidlá.
3. Bez prihlásenia vráti `https://<projekt>.vercel.app/api/subjects` HTTP 401.
4. Uloženie subjektu, vytvorenie náhľadu, QR a uloženie do histórie fungujú a po novom nasadení údaje zostanú zachované.
5. **Vyhľadať subjekt** zobrazí hlásenie, že vyhľadanie je vypnuté a OÚD treba zadať ručne.

## 12. Riešenie problémov

| Príznak | Príčina | Riešenie |
| --- | --- | --- |
| `'alembic'` / `'uvicorn' is not recognized` | balíky sú nainštalované mimo `.venv` a ich priečinok `Scripts` nie je v PATH | aktivujte `.venv` (kapitola 3) alebo použite `python -m alembic`, `python -m uvicorn` |
| `[Errno 10048] ... only one usage of each socket address` | port 8000 už používa iný proces, často už bežiaci backend | `Get-NetTCPConnection -LocalPort 8000 -State Listen` zobrazí PID; buď použite bežiaci server, alebo ho zastavte cez `Stop-Process -Id <PID>` |
| Backend beží, ale subjekty chýbajú | backend bol spustený z iného priečinka a používa inú `app.db` | zastavte ho a spustite z `C:\Apps\Dane_bu\backend` (kapitola 3) |
| „Backend nie je dostupný“, prázdny zoznam pravidiel | backend nebeží, frontend volá nesprávnu adresu alebo backend odmieta adresu stránky (CORS) | 1. otvorte `http://<server>:8000/health`; 2. v prehliadači stlačte F12 → **Console** a pozrite chybu; 3. pri CORS chybe doplňte adresu stránky do `CORS_ORIGINS` (kapitola 5) |
| V konzole je adresa ako `:5173/$%7Bwindow.location...` | v staršej verzii bola adresa API v `main.tsx` zapísaná v úvodzovkách `"..."` namiesto spätných apostrofov `` `...` `` | aktualizujte na aktuálnu verziu (kapitola 9), ktorá úpravu `main.tsx` nepotrebuje |
| Stránka sa na inom počítači neotvorí | Vite alebo backend počúvajú iba na tomto počítači, prípadne blokuje firewall | spúšťajte s `--host 0.0.0.0` (kapitola 5) a pridajte pravidlá firewallu (kapitola 6) |
| QR kód sa nezobrazí | verzia pred opravou vytvárala QR vo formáte 1.2.0 s prázdnym menom príjemcu, ktorý knižnica odmietne | aktualizujte na aktuálnu verziu (kapitola 9) a obnovte stránku (Ctrl+F5) |
| Stránka `…azurewebsites.net` zobrazuje predvolenú stránku Azure alebo „Service Unavailable“ | aplikácia sa ešte spúšťa, alebo sa nenainštalovali závislosti či nespustil `startup.sh` | počkajte pár minút a obnovte stránku; skontrolujte **Deployment Center → Logs** a **Log stream**, nastavenie `SCM_DO_BUILD_DURING_DEPLOYMENT=true` a Startup Command `sh startup.sh` (kapitola 13.3) |
| Na Azure API vracia 401 aj po prihlásení | nie je nastavené alebo vynútené prihlásenie Microsoft Entra ID | nastavte kapitolu 13.4 (Require authentication) |

## 13. Nasadenie na Azure App Service

Aplikácia beží ako jedna **Azure App Service (Linux, Python)**. Frontend a API sú na rovnakej adrese `https://<app>.azurewebsites.net`, API pod `/api`. Prístup chráni prihlásenie **Microsoft Entra ID** (App Service Authentication, „Easy Auth“), teda firemné účty Microsoft 365. Dáta sú v SQLite v trvalom priečinku `/home/data`. Vstupný bod je `backend/azure_app.py`, štartovací skript `azure/startup.sh`, zostavenie balíka `azure/build_package.py` a nasadenie `azure/deploy.ps1`.

### 13.1 Predpoklady a riziká

- **Oprávnenia:** rola Contributor (alebo Owner) na subskripcii alebo resource group. Pre Entra ID treba právo vytvoriť App registration v tenante. Ak ho nemáte, požiadajte správcu Entra ID o registráciu (13.4, možnosť „existujúca registrácia“).
- **Náklady:** plán `B1` je platený. Cenu overte v [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) pred vytvorením prostriedkov.
- **Citlivé údaje:** databáza obsahuje OÚD a identifikátory subjektov. Prístup majú všetci používatelia tenanta, ktorí prejdú prihlásením. Obmedzenie na vybraných ľudí je v 13.4.
- **SQLite v `/home`:** `/home` je jediný trvalý priečinok App Service. Ostatné súbory sa pri reštarte stratia. SQLite je vhodná iba pre **jednu inštanciu**, plán nerozširujte na viac inštancií (scale out). Pri viacerých súčasných používateľoch alebo inštanciách prejdite na PostgreSQL (kód ho podporuje cez `DATABASE_URL`).
- **Vyhľadanie v exportoch FS** je zapnuté. Exporty a index sa ukladajú do `/home/data/fs-exports` a prežijú reštart. Prvé vyhľadanie po nasadení sťahuje približne 65 MB a stavia index, takže môže trvať niekoľko minút. Ak ho Azure preruší časovým limitom požiadavky, vyhľadanie o pár minút zopakujte. Pre exporty platí licencia uvedená v README (CC BY-NC-ND pri exporte účtov).

### 13.2 Azure CLI

Inštalácia (PowerShell) a prihlásenie:

```powershell
winget install --exact --id Microsoft.AzureCLI
az login
az account show --output table
```

Ak máte viac subskripcií, vyberte správnu: `az account set --subscription "<názov alebo ID>"`. Dostupné verzie Pythonu overíte príkazom `az webapp list-runtimes --os linux`. Skript predvolene používa `PYTHON:3.12`, inú zadáte parametrom `-PythonVersion`.

### 13.3 Prvé nasadenie

Z koreňa repozitára, s aktivovaným `backend\.venv` alebo s Pythonom 3.11+ a Node.js v PATH:

```powershell
cd C:\Apps\Dane_bu
.\azure\deploy.ps1 -ResourceGroup rg-dane-bu -AppName <jedinecne-meno> -CreateResources
```

Meno aplikácie musí byť v Azure jedinečné, lebo tvorí adresu `https://<jedinecne-meno>.azurewebsites.net`. Skript:

1. zostaví balík `build\dane-bu-azure.zip` (`python azure\build_package.py`: frontend s `VITE_API_URL=/api`, backend, `docs/tax-rules.json`, `requirements.txt`, `startup.sh`),
2. vypíše prostriedky, ktoré vytvorí, a čaká na potvrdenie `ano`,
3. vytvorí resource group, Linux App Service plan a web app, zapne iba HTTPS a TLS 1.2, nastaví startup `sh startup.sh` a `SCM_DO_BUILD_DURING_DEPLOYMENT=true` (Azure pri nasadení nainštaluje `requirements.txt`),
4. nahrá balík (`az webapp deploy --type zip`).

Pri štarte `startup.sh` vytvorí `/home/data`, spustí migrácie `alembic upgrade head` a potom Uvicorn. Prvý štart po nasadení môže trvať niekoľko minút.

Bez nastaveného prihlásenia Microsoft Entra ID aplikácia **nevydá žiadne dáta**. API vracia 401 a stránka ponúkne prihlásenie. Preto hneď pokračujte krokom 13.4.

### 13.4 Prihlásenie Microsoft Entra ID

Postup podľa [dokumentácie Microsoftu](https://learn.microsoft.com/azure/app-service/configure-authentication-provider-aad):

1. Azure portál → web app → **Settings → Authentication → Add identity provider**.
2. **Identity provider:** Microsoft. **Tenant:** Workforce configuration (current tenant).
3. **App registration:** Create new app registration, názov napríklad `dane-bu`. **Supported account type:** Current tenant – Single tenant.
4. **Restrict access:** Require authentication. **Unauthenticated requests:** HTTP 302 Found redirect. **Token store:** zapnutý.
5. **Add**.

Klientsky secret sa uloží ako nastavenie `MICROSOFT_PROVIDER_AUTHENTICATION_SECRET`. Nemeňte ho ručne a nezverejňujte ho.

Pri rýchlom nastavení Azure použije starší issuer `https://sts.windows.net/...`. Microsoft odporúča upraviť ho v nastaveniach poskytovateľa na `https://login.microsoftonline.com/<tenant-id>/v2.0`.

Predvolene sa môže prihlásiť **každý používateľ tenanta**. Obmedzenie na vybraných ľudí: Microsoft Entra admin center → **Enterprise applications** → `dane-bu` → **Properties** → *Assignment required* = Yes, potom v **Users and groups** priraďte používateľov alebo skupinu.

Aplikácia overuje prihlásenie podľa hlavičky `X-MS-CLIENT-PRINCIPAL-ID`, ktorú do požiadavky vkladá iba App Service. Klient ju podvrhnúť nemôže. Na Azure **nenastavujte** `APP_PASSWORD`, inak sa aplikácia prepne na prihlásenie spoločným heslom.

### 13.5 Nastavenia aplikácie (Environment variables)

| Premenná | Hodnota | Poznámka |
| --- | --- | --- |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | nastaví skript; bez nej sa nenainštalujú závislosti |
| `DATA_DIR` | predvolene `/home/data` | databáza `app.db` a cache exportov FS |
| `DATABASE_URL` | predvolene `sqlite:////home/data/app.db` | pre PostgreSQL zadajte jeho connection string |
| `FS_LOOKUP_ENABLED` | nenastavovať (zapnuté) alebo `false` | vypnutie vyhľadania v exportoch FS |

### 13.6 Prenos existujúcich subjektov

1. V pôvodnej inštalácii stiahnite **Exportovať subjekty CSV** alebo `http://localhost:8000/subjects.csv`.
2. Prihláste sa do Azure aplikácie a otvorte `https://<app>.azurewebsites.net/api/docs`.
3. CSV nahrajte najprv cez `POST /subjects/import/preview` (kontrola), potom cez `POST /subjects/import`. Najprv otestujte súbor s jedným riadkom.
4. Súbor CSV obsahuje OÚD, po prenose ho zmažte. História platobných inštrukcií sa takto neprenáša.

### 13.7 Aktualizácia

```powershell
cd C:\Apps\Dane_bu
git pull origin main
.\azure\deploy.ps1 -ResourceGroup rg-dane-bu -AppName <jedinecne-meno>
```

Bez `-CreateResources` skript iba zostaví a nahrá nový balík. Migrácie databázy sa spustia automaticky pri štarte. Pred aktualizáciou si zálohujte dáta (13.8).

### 13.8 Zálohy

Databáza je súbor `/home/data/app.db`. Priebežne si ukladajte **Exportovať subjekty CSV** na bezpečné miesto. Ak váš cenový plán podporuje zálohy App Service (**Settings → Backups**), zapnite ich. Dostupnosť pre plán `B1` overte v portáli. Kópiu súboru získate aj cez SSH (`az webapp ssh --resource-group <rg> --name <app>`), keď je aplikácia zastavená alebo bez aktívneho zápisu.

### 13.9 Kontrola po nasadení

1. `https://<app>.azurewebsites.net` presmeruje na prihlásenie Microsoft. Po prihlásení sa zobrazí „Prihlásený: <váš účet>“.
2. V novom okne v režime inkognito bez prihlásenia sa dáta nezobrazia.
3. Uloženie subjektu, náhľad, QR kód (naskenovaný bankovou aplikáciou), uloženie do histórie a export TXT fungujú.
4. Údaje zostanú zachované po reštarte (**Overview → Restart**).
5. **Vyhľadať subjekt** nájde subjekt podľa IČO. Prvé vyhľadanie môže trvať dlhšie (13.1).
6. Pri uložení subjektu sledujte F12 → Network. POST požiadavka nesmie skončiť chybou, ktorú by spôsobila ochrana CSRF v App Service Authentication. Lokálne sa to overiť nedá.

### 13.10 Lokálny test Azure balíka

Balík sa dá otestovať lokálne ešte pred nasadením. Spustí sa tak, ako na App Service, s dočasnou databázou na porte 8010. Prihlásenie Entra ID nahrádzajú hlavičky, ktoré inak vkladá App Service:

```powershell
cd C:\Apps\Dane_bu
backend\.venv\Scripts\Activate.ps1
python azure\build_package.py
npx.cmd playwright test --config=playwright.azure.config.ts
```

Test overí, že bez prihlásenia API nevydá dáta, a potom prejde hlavný scenár vrátane QR kódu, histórie a zachovania dát po obnovení stránky. Po každej zmene kódu balík znova zostavte, inak test beží so starou verziou.
