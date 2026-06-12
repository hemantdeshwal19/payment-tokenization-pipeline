import uuid

# In production: replace with a database (Postgres, Redis, etc.)
# This is an intentional simplification for the pipeline demo
_store: dict[str, str] = {}

def store_token(encrypted_value: str) -> str:
    token = str(uuid.uuid4())
    _store[token] = encrypted_value
    return token

def retrieve_token(token: str) -> str | None:
    return _store.get(token)
