from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)

    def session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    engine.dispose()


PAYLOAD = {"name": "Test", "oud": "8026760001", "ico": "00123456"}


def test_repeated_save_returns_existing_subject(client):
    first = client.post("/subjects", json=PAYLOAD)
    second = client.post("/subjects", json=PAYLOAD)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert len(client.get("/subjects").json()) == 1


def test_parallel_saves_create_one_subject(client):
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: client.post("/subjects", json=PAYLOAD), range(4)))
    assert all(response.status_code in (200, 201) for response in responses)
    assert len({response.json()["id"] for response in responses}) == 1
    assert len(client.get("/subjects").json()) == 1


def test_conflicting_identifier_does_not_overwrite_subject(client):
    client.post("/subjects", json=PAYLOAD)
    response = client.post("/subjects", json={**PAYLOAD, "ico": "87654321"})
    assert response.status_code == 409
    assert client.get("/subjects").json()[0]["ico"] == "00123456"


def test_update_cannot_duplicate_another_subject(client):
    client.post("/subjects", json=PAYLOAD)
    other = client.post("/subjects", json={"name": "Other", "oud": "8026760002"}).json()
    response = client.put(f"/subjects/{other['id']}", json=PAYLOAD)
    assert response.status_code == 409
    assert len(client.get("/subjects").json()) == 2
