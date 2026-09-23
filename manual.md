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

Ak aktiváciu blokuje bezpečnostná politika, použite priamo `.\.venv\Scripts\python.exe` namiesto aktivácie. Ak sa zobrazí chyba `10048`, port 8000 už používa iný proces. Overte ho príkazom `Get-NetTCPConnection -LocalPort 8000 -State Listen`; použite už bežiaci server, zastavte príslušný proces cez `Stop-Process -Id <PID>`, alebo zvoľte iný port.

Kontrola: `http://localhost:8000/health`. Očakávaná odpoveď je `{"status":"ok"}`.

## 4. Frontend pre sieťový prístup

V `frontend/src/main.tsx` nastavte API takto:

```ts
const API = `${window.location.protocol}//${window.location.hostname}:8000`;
```

Nepoužívajte `127.0.0.1:8000`, pretože na inom počítači by smerovalo na jeho vlastný počítač.

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
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Adresa `127.0.0.1` označuje vždy aktuálny počítač. Adresa `0.0.0.0` znamená, že služba prijíma pripojenia aj zo siete. Používatelia preto otvárajú IP adresu servera, nie `127.0.0.1`.

Na serveri spustite `ipconfig` a zistite IPv4 adresu, napríklad `192.168.1.50`. Na inom počítači otvorte:

```text
http://192.168.1.50:5173
```

Na bežnom počítači netreba inštalovať Python, Node.js ani Docker.

## 6. Windows Firewall

PowerShell spustite ako správca:

```powershell
New-NetFirewallRule -DisplayName "Dane Bu Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
New-NetFirewallRule -DisplayName "Dane Bu Frontend" -Direction Inbound -Protocol TCP -LocalPort 5173 -Action Allow
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

Oba príkazy nastavte vo Windows Task Scheduleri alebo pomocou NSSM ako služby spúšťané po štarte servera.

## 8. Databáza a zálohy

SQLite databáza je v `backend\app.db`. Pred zálohou zastavte backend a vytvorte kópiu:

```powershell
Copy-Item C:\Apps\Dane_bu\backend\app.db D:\Zalohy\app-$(Get-Date -Format yyyy-MM-dd).db
```

Zálohy ukladajte mimo servera. Pri väčšom počte súčasných používateľov je vhodné prejsť na PostgreSQL.

## 9. Aktualizácia

Pred aktualizáciou zazálohujte databázu. Potom:

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

Overte health endpoint, otvorenie aplikácie, vyhľadanie subjektu, uloženie bez duplicity, vytvorenie textu e-mailu a QR kódu a zachovanie údajov po reštarte backendu.

