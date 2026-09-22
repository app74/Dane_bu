# Platobné údaje pre slovenské dane

MVP aplikácie pripravuje platobné údaje; platby nevykonáva a OÚD získava iba ručne od používateľa alebo z lokálnej evidencie.

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

Zdroje pravidiel: [docs/rules-sources.md](docs/rules-sources.md). Číselník: [docs/tax-rules.json](docs/tax-rules.json).

Kontroly po inštalácii závislostí:

```powershell
cd backend; python -m pytest; python -m ruff check .
cd ..\frontend; npm run build; npm test; npm run lint; npm run format:check
cd ..; npx playwright test
```

E2E závislosť sa inštaluje z koreňa projektu (`npm install`).
