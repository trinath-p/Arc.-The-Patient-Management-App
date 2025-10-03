# Patient Management MVP (FastAPI + Static Frontend)

A comprehensive Patient Management app that connects to FHIR servers as the backend data source. Built with FastAPI and a modern static HTML/CSS/JS frontend with advanced FHIR server management capabilities.

- Backend: FastAPI with dynamic FHIR server support
- Frontend: Single page application (`/static/index.html`) using vanilla JS
- Features: List, Create, Update, Search, and Sort Patients with multi-server support

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

## Quick Start

1. **Start the server**: Run the uvicorn command above
2. **Open the frontend**: Navigate to `http://localhost:8000/static/index.html`
3. **Enter FHIR server URL**: Type a FHIR server URL (e.g., `https://fhir-bootcamp.medblocks.com/fhir`)
4. **Start managing patients**: The app will automatically load patients and you can create, update, search, and sort them

## App Overview

This app is a comprehensive patient registry that connects to FHIR servers dynamically. It intentionally avoids a local DB to keep the surface small while providing enterprise-level FHIR server management. The backend normalizes/sanitizes data into FHIR Patient resources; the frontend provides a modern SPA experience with advanced server management capabilities.

## Features

### Patient Management
- **List Patients**: View all patients with pagination (15 per page)
- **Create Patient**: Add new patients with comprehensive validation
- **Update Patient**: Edit existing patient information (partial updates supported)
- **Search Patients**: Multiple search methods with advanced filtering
- **Sort Patients**: Sort by last updated timestamp (newest/oldest first)

### Search & Sort Capabilities
- **Name Search**: Partial matching on patient names
- **Phone Search**: Search by phone number
- **Identifier Search**: Exact match by patient identifier
- **Combined Search**: Use multiple search criteria simultaneously
- **Sort Options**: Sort by last updated (ascending/descending)
- **Real-time Sorting**: Instant sorting without page reload

### FHIR Server Management
- **Dynamic Server Selection**: Switch between different FHIR servers on-the-fly
- **URL Persistence**: Save and reuse previously used FHIR server URLs
- **Blank by Default**: Starts with no server selected for security
- **Auto-reload**: Automatically loads patients when server URL changes
- **Visual Feedback**: Orange border indicator during URL processing
- **Multi-server Support**: Work with multiple FHIR servers seamlessly

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
- **Local Storage**: Persistent FHIR server URL management
- **Debounced Input**: Smart input handling to prevent excessive API calls

### Configuration Options
- **Environment Variables**: FHIR_BASE_URL configuration (fallback only)
- **Dynamic Server Selection**: Real-time FHIR server URL switching
- **Pagination Control**: Configurable result limits (15 per page)
- **Sort Parameters**: Flexible sorting options via FHIR parameters
- **URL Management**: Automatic saving and retrieval of server URLs

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

## API Design

### Core Endpoints
- `GET /patients`: Returns an array of simplified patients `{ id, identifier, given, family, gender, birthDate, phone, lastUpdated }` built from FHIR `Patient` resources
- `POST /patients`: Accepts `{ given, family, gender, birthDate, phone }`, validates, and creates FHIR Patient
- `PUT /patients/{id}`: Partial updates; sanitizes name fields and phone
- `GET /patients/search`: Advanced search with multiple parameters

### Query Parameters
- `fhir_server_url`: Dynamic FHIR server URL (optional, falls back to environment variable)
- `sort`: Sort parameter (e.g., `-_lastUpdated` for newest first, `_lastUpdated` for oldest first)
- `name`: Search by patient name (partial matching)
- `phone`: Search by phone number
- `identifier`: Search by exact identifier match
- `_count`: Limit results (default: 15)

### FHIR Integration
- All endpoints support dynamic FHIR server switching via `fhir_server_url` parameter
- Automatic FHIR resource validation and error handling
- Real-time sorting and filtering using FHIR search parameters

## FHIR Server Management Workflow

### Getting Started
1. **Launch the app**: The FHIR server URL field starts blank for security
2. **Enter a server URL**: Type a FHIR server URL in the input field
3. **Auto-save**: The URL is automatically saved to localStorage after 1 second
4. **Auto-load**: Patients are automatically loaded from the new server
5. **Reuse**: Previously used URLs appear in the dropdown for quick selection

### Server Switching
- **Select from dropdown**: Choose a previously used FHIR server
- **Enter new URL**: Type a new FHIR server URL in the input field
- **Visual feedback**: Orange border indicates processing
- **Instant switching**: All operations (list, create, update, search) use the selected server

### Security Features
- **Blank by default**: No server is pre-selected on page load
- **Reset on refresh**: Returns to blank state when page is refreshed
- **URL validation**: Input field validates URL format
- **Local storage**: URLs are stored locally, not transmitted to external servers

## Technical Implementation

### Frontend Architecture
- **Vanilla JavaScript**: No frameworks, pure ES6+ JavaScript
- **Local Storage API**: Persistent FHIR server URL management
- **Debounced Input**: Prevents excessive API calls during typing
- **Event-driven**: Real-time updates based on user interactions

### Backend Architecture
- **FastAPI**: Modern Python web framework with automatic API documentation
- **Async/Await**: Non-blocking HTTP requests to FHIR servers
- **Pydantic Models**: Type-safe data validation and serialization
- **FHIR R4 Compliance**: Full compatibility with FHIR R4 specification

### FHIR Resource Handling
- **Patient Resources**: Complete FHIR Patient resource mapping
- **Bundle Processing**: Handles FHIR Bundle responses for search operations
- **Meta Data**: Extracts and displays last updated timestamps
- **Error Handling**: Comprehensive FHIR server error management

## Notes
- No local database is used. All patient operations are relayed to FHIR servers.
- We intentionally use a minimal FHIR Patient subset for MVP clarity while maintaining full FHIR compliance.
- The app supports any FHIR R4-compliant server, making it highly interoperable.
