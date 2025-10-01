const API_BASE = '';
// Requests no longer use an artificial timeout

function showAlert(message, type = 'info') {
  const wrap = document.getElementById('alerts');
  if (!wrap) return;
  const el = document.createElement('div');
  el.className = `alert ${type}`;
  el.textContent = message;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

function setLoading(isLoading) {
  const overlay = document.getElementById('loadingOverlay');
  if (!overlay) return;
  overlay.classList.toggle('hidden', !isLoading);
  overlay.classList.toggle('loader-overlay', isLoading);
}

async function fetchWithTimeout(resource, options = {}) { return fetch(resource, options); }

async function loadPatients() {
  const tbody = document.getElementById('patientsTbody');
  tbody.innerHTML = '<tr><td colspan="7" class="table-loading">Loading…</td></tr>';
  try {
    const fhirServerUrl = document.getElementById('fhirServerUrl').value.trim();
    const url = fhirServerUrl ? `${API_BASE}/patients?fhir_server_url=${encodeURIComponent(fhirServerUrl)}` : `${API_BASE}/patients`;
    const res = await fetchWithTimeout(url);
    const data = await res.json();
    renderPatients(data);
  } catch (e) {
    const msg = 'FHIR server unavailable, try later.';
    showAlert(msg, 'error');
    tbody.innerHTML = `<tr><td colspan="7">${msg}</td></tr>`;
  }
}

function renderPatients(patients) {
  const tbody = document.getElementById('patientsTbody');
  if (!Array.isArray(patients) || patients.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7">No patient found.</td></tr>';
    showAlert('No patient found.', 'info');
    return;
  }
  tbody.innerHTML = '';
  for (const p of patients) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${escapeHtml(p.identifier || '')}</td>
      <td>${escapeHtml(p.given || '')}</td>
      <td>${escapeHtml(p.family || '')}</td>
      <td>${escapeHtml(p.gender || '')}</td>
      <td>${escapeHtml(p.birthDate || '')}</td>
      <td>${escapeHtml(p.phone || '')}</td>
      <td>
        <button class="secondary" data-id="${p.id}" onclick="prefillForm('${p.id}', '${encodeURIComponent(p.identifier || '')}', '${encodeURIComponent(p.given || '')}', '${encodeURIComponent(p.family || '')}', '${encodeURIComponent(p.gender || '')}', '${encodeURIComponent(p.birthDate || '')}', '${encodeURIComponent(p.phone || '')}')">Edit</button>
      </td>
    `;
    tbody.appendChild(tr);
  }
}

function escapeHtml(str) {
  return String(str).replace(/[&<>'"]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','\'':'&#39;','"':'&quot;'}[s]));
}

function prefillForm(id, identifier, given, family, gender, birthDate, phone) {
  document.getElementById('patientId').value = id;
  document.getElementById('given').value = decodeURIComponent(given || '');
  document.getElementById('family').value = decodeURIComponent(family || '');
  document.getElementById('gender').value = decodeURIComponent(gender || 'unknown') || 'unknown';
  document.getElementById('birthDate').value = decodeURIComponent(birthDate || '');
  document.getElementById('phone').value = decodeURIComponent(phone || '');
  document.getElementById('formMsg').textContent = `Editing patient ${id}`;
}

document.getElementById('clearBtn').addEventListener('click', () => {
  document.getElementById('patientForm').reset();
  document.getElementById('patientId').value = '';
  document.getElementById('formMsg').textContent = '';
});

document.getElementById('patientForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = document.getElementById('patientId').value.trim();
  const given = document.getElementById('given').value.trim();
  const family = document.getElementById('family').value.trim();
  const gender = document.getElementById('gender').value;
  const birthDate = document.getElementById('birthDate').value;
  const phoneStr = document.getElementById('phone').value.trim();
  const phone = phoneStr ? Number(phoneStr) : NaN;
  const msg = document.getElementById('formMsg');
  msg.textContent = '';

  if (!given || !family || !gender || !birthDate) {
    msg.textContent = 'First name, last name, gender and birth date are required';
    msg.classList.add('error');
    return;
  }

  // Phone required
  if (!phoneStr || Number.isNaN(phone)) {
    msg.textContent = 'Phone number is required.';
    msg.classList.add('error');
    return;
  }

  // DOB cannot be in the future
  const today = new Date();
  const dob = new Date(birthDate);
  if (dob > new Date(today.getFullYear(), today.getMonth(), today.getDate())) {
    msg.textContent = 'Date of Birth cannot be in the future.';
    msg.classList.add('error');
    return;
  }

  try {
    setLoading(true);
    const fhirServerUrl = document.getElementById('fhirServerUrl').value.trim();
    const serverUrlParam = fhirServerUrl ? `?fhir_server_url=${encodeURIComponent(fhirServerUrl)}` : '';
    
    if (id) {
      const r = await fetchWithTimeout(`${API_BASE}/patients/${encodeURIComponent(id)}${serverUrlParam}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ given, family, gender, birthDate, phone })
      });
      const data = await r.json();
      msg.textContent = `Updated: ${data.given || ''} ${data.family || ''}`.trim();
      showAlert('Patient updated successfully.', 'success');
    } else {
      const r = await fetchWithTimeout(`${API_BASE}/patients${serverUrlParam}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ given, family, gender, birthDate, phone })
      });
      const data = await r.json();
      const identifier = data.identifier || data.id;
      msg.textContent = `Created: Patient #${identifier}`;
      showAlert('Patient created successfully.', 'success');
    }
    msg.classList.remove('error');
    await loadPatients();
    (document.getElementById('patientForm')).reset();
    document.getElementById('patientId').value = '';
  } catch (err) {
    const errMsg = 'Patient could not be created. Please try again.';
    msg.textContent = errMsg;
    msg.classList.add('error');
    showAlert(errMsg, 'error');
  } finally {
    setLoading(false);
  }
});

