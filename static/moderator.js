/* AccessRoute moderation client. No secret is persisted or embedded in the page. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const closureTypes = new Set(['blocked_pavement', 'construction']);
  let adminKey = '';
  let reports = [];
  let selected = null;
  let candidates = [];
  let map = null;
  let markerLayer = null;
  let candidateLayer = null;

  if (typeof L !== 'undefined') {
    map = L.map('map').setView([53.4808, -2.2426], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors', maxZoom: 19
    }).addTo(map);
    markerLayer = L.featureGroup().addTo(map);
    candidateLayer = L.layerGroup().addTo(map);
  } else {
    $('map').textContent = 'Map unavailable. The report list and review controls can still be used.';
  }

  async function api(url, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set('X-Admin-Key', adminKey);
    if (options.body) headers.set('Content-Type', 'application/json');
    const response = await fetch(url, { ...options, headers, cache: 'no-store' });
    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try { detail = (await response.json()).detail || detail; } catch (_) {}
      throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    return response.json();
  }

  function clearChildren(element) { element.replaceChildren(); }
  function addText(parent, tag, content) {
    const element = document.createElement(tag);
    element.textContent = content;
    parent.appendChild(element);
    return element;
  }
  function formatType(type) { return String(type).replaceAll('_', ' '); }

  function drawReportMarkers() {
    if (!map) return;
    markerLayer.clearLayers();
    candidateLayer.clearLayers();
    for (const report of reports) {
      const lat = Number(report.latitude);
      const lon = Number(report.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
      const marker = L.circleMarker([lat, lon], {
        radius: 8, color: '#145fbb', weight: 2, fillOpacity: 0.75
      }).addTo(markerLayer);
      const label = document.createElement('span');
      label.textContent = `#${report.id}: ${formatType(report.report_type)}`;
      marker.bindPopup(label);
      marker.on('click', () => selectReport(report));
    }
    if (markerLayer.getLayers().length) {
      map.fitBounds(markerLayer.getBounds().pad(0.15), { maxZoom: 15 });
    }
  }

  function renderReports() {
    const root = $('reportList');
    clearChildren(root);
    if (!reports.length) { addText(root, 'p', 'No reports match this status.'); return; }
    for (const report of reports) {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'item' + (selected && selected.id === report.id ? ' selected' : '');
      item.setAttribute('aria-label', `Review report ${report.id}`);
      addText(item, 'strong', `#${report.id} · ${formatType(report.report_type)}`);
      addText(item, 'div', report.description);
      addText(item, 'small', `${report.status} · ${new Date(report.created_at).toLocaleString()}`);
      item.addEventListener('click', () => selectReport(report));
      root.appendChild(item);
    }
  }

  async function loadReports() {
    adminKey = $('adminKey').value.trim();
    if (!adminKey) { $('status').textContent = 'Enter your moderator key first.'; return; }
    $('status').textContent = 'Loading reports...';
    selected = null;
    $('reviewForm').hidden = true;
    $('reportDetail').textContent = 'Select a report to review it.';
    try {
      const status = $('statusFilter').value;
      const data = await api(`/barriers/moderation/reports?status=${encodeURIComponent(status)}&limit=100`);
      reports = data.reports;
      $('status').textContent = `${reports.length} ${status} report(s) loaded.`;
      renderReports();
      drawReportMarkers();
    } catch (error) {
      reports = [];
      renderReports();
      drawReportMarkers();
      $('status').textContent = `Could not load reports: ${error.message}`;
    }
  }

  function renderCandidates() {
    const select = $('candidateSelect');
    const list = $('candidateList');
    clearChildren(select);
    clearChildren(list);
    if (candidateLayer) candidateLayer.clearLayers();
    const blank = document.createElement('option');
    blank.value = '';
    blank.textContent = 'No segment selected';
    select.appendChild(blank);
    for (const edge of candidates) {
      const option = document.createElement('option');
      option.value = String(edge.edge_id);
      option.textContent = `Edge #${edge.edge_id} · ${edge.distance_m}m away`;
      select.appendChild(option);
      addText(list, 'div', `#${edge.edge_id}: ${edge.source} → ${edge.target}`);
      if (candidateLayer && [edge.source_latitude, edge.source_longitude,
        edge.target_latitude, edge.target_longitude].every(v => Number.isFinite(Number(v)))) {
        const line = L.polyline([
          [Number(edge.source_latitude), Number(edge.source_longitude)],
          [Number(edge.target_latitude), Number(edge.target_longitude)]
        ], { color: '#e87516', weight: 5, opacity: 0.7 }).addTo(candidateLayer);
        const label = document.createElement('span');
        label.textContent = `Candidate edge #${edge.edge_id}`;
        line.bindPopup(label);
      }
    }
  }

  async function selectReport(report) {
    selected = report;
    candidates = [];
    $('reviewStatus').textContent = '';
    $('reportDetail').textContent = `#${report.id} — ${formatType(report.report_type)}\n\n${report.description}\n\nStatus: ${report.status}\nLocation: ${report.latitude}, ${report.longitude}`;
    $('reviewForm').hidden = report.status !== 'pending';
    $('candidateSelect').disabled = !closureTypes.has(report.report_type);
    renderReports();
    renderCandidates();
    if (map) map.setView([Number(report.latitude), Number(report.longitude)], 17);
    if (report.status !== 'pending') return;
    if (!closureTypes.has(report.report_type)) {
      $('candidateList').textContent = 'Informational report: no routing edge will be closed.';
      return;
    }
    $('candidateList').textContent = 'Finding nearby street segments...';
    try {
      const result = await api(`/barriers/reports/${report.id}/candidates`);
      if (!selected || selected.id !== report.id) return;
      candidates = result.candidates;
      renderCandidates();
      if (!candidates.length) $('candidateList').textContent = 'No nearby segments within 25m. Do not verify a closure without one.';
    } catch (error) {
      $('candidateList').textContent = `Candidate lookup failed: ${error.message}`;
    }
  }

  async function submitReview(status) {
    if (!selected || selected.status !== 'pending') return;
    const isClosure = closureTypes.has(selected.report_type);
    const selectedEdge = $('candidateSelect').value;
    const hours = Number($('durationHours').value);
    if (status === 'verified' && isClosure && !selectedEdge) {
      $('reviewStatus').textContent = 'Select a nearby street segment before approving.';
      return;
    }
    if (status === 'verified' && (!Number.isInteger(hours) || hours < 1 || hours > 720)) {
      $('reviewStatus').textContent = 'Closure duration must be 1–720 hours.';
      return;
    }
    const payload = { status, valid_hours: hours || 168,
      edge_id: status === 'verified' && isClosure ? Number(selectedEdge) : null };
    $('approve').disabled = true;
    $('reject').disabled = true;
    $('reviewStatus').textContent = 'Saving moderation decision...';
    try {
      await api(`/barriers/reports/${selected.id}/review`, {
        method: 'POST', body: JSON.stringify(payload)
      });
      $('reviewStatus').textContent = `Report #${selected.id} ${status}.`;
      await loadReports();
    } catch (error) {
      $('reviewStatus').textContent = `Review failed: ${error.message}`;
    } finally {
      $('approve').disabled = false;
      $('reject').disabled = false;
    }
  }

  $('loadReports').addEventListener('click', loadReports);
  $('statusFilter').addEventListener('change', () => { if (adminKey) loadReports(); });
  $('approve').addEventListener('click', () => submitReview('verified'));
  async function loadAudit() {
    adminKey = $('adminKey').value.trim();
    if (!adminKey) {
      $('auditStatus').textContent = 'Enter your moderator key first.';
      return;
    }
    $('auditStatus').textContent = 'Loading recent moderation decisions...';
    const root = $('auditList');
    clearChildren(root);
    try {
      const result = await api('/barriers/moderation/audit?limit=30&offset=0');
      if (!result.events.length) {
        $('auditStatus').textContent = 'No moderation decisions recorded yet.';
        return;
      }
      for (const event of result.events) {
        const entry = document.createElement('p');
        const edge = event.edge_id === null ? 'informational' : `edge #${event.edge_id}`;
        entry.textContent = `Report #${event.report_id}: ${event.decision} (${edge}) · ` +
          new Date(event.recorded_at).toLocaleString();
        root.appendChild(entry);
      }
      $('auditStatus').textContent = `${result.events.length} recent decision(s) loaded.`;
    } catch (error) {
      $('auditStatus').textContent = `Could not load audit history: ${error.message}`;
    }
  }

  $('loadAudit').addEventListener('click', loadAudit);
  $('reject').addEventListener('click', () => submitReview('rejected'));
})();
