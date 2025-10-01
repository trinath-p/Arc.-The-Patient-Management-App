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

## Features

### Patient Management
- **List Patients**: View all patients with pagination (15 per page)
- **Create Patient**: Add new patients with validation
- **Update Patient**: Edit existing patient information (partial updates supported)
- **Search Patients**: Multiple search methods available

### Search Capabilities
- **Name Search**: Partial matching on patient names
- **Phone Search**: Search by phone number
- **Identifier Search**: Exact match by patient identifier
- **Combined Search**: Use multiple search criteria simultaneously
- **Sort Options**: Sort by last updated (ascending/descending)

### FHIR Server Integration
- **Configurable Server**: Switch between different FHIR servers
- **URL Management**: Save and reuse previously used FHIR server URLs
- **Real-time Operations**: All operations reflect immediately in the UI
- **Error Handling**: Graceful handling of server unavailability

### Data Validation & Rules
- **Future Date Prevention**: Date of Birth cannot be in the future
- **Phone Validation**: Numeric phone number validation (required for creation)
- **Required Fields**: First name, last name, gender, and birth date are mandatory
- **Data Sanitization**: Automatic trimming and normalization of input data

### User Interface Features
- **Responsive Design**: Works on desktop and mobile devices
- **Loading States**: Visual feedback during operations
  - Full-screen overlay loader for create/update operations
  - Table-specific loading for list/search operations
- **Alert System**: Success, error, and informational messages
- **Form Management**: Clear form functionality and validation feedback

### Advanced Features
- **FHIR Resource Mapping**: Converts between simplified API format and FHIR Patient resources
- **Identifier Management**: Handles both FHIR resource IDs and official identifiers
- **Telecom Support**: Phone number management with system specification
- **Meta Data Tracking**: Last updated timestamps from FHIR meta fields
- **CORS Support**: Cross-origin resource sharing enabled for API access

### Configuration Options
- **Environment Variables**: FHIR_BASE_URL configuration
- **Server Selection**: Dynamic FHIR server URL switching
- **Pagination Control**: Configurable result limits
- **Sort Parameters**: Flexible sorting options via FHIR parameters

### Error Handling
- **Network Errors**: Handles connection failures gracefully
- **Validation Errors**: Clear feedback for invalid input
- **Server Errors**: Proper HTTP status code handling
- **Empty Results**: User-friendly messages for no results found

### Technical Features
- **Async Operations**: Non-blocking HTTP requests
- **Timeout Management**: 30-second timeout for FHIR requests
- **Resource Type Validation**: Ensures only Patient resources are processed
- **Partial Updates**: FHIR-compliant resource merging for updates

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
