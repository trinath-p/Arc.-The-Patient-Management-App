# Patient Management MVP (FastAPI + Static Frontend)

A minimal Patient Management app that uses a public FHIR test server as the backend data source. Built with FastAPI and a static HTML/CSS/JS frontend.

- Backend: FastAPI, proxied to `https://fhir-bootcamp.medblocks.com/fhir`
- Frontend: Single page (`/static/index.html`) using vanilla JS
- Features: List, Create, Update, and Search Patients

## Prerequisites
- Python 3.10+
- Windows PowerShell or any terminal

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API root: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:8000/static/index.html`

## App Overview

This app is a minimal patient registry that proxies to a public FHIR server. It intentionally avoids a local DB to keep the surface small. The backend normalizes/sanitizes data into FHIR Patient resources; the frontend provides a simple SPA experience.

### What you can do
- List patients (first 50)
- Search by name and/or phone (partial)
- Search by identifier (exact) via the Identifier field in the search bar
- Create a patient
- Update an existing patient

All operations occur against the configured FHIR server and are reflected immediately in the UI after success.

## Enhancements

### Error handling
- Server unavailable: UI shows "FHIR server unavailable, try later." when network/DNS errors occur.
- No results: Lists and searches display "No patient found.". Phone-specific searches show "No patient found with this phone number.".
- Creation failure: UI displays "Patient could not be created. Please try again.".

### Loading state
- Centered overlay loader (webM) blocks the UI during create/update.
- Section-level loader replaces the Patients table body with a "Loading…" message while listing or searching.
- On first page load, only the table-scoped loading appears (no blocking overlay flash).

### Centralized alerts
- Reusable alert/toast system (success/info/error) used for success/failure and informational messages.


## Testing the scenarios
- Server down: Set `FHIR_BASE_URL` to an invalid host or disconnect network; attempt list or search. Expect server unavailable alert.
- No results: Search for a random name or uncommon phone to see "No patient found" messages.
- Success path: Create with valid inputs; you should see "Created: Patient #<identifier>" and the list refreshes.

## Validation and data rules
- Date of Birth cannot be in the future (enforced in UI and API).
- Phone number is required for creation and must be numeric:
  - Backend: Pydantic `conint(strict=True)` for `PatientCreate.phone` and optional numeric for updates.
  - Frontend: numeric input (`type="number"` + `inputmode="numeric"`), parsed to `Number`; non-numeric shows an error.
- Success messages display the Patient Identifier (e.g., "Created: Patient #2260").
- Requests do not use artificial timeouts; loader remains until the request completes or fails.

## Configuration
- Backend FHIR URL: `FHIR_BASE_URL` environment variable (default `https://fhir-bootcamp.medblocks.com/fhir`).
- Client appearance: loader video at `static/loading.webm`; you can replace it with any webM.
- Colors/icons: date input uses a light calendar icon for contrast; adjust in `static/style.css`.

## API design (brief)
- `GET /patients`: returns an array of simplified patients `{ id, identifier, given, family, gender, birthDate, phone }` built from FHIR `Patient`.
- `POST /patients`: accepts `{ given, family, gender, birthDate, phone }`, validates, and creates FHIR Patient.
- `PUT /patients/{id}`: partial updates; sanitizes name fields and phone.
- `GET /patients/search?name&phone`: bundles FHIR search; returns simplified array.
- `GET /patients/search?identifier` is also supported (exact identifier match).

## Notes
- No local database is used. All patient operations are relayed to the public FHIR server.
- We intentionally use a minimal FHIR Patient subset for MVP clarity.
