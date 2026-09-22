import zipfile
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import subject_lookup as lookup
from app.main import app


def make_export(path, rows, updated=None):
    updated = updated or date.today().strftime("%d%m%Y")
    xml = f"<Export><DatumAktualizacieZoznamu>{updated}</DatumAktualizacieZoznamu><Rows>"
    for row in rows:
        xml += "<ITEM>" + "".join(f"<{k}>{v}</{k}>" for k, v in row.items()) + "</ITEM>"
    xml += "</Rows></Export>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("data.xml", xml)


@pytest.fixture
def exports(tmp_path, monkeypatch):
    registry = tmp_path / "registry.zip"
    accounts = tmp_path / "accounts.zip"
    make_export(registry, [{"ICO": "00123456", "DIC": "2012345678", "NAZOV_DS": "Žltý test"}])
    make_export(accounts, [{"ICO": "00123456", "IBAN": "SK6181805002408026569576"}])
    monkeypatch.setattr(lookup, "export_path", lambda name:
                        registry if name == "ds_dsrdp" else accounts)
    return registry, accounts


@pytest.mark.parametrize("identifier", ["00123456", "2012345678"])
def test_lookup_joins_actual_registry_identifiers(exports, identifier):
    result = lookup.lookup_subject(identifier)["results"][0]
    assert result["name"] == "Žltý test"
    assert result["ico"] == "00123456"
    assert result["dic"] == "2012345678"
    assert result["oud"] == "8026569576"
    assert result["ic_dph"] is None


def test_missing_account_does_not_invent_oud(exports):
    make_export(exports[1], [])
    assert lookup.lookup_subject("00123456")["results"][0]["oud"] is None


def test_conflicting_accounts_are_not_selected(exports):
    make_export(exports[1], [
        {"ICO": "00123456", "IBAN": "SK6181805002408026569576"},
        {"ICO": "00123456", "IBAN": "different"},
    ])
    assert lookup.lookup_subject("00123456")["results"][0]["oud"] is None


def test_unknown_identifier_returns_no_match(exports):
    assert lookup.lookup_subject("99999999")["results"] == []


def test_lookup_by_company_name(exports):
    result = lookup.lookup_subject("test")["results"]
    assert len(result) == 1
    assert result[0]["name"] == "Žltý test"


def test_stale_export_is_rejected(exports):
    make_export(exports[0], [], "01012000")
    with pytest.raises(lookup.LookupUnavailable):
        lookup.lookup_subject("00123456")


@pytest.mark.parametrize("iban", ["SK0081805002408026569576", "", "SK3112000000198742637541"])
def test_invalid_or_non_tax_account_is_rejected(iban):
    with pytest.raises(lookup.LookupUnavailable):
        lookup.oud_from_iban(iban)


def test_endpoint_validates_identifier_without_download(monkeypatch):
    monkeypatch.setattr(lookup, "export_path", lambda _: pytest.fail("Unexpected download"))
    assert TestClient(app).post("/subject-lookup", json={"identifier": "12"}).status_code == 422


def test_endpoint_reports_unavailable_source(monkeypatch):
    def unavailable(_):
        raise lookup.LookupUnavailable("Zdroj je nedostupný.")
    monkeypatch.setattr(lookup, "export_path", unavailable)
    response = TestClient(app).post("/subject-lookup", json={"identifier": "00123456"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Zdroj je nedostupný."