document.getElementById('searchBtn').addEventListener('click', async () => {
  const ident = document.getElementById('searchIdentifier').value.trim();
  const name = document.getElementById('searchName').value.trim();
  const phone = document.getElementById('searchPhone').value.trim();
  const fhirServerUrl = document.getElementById('fhirServerUrl').value.trim();
  const params = new URLSearchParams();
  if (ident) params.append('identifier', ident);
  if (name) params.append('name', name);
  if (phone) params.append('phone', phone);
  if (fhirServerUrl) params.append('fhir_server_url', fhirServerUrl);
  const tbody = document.getElementById('patientsTbody');
  tbody.innerHTML = '<tr><td colspan="7" class="table-loading">Searching…</td></tr>';
  try {
    setLoading(true);
    const r = await fetchWithTimeout(`${API_BASE}/patients/search?${params.toString()}`);
    const data = await r.json();
    if ((params.get('phone') || '') && (!Array.isArray(data) || data.length === 0)) {
      tbody.innerHTML = '<tr><td colspan="7">No patient found with this phone number.</td></tr>';
      showAlert('No patient found with this phone number.', 'info');
      return;
    }
    renderPatients(data);
  } catch (e) {
    const msg = (e.name === 'AbortError') ? 'Request taking too long. Please retry.' : 'FHIR server unavailable, try later.';
    showAlert(msg, 'error');
    tbody.innerHTML = `<tr><td colspan="7">${msg}</td></tr>`;
  } finally {
    setLoading(false);
  }
});

document.getElementById('resetBtn').addEventListener('click', () => {
  document.getElementById('searchIdentifier').value = '';
  document.getElementById('searchName').value = '';
  document.getElementById('searchPhone').value = '';
  loadPatients();
});

// Auto-reload patients when FHIR server URL changes
document.getElementById('fhirServerUrl').addEventListener('input', (e) => {
  // Debounce the input to avoid too many requests
  clearTimeout(window.fhirUrlTimeout);
  
  // Show a visual indicator that we're waiting for input to settle
  const input = e.target;
  input.style.borderColor = '#ffa500'; // Orange border to indicate processing
  
  window.fhirUrlTimeout = setTimeout(() => {
    if (e.target.value.trim()) {
      showAlert('Loading patients from new FHIR server...', 'info');
      loadPatients();
    }
    input.style.borderColor = ''; // Reset border color
  }, 1000); // Wait 1 second after user stops typing
});

