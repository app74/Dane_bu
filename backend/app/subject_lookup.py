"""Exact identifier lookup in the official, published FS XML exports."""

import io
import json
import re
import sqlite3
import tempfile
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

from .domain.iban import validate_iban

SOURCE = "https://www.financnasprava.sk/sk/danovi-a-colni-specialisti/technicke-informacie/podklady-pre-tvorcov-sw/exporty-informacnych-zoznamov"
CACHE = Path(tempfile.gettempdir()) / "dane-bu-fs-exports"
LOCK = threading.Lock()
INDEX_LOCK = threading.Lock()


class LookupUnavailable(Exception):
    pass


def export_path(name: str) -> Path:
    with LOCK:
        CACHE.mkdir(exist_ok=True)
        path = CACHE / f"{name}.zip"
        if path.exists() and time.time() - path.stat().st_mtime < 86400:
            return path
        temporary = path.with_suffix(".download")
        try:
            url = f"https://report.financnasprava.sk/{name}.zip"
            with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as out:
                size = 0
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > 150 * 1024 * 1024:
                        raise LookupUnavailable("Export FS je príliš veľký.")
                    out.write(chunk)
            with zipfile.ZipFile(temporary) as archive:
                info = archive.getinfo(f"{name}.xml")
                if info.file_size > 1024 * 1024 * 1024:
                    raise LookupUnavailable("Export FS je príliš veľký.")
            temporary.replace(path)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
            raise LookupUnavailable(
                "Export Finančnej správy nie je dostupný. Skúste neskôr."
            ) from error
        finally:
            temporary.unlink(missing_ok=True)
        return path


def build_index(path: Path, target: Path) -> None:
    updated = ""
    with closing(sqlite3.connect(target)) as db, db, zipfile.ZipFile(path) as archive:
        db.execute("CREATE TABLE rows (ico TEXT, dic TEXT, data TEXT)")
        db.execute("CREATE TABLE metadata (updated TEXT)")
        xml_names = [name for name in archive.namelist() if name.endswith(".xml")]
        if len(xml_names) != 1:
            raise LookupUnavailable("Neznámy formát exportu FS.")
        with archive.open(xml_names[0]) as raw:
            # FS declares UTF-8; reject damaged text rather than changing names silently.
            stream = io.TextIOWrapper(raw, encoding="utf-8")
            stack = []
            for event, element in ET.iterparse(stream, events=("start", "end")):
                if event == "start":
                    stack.append(element)
                    continue
                if element.tag == "DatumAktualizacieZoznamu":
                    updated = datetime.strptime(element.text or "", "%d%m%Y").date().isoformat()
                if element.tag == "ITEM":
                    row = {child.tag: (child.text or "").strip() for child in element}
                    db.execute("INSERT INTO rows VALUES (?, ?, ?)",
                               (row.get("ICO"), row.get("DIC"), json.dumps(row)))
                    stack[-2].remove(element)
                stack.pop()
        db.execute("CREATE INDEX by_ico ON rows(ico)")
        db.execute("CREATE INDEX by_dic ON rows(dic)")
        db.execute("INSERT INTO metadata VALUES (?)", (updated,))


def find_rows(path: Path, field: str, values: set[str]) -> tuple[list[dict], str]:
    if field not in {"ICO", "DIC"}:
        raise ValueError("Nepodporovaný identifikátor.")
    target = path.with_suffix(".db")
    with INDEX_LOCK:
        if not target.exists() or target.stat().st_mtime < path.stat().st_mtime:
            temporary = path.with_suffix(".building.db")
            temporary.unlink(missing_ok=True)
            try:
                build_index(path, temporary)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
    with closing(sqlite3.connect(target)) as db:
        updated = db.execute("SELECT updated FROM metadata").fetchone()[0]
        rows = []
        for value in sorted(values):
            rows.extend(json.loads(row[0]) for row in db.execute(
                f"SELECT data FROM rows WHERE {field.lower()} = ?", (value,)))
    if not updated or not 0 <= (date.today() - date.fromisoformat(updated)).days <= 3:
        raise LookupUnavailable("Export FS nemá aktuálny dátum. Overte OÚD ručne na portáli FS.")
    return rows, updated


