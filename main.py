from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, constr, conint
from typing import List, Optional, Dict, Any
import httpx
import os
import json
import jsonschema
from jsonschema import validate, ValidationError


FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "https://fhir-bootcamp.medblocks.com/fhir")

# Load FHIR schema on startup
with open("fhir.schema.json", "r") as schema_file:
    FHIR_SCHEMA = json.load(schema_file)


class HumanName(BaseModel):
    family: Optional[str] = None
    given: Optional[List[str]] = None


class Telecom(BaseModel):
    system: constr(strip_whitespace=True) = Field(default="phone")
    value: constr(strip_whitespace=True)


class PatientCreate(BaseModel):
    given: constr(strip_whitespace=True, min_length=1)
    family: constr(strip_whitespace=True, min_length=1)
    gender: constr(strip_whitespace=True, min_length=1)
    birthDate: constr(strip_whitespace=True, min_length=1)
    phone: conint(strict=True)


class PatientUpdate(BaseModel):
    given: Optional[constr(strip_whitespace=True, min_length=1)] = None
    family: Optional[constr(strip_whitespace=True, min_length=1)] = None
    gender: Optional[constr(strip_whitespace=True, min_length=1)] = None
    birthDate: Optional[constr(strip_whitespace=True, min_length=1)] = None
    phone: Optional[conint(strict=True)] = None


class PatientSummary(BaseModel):
    id: str
    identifier: Optional[str] = None
    given: Optional[str] = None
    family: Optional[str] = None
    gender: Optional[str] = None
    birthDate: Optional[str] = None
    phone: Optional[str] = None
    lastUpdated: Optional[str] = None


app = FastAPI(title="Patient Management API (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


async def fhir_get(path: str, params: Optional[Dict[str, Any]] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
    server_url = base_url or FHIR_BASE_URL
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{server_url}/{path.lstrip('/')}", params=params)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR request failed: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"FHIR connection error: {e}")


async def fhir_post(resource_type: str, data: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    server_url = base_url or FHIR_BASE_URL
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{server_url}/{resource_type}", json=data)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR request failed: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"FHIR connection error: {e}")


async def fhir_put(resource_type: str, resource_id: str, data: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    server_url = base_url or FHIR_BASE_URL
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.put(f"{server_url}/{resource_type}/{resource_id}", json=data)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR request failed: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"FHIR connection error: {e}")


def build_patient_resource(given: str, family: str, gender: str, birthDate: str, phone: Optional[int]) -> Dict[str, Any]:
    resource = {
        "resourceType": "Patient",
        "name": [
            {
                "use": "official",
                "family": family,
                "given": [given],
            }
        ],
        "gender": gender.lower(),
        "birthDate": birthDate,
    }
    if phone is not None:
        resource["telecom"] = [{"system": "phone", "value": str(phone)}]
    return resource


def validate_birthdate_not_future(birth_date: str) -> None:
    # Simple YYYY-MM-DD validation against today
    from datetime import date
    try:
        parts = [int(x) for x in birth_date.split("-")]
        if len(parts) != 3:
            return
        year, month, day = parts
        d = date(year, month, day)
    except Exception:
        return
    if d > date.today():
        raise HTTPException(status_code=422, detail="Date of Birth cannot be in the future.")


def validate_resource_against_fhir_schema(resource: Dict[str, Any]) -> None:
    """
    Layer 3: FHIR Schema validation using jsonschema
    Validates the constructed FHIR resource against fhir.schema.json
    """
    try:
        validate(instance=resource, schema=FHIR_SCHEMA)
    except ValidationError as e:
        # Extract the path and error message for better error reporting
        path = '.'.join(map(str, e.path)) if e.path else 'root'
        error_message = e.message
        
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "detail": f"FHIR schema validation error: {error_message} on path {path}"
            }
        )


def extract_patient_summary(entry: Dict[str, Any]) -> Optional[PatientSummary]:
    res = entry.get("resource") if "resource" in entry else entry
    if not res or res.get("resourceType") != "Patient":
        return None
    pid = res.get("id", "")
    # Prefer official identifier value if present; otherwise fallback to resource id
    identifier = res.get("id")
    identifiers = res.get("identifier") or []
    if identifiers:
        identifier = identifiers[0].get("value") or identifiers[0].get("id") or identifier
    given_val = None
    family_val = None
    names = res.get("name") or []
    if names:
        name_obj = names[0]
        given_list = name_obj.get("given", []) or []
        given_val = (given_list[0] if given_list else None)
        if isinstance(given_val, str):
            given_val = given_val.strip()
        family_val = (name_obj.get("family") or "").strip() or None
    phone_val = None
    telecom = res.get("telecom") or []
    for t in telecom:
        if t.get("system") == "phone" and t.get("value"):
            phone_val = t.get("value")
            break
    gender = res.get("gender")
    birthDate = res.get("birthDate")
    # Extract lastUpdated from meta field
    lastUpdated = None
    meta = res.get("meta", {})
    if meta and "lastUpdated" in meta:
        lastUpdated = meta["lastUpdated"]
    return PatientSummary(id=pid, identifier=identifier, given=given_val, family=family_val, gender=gender, birthDate=birthDate, phone=phone_val, lastUpdated=lastUpdated)


@app.get("/patients", response_model=List[PatientSummary])
async def list_patients(
    fhir_server_url: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default=None, description="Sort by field (e.g., '-_lastUpdated' for descending, '_lastUpdated' for ascending)")
) -> List[PatientSummary]:
    server_url = fhir_server_url or FHIR_BASE_URL
    params = {"_count": 15}
    if sort:
        params["_sort"] = sort
    bundle = await fhir_get("Patient", params=params, base_url=server_url)
    entries = bundle.get("entry", [])
    summaries: List[PatientSummary] = []
    for e in entries:
        summary = extract_patient_summary(e)
        if summary:
            summaries.append(summary)
    return summaries


