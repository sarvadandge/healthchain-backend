import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL             = os.getenv("ALCHEMY_RPC")
PRIVATE_KEY         = os.getenv("PRIVATE_KEY")
HEALTHCHAIN_ADDRESS = os.getenv("HEALTHCHAIN_ADDRESS")

if not HEALTHCHAIN_ADDRESS and os.path.exists("/shared/address.txt"):
    with open("/shared/address.txt") as f:
        HEALTHCHAIN_ADDRESS = f.read().strip()
        print("✅ Loaded contract address from shared volume")
# ─── Connect ──────────────────────────────────────────────────
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise Exception("❌ Cannot connect to Polygon. Check ALCHEMY_RPC in .env")

print(f"✅ Connected | Chain ID: {w3.eth.chain_id}")

# ─── Load ABI ─────────────────────────────────────────────────
def _load_abi() -> list:
    shared_path = "/shared/HealthChain.json"

    if os.path.exists(shared_path):
        print("✅ Loading ABI from shared volume")
        with open(shared_path) as f:
            data = json.load(f)
    else:
        print("⚠️ Falling back to local ABI")
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "HealthChain.json")
        if not os.path.exists(path):
            raise FileNotFoundError("HealthChain.json not found")
        with open(path) as f:
            data = json.load(f)

    return data["abi"] if isinstance(data, dict) else data

ABI = _load_abi()

# ─── Contract ─────────────────────────────────────────────────
if not HEALTHCHAIN_ADDRESS:
    raise Exception("❌ HEALTHCHAIN_ADDRESS not set in .env")

contract = w3.eth.contract(
    address=Web3.to_checksum_address(HEALTHCHAIN_ADDRESS),
    abi=ABI
)

print(f"✅ HealthChain loaded at {HEALTHCHAIN_ADDRESS}")

# ─── Shared tx helper ─────────────────────────────────────────
def _send_tx(fn) -> str:
    """Build, sign, send, wait. Raises on revert with reason."""
    account = w3.eth.account.from_key(PRIVATE_KEY)

    txn = fn.build_transaction({
        "from":     account.address,
        "nonce":    w3.eth.get_transaction_count(account.address),
        "gas":      800000,
        "gasPrice": w3.eth.gas_price,
    })

    signed  = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # ── Detect revert ─────────────────────────────────────────
    if receipt.status == 0:
        try:
            w3.eth.call({
                "to":   txn["to"],
                "from": txn["from"],
                "data": txn["data"],
                "gas":  txn["gas"],
            }, receipt.blockNumber)
        except Exception as revert_err:
            raise Exception(f"Transaction reverted: {revert_err}")
        raise Exception(f"Transaction reverted (no reason). tx: {tx_hash.hex()}")

    return tx_hash.hex()


# ─────────────────────────────────────────────────────────────
# SENSOR DATA
# ─────────────────────────────────────────────────────────────

def store_sensor_data(sensor_id: int, cid: str, data_hash: str, data_type: str) -> str:
    tx = _send_tx(contract.functions.storeSensorData(sensor_id, cid, data_hash, data_type))
    print(f"✅ Sensor data stored: {tx}")
    return tx

def get_latest_sensor_record(sensor_id: int) -> dict:
    r = contract.functions.getLatestSensorRecord(sensor_id).call()
    return _parse_sensor(r)

def get_sensor_history(sensor_id: int) -> list:
    records = contract.functions.getSensorHistory(sensor_id).call()
    return [_parse_sensor(r) for r in records]

def get_sensor_record_count(sensor_id: int) -> int:
    return contract.functions.getSensorRecordCount(sensor_id).call()

def _parse_sensor(r) -> dict:
    return {
        "sensor_id":   r[0],
        "ipfs_cid":    r[1],
        "data_hash":   r[2],
        "data_type":   r[3],
        "uploader":    r[4],
        "timestamp":   r[5],
        "is_verified": r[6],
    }

