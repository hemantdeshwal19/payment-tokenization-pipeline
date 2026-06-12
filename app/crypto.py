import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Key must be 32 bytes for AES-256
# In production this comes from a secrets manager, never hardcoded
_KEY = os.environ.get("ENCRYPTION_KEY", "dev-only-key-do-not-use-in-prod!!").encode()[:32]

def encrypt(plaintext: str) -> str:
    cipher = AES.new(_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode()
    ct = base64.b64encode(ct_bytes).decode()
    return f"{iv}:{ct}"

def decrypt(token_data: str) -> str:
    iv_b64, ct_b64 = token_data.split(":")
    iv = base64.b64decode(iv_b64)
    ct = base64.b64decode(ct_b64)
    cipher = AES.new(_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size).decode()
