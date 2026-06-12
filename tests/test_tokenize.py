import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_tokenize_valid_card():
    response = client.post("/tokenize", json={"card_number": "4111111111111111"})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert len(data["token"]) == 36

def test_tokenize_returns_unique_tokens():
    r1 = client.post("/tokenize", json={"card_number": "4111111111111111"})
    r2 = client.post("/tokenize", json={"card_number": "4111111111111111"})
    assert r1.json()["token"] != r2.json()["token"]

def test_tokenize_invalid_card_letters():
    response = client.post("/tokenize", json={"card_number": "abcd1234efgh"})
    assert response.status_code == 400

def test_tokenize_invalid_card_too_short():
    response = client.post("/tokenize", json={"card_number": "123"})
    assert response.status_code == 400

def test_tokenize_invalid_card_too_long():
    response = client.post("/tokenize", json={"card_number": "123456789012345678901"})
    assert response.status_code == 400

def test_detokenize_valid_token():
    r1 = client.post("/tokenize", json={"card_number": "4111111111111111"})
    token = r1.json()["token"]
    r2 = client.post("/detokenize", json={"token": token})
    assert r2.status_code == 200
    assert r2.json()["card_number"] == "4111111111111111"

def test_detokenize_invalid_token():
    response = client.post("/detokenize", json={"token": "fake-token-that-does-not-exist"})
    assert response.status_code == 404

def test_card_number_not_in_token():
    response = client.post("/tokenize", json={"card_number": "4111111111111111"})
    token = response.json()["token"]
    assert "4111111111111111" not in token
