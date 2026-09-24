"""Due-date settings API, holidays table, preview integration and the 0003 migration."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def preview(client: TestClient, rule_id: str) -> dict:
    subject = client.post("/subjects", json={"name": "Splatnosť", "oud": "8133492105"}).json()
    response = client.post(
        "/payment-instructions/preview",
        json={"subject_id": subject["id"], "rule_id": rule_id, "amount": "500.00"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_vat_august_2026_is_due_on_25_september() -> None:
    body = preview(TestClient(app), "vat-2026-month-08")
    assert body["due_date"] == "2026-09-25"
    assert body["variable_symbol"] == "1100082026"
    assert body["rule_name"] == "DPH – august 2026"
    assert "25. deň" in body["due_date_basis"]


def test_vat_weekend_and_holidays_shift_to_next_workday() -> None:
    client = TestClient(app)
    assert preview(client, "vat-2026-month-03")["due_date"] == "2026-04-27"  # FS list
    assert preview(client, "vat-2026-quarter-01")["due_date"] == "2026-04-27"  # FS list
    assert preview(client, "vat-2026-month-09")["due_date"] == "2026-10-26"
    assert preview(client, "vat-2026-month-11")["due_date"] == "2026-12-25"  # no holidays yet
    for day, name in (("2026-12-25", "Prvý sviatok vianočný"), ("2026-12-26", "Druhý sviatok")):
        assert client.post("/settings/holidays", json={"day": day, "name": name}).status_code == 201
    assert preview(client, "vat-2026-month-11")["due_date"] == "2026-12-28"


def test_advances_and_catalog_rules_keep_official_dates() -> None:
    client = TestClient(app)
    assert preview(client, "income-po-advance-2026-month-01")["due_date"] == "2026-02-02"
    assert preview(client, "income-po-advance-2026-month-08")["due_date"] == "2026-08-31"
    assert preview(client, "income-return-2025")["due_date"] == "2026-03-31"
    assert preview(client, "withholding-dividend-2026-05")["due_date"] == "2026-06-15"


def test_settings_table_lists_defaults() -> None:
    rows = {row["key"]: row for row in TestClient(app).get("/settings/due-dates").json()}
    assert rows["vat-month"]["kind"] == "next_month_day" and rows["vat-month"]["day"] == 25
    assert rows["vat-month"]["shift_to_workday"] is True and rows["vat-month"]["is_default"]
    assert "222/2004" in rows["vat-quarter"]["basis"]
    assert rows["income-return"]["kind"] == "catalog"


def test_setting_can_be_changed_and_reset() -> None:
    client = TestClient(app)
    changed = client.put(
        "/settings/due-dates/vat-month",
        json={"kind": "next_month_day", "day": 20, "shift_to_workday": False},
    )
    assert changed.status_code == 200 and changed.json()["is_default"] is False
    assert preview(client, "vat-2026-month-08")["due_date"] == "2026-09-20"
    reset = client.delete("/settings/due-dates/vat-month").json()
    assert reset["is_default"] is True and reset["day"] == 25
    assert preview(client, "vat-2026-month-08")["due_date"] == "2026-09-25"


def test_invalid_settings_are_rejected() -> None:
    client = TestClient(app)
    assert client.put("/settings/due-dates/vat-month", json={"kind": "x"}).status_code == 422
    assert client.put(
        "/settings/due-dates/vat-month", json={"kind": "next_month_day"}
    ).status_code == 422
    assert client.put(
        "/settings/due-dates/vat-month", json={"kind": "next_month_day", "day": 32}
    ).status_code == 422
    assert client.put(
        "/settings/due-dates/unknown", json={"kind": "catalog"}
    ).status_code == 404


def test_holidays_crud() -> None:
    client = TestClient(app)
    payload = {"day": "2027-03-26", "name": "Veľký piatok"}
    assert client.post("/settings/holidays", json=payload).status_code == 201
    assert client.post("/settings/holidays", json=payload).status_code == 409
    listed = client.get("/settings/holidays", params={"year": 2027}).json()
    assert listed["holidays"] == [payload]
    assert listed["source_url"].startswith("https://www.slov-lex.sk/")
    assert client.delete("/settings/holidays/2027-03-26").status_code == 204
    assert client.delete("/settings/holidays/2027-03-26").status_code == 404


def test_migration_creates_tables_and_seeds_confirmed_days_of_rest(tmp_path) -> None:
    database = tmp_path / "migrated.db"
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{database.as_posix()}")
    backend = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend, env=env,
                   check=True, capture_output=True)
    with sqlite3.connect(database) as db:
        days = {row[0] for row in db.execute("SELECT day FROM public_holidays")}
        assert db.execute("SELECT count(*) FROM due_date_settings").fetchone()[0] == 0
    assert len(days) == 33
    assert {"2026-04-03", "2026-04-06", "2027-03-26", "2027-03-29", "2026-12-25"} <= days
    assert not {"2026-09-01", "2026-09-15", "2026-05-08", "2026-11-17"} & days