def verify_sensor_integrity(sensor_id: int, record_index: int, computed_hash: str) -> str:
    tx = _send_tx(contract.functions.verifySensorIntegrity(sensor_id, record_index, computed_hash))
    print(f"✅ Integrity verified: {tx}")
    return tx


# ─────────────────────────────────────────────────────────────
# PATIENT REPORTS
# ─────────────────────────────────────────────────────────────

def upload_report(
    patient_id:  str,
    cid:         str,
    file_hash:   str,
    report_type: str,
    nonce:       str
) -> str:
    tx = _send_tx(contract.functions.uploadReport(
        patient_id, cid, file_hash, report_type, nonce
    ))
    print(f"✅ Report uploaded: {tx}")
    return tx

def get_patient_reports(patient_id: str) -> list:
    account = w3.eth.account.from_key(PRIVATE_KEY)
    records = contract.functions.getPatientReports(patient_id).call(
        {"from": account.address}
    )
    return [_parse_report(r) for r in records]

def get_report_count(patient_id: str) -> int:
    return contract.functions.getReportCount(patient_id).call()

def _parse_report(r) -> dict:
    return {
        "report_id":   r[0],
        "patient_id":  r[1],
        "ipfs_cid":    r[2],
        "file_hash":   r[3],
        "report_type": r[4],
        "nonce":       r[5],
        "uploaded_by": r[6],
        "timestamp":   r[7],
        "is_active":   r[8],
    }


# ─────────────────────────────────────────────────────────────
# DOCTOR ACCESS
# ─────────────────────────────────────────────────────────────

def grant_doctor_access(patient_id: str, doctor_address: str) -> str:
    tx = _send_tx(contract.functions.grantDoctorAccess(
        patient_id, Web3.to_checksum_address(doctor_address)
    ))
    print(f"✅ Doctor access granted: {tx}")
    return tx

def revoke_doctor_access(patient_id: str, doctor_address: str) -> str:
    tx = _send_tx(contract.functions.revokeDoctorAccess(
        patient_id, Web3.to_checksum_address(doctor_address)
    ))
    print(f"✅ Doctor access revoked: {tx}")
    return tx

def check_doctor_access(patient_id: str, doctor_address: str) -> bool:
    return contract.functions.checkDoctorAccess(
        patient_id, Web3.to_checksum_address(doctor_address)
    ).call()


# ─────────────────────────────────────────────────────────────
# EMERGENCY CONTACTS
# ─────────────────────────────────────────────────────────────

def add_emergency_contact(
    patient_id: str, contact_wallet: str, name: str, relation: str
) -> str:
    tx = _send_tx(contract.functions.addEmergencyContact(
        patient_id, Web3.to_checksum_address(contact_wallet), name, relation
    ))
    print(f"✅ Emergency contact added: {tx}")
    return tx

def remove_emergency_contact(patient_id: str, contact_wallet: str) -> str:
    tx = _send_tx(contract.functions.removeEmergencyContact(
        patient_id, Web3.to_checksum_address(contact_wallet)
    ))
    print(f"✅ Emergency contact removed: {tx}")
    return tx

def get_emergency_contacts(patient_id: str) -> list:
    account   = w3.eth.account.from_key(PRIVATE_KEY)
    contacts  = contract.functions.getEmergencyContacts(patient_id).call(
        {"from": account.address}
    )
    return [
        {"wallet": c[0], "name": c[1], "relation": c[2], "is_active": c[3]}
        for c in contacts
    ]

def check_emergency_contact(patient_id: str, address: str) -> bool:
    return contract.functions.checkEmergencyContact(
        patient_id, Web3.to_checksum_address(address)
    ).call()

def get_caller_role(patient_id: str, caller_address: str) -> str:
    return contract.functions.getCallerRole(patient_id).call(
        {"from": Web3.to_checksum_address(caller_address)}
    )
