import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

PINATA_API_KEY    = os.getenv("PINATA_API_KEY")
PINATA_SECRET_KEY = os.getenv("PINATA_SECRET_KEY")
PINATA_JSON_URL   = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
PINATA_FILE_URL   = "https://api.pinata.cloud/pinning/pinFileToIPFS"
GATEWAY           = "https://gateway.pinata.cloud/ipfs"

def _headers():
    return {
        "pinata_api_key":        PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_KEY,
    }

# ─── JSON (sensor data) ───────────────────────────────────────

def upload_json_to_ipfs(data: dict) -> str:
    """Upload JSON dict to IPFS. Returns CID."""
    headers = {**_headers(), "Content-Type": "application/json"}
    payload = {
        "pinataContent":  data,
        "pinataMetadata": {
            "name": f"sensor_{data.get('sensor_id','x')}_{data.get('timestamp','')}"
        }
    }
    r = requests.post(PINATA_JSON_URL, json=payload, headers=headers, timeout=30)
    if r.status_code == 200:
        cid = r.json()["IpfsHash"]
        print(f"✅ JSON → IPFS: {cid}")
        return cid
    raise Exception(f"Pinata JSON upload failed: {r.text}")

def fetch_json_from_ipfs(cid: str) -> dict:
    """Fetch JSON from IPFS by CID."""
    r = requests.get(f"{GATEWAY}/{cid}", timeout=15)
    if r.status_code == 200:
        return r.json()
    raise Exception(f"IPFS fetch failed [{cid}]: {r.text}")

# ─── File (patient reports) ───────────────────────────────────

def upload_file_to_ipfs(file_bytes: bytes, filename: str) -> str:
    """Upload encrypted file to IPFS. Returns CID."""
    files = {"file": (filename, file_bytes, "application/octet-stream")}
    r = requests.post(
        PINATA_FILE_URL,
        files=files,
        headers=_headers(),
        data={"pinataMetadata": json.dumps({"name": filename})},
        timeout=60
    )
    if r.status_code == 200:
        cid = r.json()["IpfsHash"]
        print(f"✅ File → IPFS: {cid}")
        return cid
    raise Exception(f"Pinata file upload failed: {r.text}")

def fetch_file_from_ipfs(cid: str) -> bytes:
    """Fetch encrypted file bytes from IPFS."""
    r = requests.get(f"{GATEWAY}/{cid}", timeout=30)
    if r.status_code == 200:
        return r.content
    raise Exception(f"IPFS file fetch failed [{cid}]: {r.text}")
