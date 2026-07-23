import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.crypto import encrypt, decrypt
from app.vault import store_token, retrieve_token

app = FastAPI(title="Tokenization Service")

class TokenizeRequest(BaseModel):
    card_number: str

class TokenizeResponse(BaseModel):
    token: str

class DetokenizeRequest(BaseModel):
    token: str

class DetokenizeResponse(BaseModel):
    card_number: str


@app.post("/tokenize", response_model=TokenizeResponse)
def tokenize(req: TokenizeRequest):
    if not req.card_number.isdigit() or len(req.card_number) not in range(13, 20):
        raise HTTPException(status_code=400, detail="Invalid card number format")
    encrypted = encrypt(req.card_number)
    token = store_token(encrypted)
    return TokenizeResponse(token=token)


@app.post("/detokenize", response_model=DetokenizeResponse)
def detokenize(req: DetokenizeRequest):
    encrypted = retrieve_token(req.token)
    if not encrypted:
        raise HTTPException(status_code=404, detail="Token not found")
    card_number = decrypt(encrypted)
    return DetokenizeResponse(card_number=card_number)


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Monit lab: intentional memory leak endpoint, for testing the ---
# --- "if totalmem > 250 MB then restart" rule. Not production code. ---
if os.environ.get("ENABLE_LEAK_TEST") == "1":
    _leak_store = []

    @app.post("/leak")
    def leak():
        _leak_store.append("x" * 10_000_000)  # ~10MB per call
        return {"leaked_mb": len(_leak_store) * 10}
