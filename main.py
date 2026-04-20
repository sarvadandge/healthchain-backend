from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import hashlib
import json
import os

from ipfs import (
    upload_json_to_ipfs, fetch_json_from_ipfs,
    upload_file_to_ipfs,  fetch_file_from_ipfs,
)
from hash_utils import generate_hash
from encryption import encrypt_file, decrypt_file
from blockchain import (
    # sensor
    store_sensor_data, get_latest_sensor_record,
    get_sensor_history, get_sensor_record_count,
    verify_sensor_integrity,
    # reports
    upload_report, get_patient_reports, get_report_count,
    # doctor
    grant_doctor_access, revoke_doctor_access, check_doctor_access,
    # emergency
    add_emergency_contact, remove_emergency_contact,
    get_emergency_contacts, check_emergency_contact, get_caller_role,
    # misc
    contract, w3, PRIVATE_KEY, ABI,
)

app = FastAPI(title="HealthChain API")

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request models ───────────────────────────────────────────

class SensorData(BaseModel):
    sensor_id:  int
    data_type:  str
    value:      float
    unit:       str
    patient_id: str
    location:   str

class VerifyRequest(BaseModel):
    sensor_id:    int
    record_index: int
    cid:          str

class DoctorRequest(BaseModel):
    patient_id:     str
    doctor_address: str

class EmergencyContactRequest(BaseModel):
    patient_id:     str
    contact_wallet: str
    name:           str
    relation:       str

class RemoveContactRequest(BaseModel):
    patient_id:     str
    contact_wallet: str

class RoleRequest(BaseModel):
    patient_id:     str
    caller_address: str


# ─────────────────────────────────────────────────────────────
# SENSOR ROUTES
# ─────────────────────────────────────────────────────────────

@app.post("/sensor/upload")
async def sensor_upload(data: SensorData):
    try:
        payload = {
            "sensor_id":  data.sensor_id,
            "data_type":  data.data_type,
            "value":      data.value,
            "unit":       data.unit,
            "patient_id": data.patient_id,
            "location":   data.location,
            "timestamp":  datetime.utcnow().isoformat(),
        }
        data_hash = generate_hash(payload)
        cid       = upload_json_to_ipfs(payload)
        tx_hash   = store_sensor_data(data.sensor_id, cid, data_hash, data.data_type)
        return {"success": True, "cid": cid, "data_hash": data_hash, "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sensor/verify")
async def sensor_verify(req: VerifyRequest):
    try:
        ipfs_data     = fetch_json_from_ipfs(req.cid)
        computed_hash = generate_hash(ipfs_data)
        tx_hash       = verify_sensor_integrity(
            req.sensor_id, req.record_index, computed_hash
        )
        return {"cid": req.cid, "computed_hash": computed_hash, "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sensor/{sensor_id}/latest")
async def sensor_latest(sensor_id: int):
    try:
        return get_latest_sensor_record(sensor_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sensor/{sensor_id}/history")
async def sensor_history(sensor_id: int):
    try:
        return {"records": get_sensor_history(sensor_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sensor/{sensor_id}/count")
async def sensor_count(sensor_id: int):
    try:
        return {"count": get_sensor_record_count(sensor_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# PATIENT REPORT ROUTES
# ─────────────────────────────────────────────────────────────

@app.post("/patient/upload-report")
async def patient_upload_report(
    patient_id:  str        = Form(...),
    report_type: str        = Form(...),
    file:        UploadFile = File(...),
):
    try:
        file_bytes = await file.read()
        file_hash  = hashlib.sha256(file_bytes).hexdigest()

        encrypted_bytes, nonce = encrypt_file(file_bytes)
        filename = f"{patient_id}_{report_type}_{file.filename}"
        cid      = upload_file_to_ipfs(encrypted_bytes, filename)
        tx_hash  = upload_report(patient_id, cid, file_hash, report_type, nonce)

        return {
            "success":     True,
            "cid":         cid,
            "file_hash":   file_hash,
            "report_type": report_type,
            "tx_hash":     tx_hash,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/reports")
async def patient_reports(patient_id: str):
    try:
        return {"reports": get_patient_reports(patient_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/report-count")
async def patient_report_count(patient_id: str):
    try:
        return {"count": get_report_count(patient_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/get-report/{cid}")
async def get_report_file(cid: str, nonce: str):
    try:
        encrypted = fetch_file_from_ipfs(cid)
        decrypted = decrypt_file(encrypted, nonce)
        return Response(
            content=decrypted,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=report_{cid[:8]}.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# DOCTOR ACCESS ROUTES
# ─────────────────────────────────────────────────────────────

@app.post("/patient/grant-doctor")
async def grant_doctor(req: DoctorRequest):
    try:
        tx = grant_doctor_access(req.patient_id, req.doctor_address)
        return {"success": True, "tx_hash": tx}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patient/revoke-doctor")
async def revoke_doctor(req: DoctorRequest):
    try:
        tx = revoke_doctor_access(req.patient_id, req.doctor_address)
        return {"success": True, "tx_hash": tx}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/check-doctor/{doctor_address}")
async def check_doctor(patient_id: str, doctor_address: str):
    try:
        return {"has_access": check_doctor_access(patient_id, doctor_address)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# EMERGENCY CONTACT ROUTES
# ─────────────────────────────────────────────────────────────

@app.post("/patient/emergency-contact/add")
async def emergency_add(req: EmergencyContactRequest):
    try:
        tx = add_emergency_contact(
            req.patient_id, req.contact_wallet, req.name, req.relation
        )
        return {"success": True, "tx_hash": tx}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patient/emergency-contact/remove")
async def emergency_remove(req: RemoveContactRequest):
    try:
        tx = remove_emergency_contact(req.patient_id, req.contact_wallet)
        return {"success": True, "tx_hash": tx}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/emergency-contacts")
async def emergency_list(patient_id: str):
    try:
        return {"contacts": get_emergency_contacts(patient_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/check-emergency/{address}")
async def emergency_check(patient_id: str, address: str):
    try:
        return {"is_emergency_contact": check_emergency_contact(patient_id, address)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patient/role")
async def role_check(req: RoleRequest):
    try:
        role = get_caller_role(req.patient_id, req.caller_address)
        return {"patient_id": req.patient_id, "caller": req.caller_address, "role": role}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# HEALTH + DEBUG ROUTES
# ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "running"}

@app.get("/status")
async def status():
    from web3 import Web3
    account = w3.eth.account.from_key(PRIVATE_KEY)
    balance = w3.eth.get_balance(account.address)
    return {
        "connected":        w3.is_connected(),
        "chain_id":         w3.eth.chain_id,
        "wallet":           account.address,
        "balance_matic":    float(Web3.from_wei(balance, "ether")),
        "contract_address": contract.address,
    }

@app.get("/debug/{patient_id}")
async def debug_patient(patient_id: str):
    try:
        count = get_report_count(patient_id)
        reports = get_patient_reports(patient_id)
        return {
            "patient_id":     patient_id,
            "report_count":   count,
            "reports_length": len(reports),
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/abis/healthchain")
async def get_abi():
    return {"abi": ABI}