def find_rows_by_name(path: Path, query: str) -> tuple[list[dict], str]:
    target = path.with_suffix(".db")
    with INDEX_LOCK:
        if not target.exists() or target.stat().st_mtime < path.stat().st_mtime:
            temporary = path.with_suffix(".building.db")
            temporary.unlink(missing_ok=True)
            try:
                build_index(path, temporary)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
    pattern = f"%{query.casefold()}%"
    with closing(sqlite3.connect(target)) as db:
        updated = db.execute("SELECT updated FROM metadata").fetchone()[0]
        rows = [json.loads(row[0]) for row in db.execute(
            "SELECT data FROM rows WHERE lower(json_extract(data, '$.NAZOV_DS')) LIKE ?", (pattern,)
        )]
    if not updated or not 0 <= (date.today() - date.fromisoformat(updated)).days <= 3:
        raise LookupUnavailable("Export FS nemá aktuálny dátum. Overte OÚD ručne na portáli FS.")
    return rows, updated


def oud_from_iban(iban: str) -> str:
    iban = iban.replace(" ", "").upper()
    if not validate_iban(iban) or iban[4:8] != "8180" or iban[8:14] != "500240":
        raise LookupUnavailable("Účet v exporte FS nemá očakávaný platný formát.")
    return iban[14:24]


def lookup_subject(identifier: str) -> dict:
    query = identifier.strip()
    compact = re.sub(r"\s+", "", query)
    if re.fullmatch(r"(?:[0-9]{8}|[0-9]{10})", compact):
        field, value = ("ICO", compact) if len(compact) == 8 else ("DIC", compact)
        def query_rows() -> tuple[list[dict], str]:
            return find_rows(export_path("ds_dsrdp"), field, {value})
    elif len(query) >= 3:
        def query_rows() -> tuple[list[dict], str]:
            return find_rows_by_name(export_path("ds_dsrdp"), query)
    else:
        raise ValueError("Zadajte celé IČO, DIČ alebo aspoň 3 znaky názvu spoločnosti.")
    try:
        registered, registry_date = query_rows()
        icos = {row["ICO"] for row in registered if row.get("ICO")}
        if "field" in locals() and field == "ICO":
            icos.add(value)
        accounts, account_date = find_rows(export_path("ds_dph_oud"), "ICO", icos)
        results = []
        for row in registered:
            matches = [a for a in accounts if a.get("ICO") == row.get("ICO")]
            # Never choose silently between conflicting accounts.
            unique_accounts = {a.get("IBAN", "") for a in matches}
            account = matches[0] if len(unique_accounts) == 1 else None
            results.append({
                "name": row.get("NAZOV_DS", ""), "ico": row.get("ICO") or None,
                "dic": row.get("DIC") or None,
                "ic_dph": account.get("IC_DPH") if account else None,
                "oud": oud_from_iban(account["IBAN"]) if account else None,
                "address": ", ".join(filter(None, [row.get("ULICA_CISLO"), row.get("OBEC")])),
            })
        if not registered and 'field' in locals() and field == "ICO":
            for account in accounts:
                results.append({
                    "name": account.get("NAZOV_SUBJEKTU", ""), "ico": identifier,
                    "dic": None, "ic_dph": account.get("IC_DPH"),
                    "oud": oud_from_iban(account.get("IBAN", "")),
                    "address": account.get("OBEC", ""),
                })
        return {
            "results": results, "source_url": SOURCE,
            "registry_date": registry_date, "accounts_date": account_date,
        }
    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile, sqlite3.Error) as error:
        raise LookupUnavailable(
            "Údaje FS sa nepodarilo bezpečne načítať. Overte OÚD ručne."
        ) from error