@app.post("/patients", response_model=PatientSummary)
async def create_patient(payload: PatientCreate, fhir_server_url: Optional[str] = Query(default=None)) -> PatientSummary:
    # Layer 1: Pydantic validation (automatic via PatientCreate model)
    # Layer 2: Business Rules validation
    validate_birthdate_not_future(payload.birthDate)
    
    # Build the FHIR resource
    resource = build_patient_resource(
        given=payload.given,
        family=payload.family,
        gender=payload.gender,
        birthDate=payload.birthDate,
        phone=payload.phone,
    )
    
    # Layer 3: FHIR Schema validation
    validate_resource_against_fhir_schema(resource)
    
    server_url = fhir_server_url or FHIR_BASE_URL
    created = await fhir_post("Patient", resource, base_url=server_url)
    summary = extract_patient_summary(created)
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to create patient")
    return summary


@app.put("/patients/{patient_id}", response_model=PatientSummary)
async def update_patient(patient_id: str, payload: PatientUpdate, fhir_server_url: Optional[str] = Query(default=None)) -> PatientSummary:
    # Layer 1: Pydantic validation (automatic via PatientUpdate model)
    server_url = fhir_server_url or FHIR_BASE_URL
    existing = await fhir_get(f"Patient/{patient_id}", base_url=server_url)
    if not existing or existing.get("resourceType") != "Patient":
        raise HTTPException(status_code=404, detail="Patient not found")

    # Merge updates into existing resource according to FHIR
    if payload.birthDate is not None:
        # Layer 2: Business Rules validation
        validate_birthdate_not_future(payload.birthDate)
    if payload.given is not None or payload.family is not None:
        names = existing.get("name") or [{}]
        name_obj = names[0] if names else {}
        if payload.given is not None:
            name_obj["given"] = [payload.given]
        if payload.family is not None:
            name_obj["family"] = payload.family
        existing["name"] = [name_obj]
    if payload.gender is not None:
        existing["gender"] = payload.gender.lower()
    if payload.birthDate is not None:
        existing["birthDate"] = payload.birthDate
    if payload.phone is not None:
        if payload.phone == "":
            # Remove phone if empty string provided
            telecom = existing.get("telecom") or []
            telecom = [t for t in telecom if t.get("system") != "phone"]
            existing["telecom"] = telecom
        else:
            existing["telecom"] = [{"system": "phone", "value": str(payload.phone)}]

    # Layer 3: FHIR Schema validation
    validate_resource_against_fhir_schema(existing)

    updated = await fhir_put("Patient", patient_id, existing, base_url=server_url)
    summary = extract_patient_summary(updated)
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to update patient")
    return summary


@app.get("/patients/search", response_model=List[PatientSummary])
async def search_patients(
    name: Optional[str] = Query(default=None), 
    phone: Optional[str] = Query(default=None), 
    identifier: Optional[str] = Query(default=None), 
    fhir_server_url: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default=None, description="Sort by field (e.g., '-_lastUpdated' for descending, '_lastUpdated' for ascending)")
) -> List[PatientSummary]:
    params: Dict[str, Any] = {"_count": 15}
    if name:
        params["name"] = name
    if phone:
        params["telecom"] = phone
    if identifier:
        params["_id"] = identifier
    if sort:
        params["_sort"] = sort
    server_url = fhir_server_url or FHIR_BASE_URL
    bundle = await fhir_get("Patient", params=params, base_url=server_url)
    entries = bundle.get("entry", [])
    results: List[PatientSummary] = []
    for e in entries:
        summary = extract_patient_summary(e)
        if summary:
            results.append(summary)
    return results


@app.get("/")
async def root():
    return {"message": "Patient Management API running", "docs": "/docs", "frontend": "/static/index.html"}


# To run: uvicorn main:app --reload

