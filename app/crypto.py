import os
import base64
from Crypto.Cipher import AES

# Key must be 32 bytes for AES-256
# In production this comes from a secrets manager, never hardcoded
_KEY = os.environ.get("ENCRYPTION_KEY", "dev-only-key-do-not-use-in-prod!!").encode()[:32]

def encrypt(plaintext: str) -> str:
    cipher = AES.new(_KEY, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    nonce = base64.b64encode(cipher.nonce).decode()
    ct = base64.b64encode(ciphertext).decode()
    t = base64.b64encode(tag).decode()
    return f"{nonce}:{ct}:{t}"

def decrypt(token_data: str) -> str:
    nonce_b64, ct_b64, tag_b64 = token_data.split(":")
    nonce = base64.b64decode(nonce_b64)
    ct = base64.b64decode(ct_b64)
    tag = base64.b64decode(tag_b64)
    cipher = AES.new(_KEY, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag).decode()
