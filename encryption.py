import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = bytes.fromhex(os.getenv("ENCRYPTION_KEY"))

def encrypt_file(file_bytes: bytes) -> tuple[bytes, str]:
    """AES-256-GCM encrypt. Returns (encrypted_bytes, nonce_hex)."""
    aesgcm = AESGCM(ENCRYPTION_KEY)
    nonce  = os.urandom(12)
    encrypted = aesgcm.encrypt(nonce, file_bytes, None)
    return encrypted, nonce.hex()

def decrypt_file(encrypted_bytes: bytes, nonce_hex: str) -> bytes:
    """AES-256-GCM decrypt."""
    aesgcm = AESGCM(ENCRYPTION_KEY)
    nonce  = bytes.fromhex(nonce_hex)
    return aesgcm.decrypt(nonce, encrypted_bytes, None)
