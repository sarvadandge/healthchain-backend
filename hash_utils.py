import hashlib
import json

def generate_hash(data: dict) -> str:
    """SHA-256 hash of a dict. Keys are sorted for consistency."""
    json_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_string.encode()).hexdigest()
