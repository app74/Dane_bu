from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tax_rules_exposes_only_supported_rules() -> None:
    response = TestClient(app).get("/tax-rules")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert ids == {
        "income-return-2025",
        "income-fo-resident-2025",
            "income-fo-nonresident-2025",
            "income-po-advance-2026-month-01",
            "income-po-advance-2026-quarter-01",
            "withholding-dividend-2026-05",
            "motor-vehicle-return-2025",
        "vat-2026-month-03",
        "vat-2026-quarter-01",
    }
    assert all("source_url" in item for item in response.json())

def test_subject_crud_stores_oud_as_text() -> None:
    client = TestClient(app)
    response = client.post("/subjects", json={"name": "Testovací subjekt", "oud": "0123456789"})
    assert response.status_code == 201
    assert response.json()["oud"] == "0123456789"
    assert any(item["id"] == response.json()["id"] for item in client.get("/subjects").json())

def test_subject_rejects_invalid_oud() -> None:
    response = TestClient(app).post("/subjects", json={"name": "Chyba", "oud": "123"})
    assert response.status_code == 422


def test_subject_can_be_updated_and_deleted() -> None:
    client = TestClient(app)
    created = client.post("/subjects", json={"name": "Pôvodný", "oud": "9876543210"}).json()
    subject_id = created["id"]
    updated = client.put(
        f"/subjects/{subject_id}",
        json={"name": "Aktualizovaný", "oud": "9876543210", "ico": "12345678"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Aktualizovaný"
    assert client.delete(f"/subjects/{subject_id}").status_code == 204
    assert client.get(f"/subjects/{subject_id}").status_code == 404


def test_payment_preview_returns_auditable_instruction() -> None:
    client = TestClient(app)
    subject = client.post(
        "/subjects", json={"name": "Platiteľ", "oud": "1234567890"}
    ).json()
    response = client.post(
        "/payment-instructions/preview",
        json={
            "subject_id": subject["id"],
            "rule_id": "income-return-2025",
            "amount": "100.00",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["variable_symbol"] == "1700992025"
    assert body["iban_valid"] is True
    assert body["source_url"].startswith("https://www.financnasprava.sk/")


def test_payment_preview_rejects_unverified_rule() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "Platiteľ", "oud": "1234567890"}).json()
    response = client.post(
        "/payment-instructions/preview",
        json={"subject_id": subject["id"], "rule_id": "vat-2026-monthly", "amount": "1.00"},
    )
    assert response.status_code == 422


def test_payment_instruction_can_be_saved_as_snapshot() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "História", "oud": "1111111111"}).json()
    payload = {
        "subject_id": subject["id"],
        "rule_id": "motor-vehicle-return-2025",
        "amount": "25.00",
    }
    saved = client.post("/payment-instructions", json=payload)
    assert saved.status_code == 201
    history = client.get("/payment-instructions")
    assert history.status_code == 200
    assert history.json()[0]["variable_symbol"] == "1700992025"
    assert client.get("/payment-instructions/1").status_code == 200
    assert client.get("/payment-instructions/999999").status_code == 404


def test_confirmed_vat_period_can_be_previewed() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "DPH", "oud": "2222222222"}).json()
    response = client.post(
        "/payment-instructions/preview",
        json={"subject_id": subject["id"], "rule_id": "vat-2026-month-03", "amount": "50.00"},
    )
    assert response.status_code == 200
    assert response.json()["variable_symbol"] == "1100032026"
    assert response.json()["due_date"] == "2026-04-27"


def test_confirmed_vat_quarter_can_be_previewed() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "DPH štvrťrok", "oud": "3333333333"}).json()
    response = client.post(
        "/payment-instructions/preview",
        json={"subject_id": subject["id"], "rule_id": "vat-2026-quarter-01", "amount": "75.00"},
    )
    assert response.status_code == 200
    assert response.json()["variable_symbol"] == "1100412026"
    assert response.json()["due_date"] == "2026-04-27"


def test_confirmed_fo_resident_rule_can_be_previewed() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "FO", "oud": "4444444444"}).json()
    response = client.post(
        "/payment-instructions/preview",
        json={"subject_id": subject["id"], "rule_id": "income-fo-resident-2025", "amount": "10.00"},
    )
    assert response.status_code == 200
    assert "500208" in response.json()["domestic_account"]


def test_confirmed_fo_nonresident_rule_can_be_previewed() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "FO nerezident", "oud": "5555555555"}).json()
    response = client.post(
        "/payment-instructions/preview",
        json={
            "subject_id": subject["id"],
            "rule_id": "income-fo-nonresident-2025",
            "amount": "10.00",
        },
    )
    assert response.status_code == 200
    assert "500216" in response.json()["domestic_account"]


def test_confirmed_po_advance_month_can_be_previewed() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "DPPO preddavok", "oud": "6666666666"}).json()
    response = client.post(
        "/payment-instructions/preview",
        json={
            "subject_id": subject["id"],
            "rule_id": "income-po-advance-2026-month-01",
            "amount": "20.00",
        },
    )
    assert response.status_code == 200
    assert response.json()["variable_symbol"] == "1100012026"
    assert response.json()["due_date"] == "2026-02-02"


def test_confirmed_withholding_dividend_rule_can_be_previewed() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "Platiteľ zrážky", "oud": "9999999999"}).json()
    response = client.post(
        "/payment-instructions/preview",
        json={
            "subject_id": subject["id"],
            "rule_id": "withholding-dividend-2026-05",
            "amount": "1700.00",
        },
    )
    assert response.status_code == 200
    assert "500267" in response.json()["domestic_account"]
    assert response.json()["variable_symbol"] == "1700052026"
    assert response.json()["due_date"] == "2026-06-15"


def test_payment_preview_rejects_invalid_amount() -> None:
    client = TestClient(app)
    subject = client.post("/subjects", json={"name": "Suma", "oud": "7777777777"}).json()
    for amount in ["-1.00", "1.001", "nie číslo"]:
        response = client.post(
            "/payment-instructions/preview",
            json={
                "subject_id": subject["id"],
                "rule_id": "income-return-2025",
                "amount": amount,
            },
        )
        assert response.status_code == 422


def test_payment_preview_rejects_missing_subject() -> None:
    response = TestClient(app).post(
        "/payment-instructions/preview",
        json={"subject_id": 999999, "rule_id": "income-return-2025", "amount": "1.00"},
    )
    assert response.status_code == 404
