/**
 * admin_v3.js — JavaScript for the v3 admin panel sections:
 *   Access Requests, Test Sessions, AI Insights, Activity Log
 */

/* ─── Helpers ─────────────────────────────────────────────── */
function statusBadge(s) {
    const map = {
        pending:      'badge-warning',
        approved:     'badge-success',
        rejected:     'badge-danger',
        running:      'badge-info',
        completed:    'badge-success',
        aborted:      'badge-danger',
        setup:        'badge-secondary',
        passed:       'badge-success',
        failed:       'badge-danger',
        inconclusive: 'badge-warning',
        info:         'badge-info',
        warning:      'badge-warning',
        critical:     'badge-danger',
    };
    return `<span class="status-badge ${map[s] || 'badge-secondary'}">${s}</span>`;
}

function fmtDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('en-IN', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' });
}

function fmtDuration(sec) {
    if (!sec) return '—';
    const m = Math.floor(sec / 60), s = sec % 60;
    return m ? `${m}m ${s}s` : `${s}s`;
}

function showToastV3(msg, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

/* ─── Nav badge updater ────────────────────────────────────── */
async function updateV3NavBadges() {
    try {
        // Pending access requests badge
        const r = await fetch('/api/admin/access-requests?status=pending&per_page=1');
        const d = await r.json();
        const pendingCount = d.counts?.pending || 0;
        const badge = document.getElementById('pendingBadge');
        if (badge) {
            badge.textContent = pendingCount > 0 ? pendingCount : '';
            badge.style.display = pendingCount > 0 ? 'inline-block' : 'none';
        }

        // Unread AI insights
        const r2 = await fetch('/api/admin/ai-insights?unread=1');
        const d2 = await r2.json();
        const unread = d2.unread_count || 0;
        const iBadge = document.getElementById('insightBadge');
        if (iBadge) {
            iBadge.textContent = unread > 0 ? unread : '';
            iBadge.style.display = unread > 0 ? 'inline-block' : 'none';
        }
    } catch (e) { /* silent */ }
}

// Run on load and poll every 60s
updateV3NavBadges();
setInterval(updateV3NavBadges, 60000);

// Hook into the existing section switch to lazy-load v3 sections
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#adminNav a[data-section]').forEach(link => {
        link.addEventListener('click', () => {
            const sec = link.dataset.section;
            if (sec === 'access-requests') loadAccessRequests();
            if (sec === 'test-sessions')   loadTestSessions();
            if (sec === 'ai-insights')     loadAIInsights();
            if (sec === 'activity-log')    loadActivityLog();
        });
    });

    // Modal close buttons
    document.getElementById('closeAccessModal')?.addEventListener('click',  closeAccessModal);
    document.getElementById('cancelAccessModal')?.addEventListener('click', closeAccessModal);
    document.getElementById('confirmAccessBtn')?.addEventListener('click',  confirmAccessAction);

    // Close on backdrop click
    document.getElementById('accessApproveModal')?.addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeAccessModal();
    });
});

/* ═══════════════════════════════════════════════════════════
   ACCESS REQUESTS
═══════════════════════════════════════════════════════════ */
let _accessAction = null;  // 'approve' | 'reject'

async function loadAccessRequests(page = 1) {
    const status = document.getElementById('accessStatusFilter')?.value || '';
    const url    = `/api/admin/access-requests?page=${page}&per_page=20${status ? '&status=' + status : ''}`;
    const data   = await (await fetch(url)).json();

    // Update count badges
    document.getElementById('accessPendingCount').textContent  = data.counts?.pending  ?? '—';
    document.getElementById('accessApprovedCount').textContent = data.counts?.approved ?? '—';
    document.getElementById('accessRejectedCount').textContent = data.counts?.rejected ?? '—';

    // Update nav badge
    const badge = document.getElementById('pendingBadge');
    if (badge) {
        const p = data.counts?.pending || 0;
        badge.textContent    = p || '';
        badge.style.display  = p ? 'inline-block' : 'none';
    }

    const tbody = document.getElementById('accessRequestsTbody');
    tbody.innerHTML = data.requests.length
        ? data.requests.map(r => `
            <tr>
                <td>${r.id}</td>
                <td><strong>${r.full_name}</strong></td>
                <td style="font-size:12px">${r.email}</td>
                <td>${r.company_name || '—'}</td>
                <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px" title="${(r.purpose||'').replace(/"/g,'&quot;')}">${r.purpose || '—'}</td>
                <td>${statusBadge(r.status)}</td>
                <td style="font-size:12px">${fmtDate(r.created_at)}</td>
                <td>
                    ${r.status === 'pending' ? `
                        <button class="btn btn-xs btn-primary access-action-btn"
                            data-id="${r.id}" data-action="approve"
                            data-name="${(r.full_name||'').replace(/"/g,'&quot;')}"
                            data-email="${r.email}">
                            <i class="fas fa-check"></i> Approve
                        </button>
                        <button class="btn btn-xs btn-danger access-action-btn"
                            data-id="${r.id}" data-action="reject"
                            data-name="${(r.full_name||'').replace(/"/g,'&quot;')}"
                            data-email="${r.email}">
                            <i class="fas fa-times"></i> Reject
                        </button>` : ''}
                    ${r.status === 'approved' ? `
                        <button class="btn btn-xs btn-outline-dark revoke-btn" data-id="${r.id}">
                            <i class="fas fa-ban"></i> Revoke
                        </button>
                        ${r.has_token ? `<span style="font-size:11px;color:var(--success-color)"><i class="fas fa-key"></i> Token Active</span>` : ''}
                    ` : ''}
                </td>
            </tr>`).join('')
        : '<tr><td colspan="8" class="text-center">No requests found</td></tr>';

    // Delegate click events — avoids inline onclick escaping bugs
    tbody.querySelectorAll('.access-action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            openAccessModal(
                btn.dataset.id,
                btn.dataset.action,
                btn.dataset.name,
                btn.dataset.email
            );
        });
    });
    tbody.querySelectorAll('.revoke-btn').forEach(btn => {
        btn.addEventListener('click', () => revokeToken(btn.dataset.id));
    });

    renderPagination('accessPagination', data.pages, page, loadAccessRequests);
}

function openAccessModal(id, action, name, email) {
    _accessAction = action;
    document.getElementById('accessReqId').value = id;
    document.getElementById('accessModalTitle').textContent = action === 'approve'
        ? `Approve Access — ${name}` : `Reject Request — ${name}`;
    document.getElementById('accessModalContent').innerHTML =
        `<p style="margin-bottom:12px;font-size:13px;color:var(--text-muted)"><i class="fas fa-envelope"></i> ${email}</p>`;
    document.getElementById('approveFields').style.display = action === 'approve' ? '' : 'none';
    document.getElementById('rejectFields').style.display  = action === 'reject'  ? '' : 'none';
    const confirmBtn = document.getElementById('confirmAccessBtn');
    confirmBtn.className   = action === 'approve' ? 'btn btn-primary' : 'btn btn-danger';
    confirmBtn.textContent = action === 'approve' ? 'Approve & Generate Token' : 'Reject Request';
    document.getElementById('accessApproveModal').classList.add('open');
}

function closeAccessModal() {
    document.getElementById('accessApproveModal').classList.remove('open');
    _accessAction = null;
}

async function confirmAccessAction() {
    const id = document.getElementById('accessReqId').value;
    if (_accessAction === 'approve') {
        const body = {
            approved_by:  document.getElementById('accessApprovedBy').value || 'Admin',
            expire_days:  parseInt(document.getElementById('accessExpireDays').value) || 30,
        };
        const res  = await fetch(`/api/admin/access-requests/${id}/approve`, {
            method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok) {
            showToastV3(`✅ Approved. Token: ${data.access_token}`, 'success');
            // Copy token to clipboard
            navigator.clipboard?.writeText(data.access_token);
            alert(`Token copied to clipboard:\n${data.access_token}\n\nExpires: ${new Date(data.expires_at).toLocaleString()}`);
        } else {
            showToastV3(data.error || 'Failed', 'error');
        }
    } else {
        const body = {
            rejected_by:     'Admin',
            rejection_note:  document.getElementById('accessRejectionNote').value,
        };
        const res = await fetch(`/api/admin/access-requests/${id}/reject`, {
            method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
        });
        if (res.ok) showToastV3('Request rejected', 'success');
        else showToastV3('Failed to reject', 'error');
    }
    closeAccessModal();
    loadAccessRequests();
}

async function revokeToken(id) {
    if (!confirm('Revoke this access token? The user will immediately lose access.')) return;
    const res = await fetch(`/api/admin/access-requests/${id}/revoke`, { method:'PUT' });
    if (res.ok) { showToastV3('Token revoked', 'success'); loadAccessRequests(); }
    else showToastV3('Revoke failed', 'error');
}

/* ═══════════════════════════════════════════════════════════
   TEST SESSIONS
═══════════════════════════════════════════════════════════ */
async function loadTestSessions(page = 1) {
    const status = document.getElementById('testSessionStatus')?.value || '';
    const result = document.getElementById('testSessionResult')?.value || '';
    const params = new URLSearchParams({ page, per_page: 20 });
    if (status) params.set('status', status);
    if (result) params.set('result', result);

    const data  = await (await fetch(`/api/admin/test-sessions?${params}`)).json();
    const tbody = document.getElementById('testSessionsTbody');

    tbody.innerHTML = data.sessions.length
        ? data.sessions.map(s => `
            <tr>
                <td style="font-family:monospace;font-size:12px">${s.session_code}</td>
                <td>${s.valve_id || '—'}</td>
                <td>${s.test_type}</td>
                <td>${s.operator_name}</td>
                <td>${statusBadge(s.status)}</td>
                <td>${s.result ? statusBadge(s.result) : '—'}</td>
                <td>${fmtDuration(s.duration_seconds)}</td>
                <td style="font-size:12px">${fmtDate(s.created_at)}</td>
                <td>
                    <button class="btn btn-xs btn-outline-dark"
                        title="Download PDF Report"
                        onclick="generateTestSessionPDF(${s.id},'${s.session_code}',this)"
                        style="color:#f59e0b;border-color:#f59e0b">
                        <i class="fas fa-file-pdf"></i> PDF
                    </button>
                </td>
            </tr>`).join('')
        : '<tr><td colspan="9" class="text-center">No sessions found</td></tr>';

    renderPagination('testSessionsPagination', data.pages, page, loadTestSessions);
}

/* ─ Test Session PDF Report (client-side via jsPDF) ────────── */
async function generateTestSessionPDF(sessionId, code, btn) {
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    try {
        // Fetch session data from the testing sub-app
        const sessRes = await fetch(`/testing/api/tests/sessions/${sessionId}`);
        const readRes = await fetch(`/testing/api/tests/sessions/${sessionId}/readings?limit=1000`);
        if (!sessRes.ok) { alert('Could not load session data (check auth).'); return; }
        const sess     = await sessRes.json();
        const readData = readRes.ok ? await readRes.json() : { readings: [] };
        const readings = readData.readings || [];

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        const W   = doc.internal.pageSize.getWidth();
        const H   = doc.internal.pageSize.getHeight();

        // Header
        doc.setFillColor(10, 22, 40); doc.rect(0, 0, W, 32, 'F');
        doc.setTextColor(0, 200, 255); doc.setFontSize(18); doc.setFont('helvetica','bold');
        doc.text('TESTINY', 14, 13);
        doc.setTextColor(200, 220, 255); doc.setFontSize(9); doc.setFont('helvetica','normal');
        doc.text('Industrial Valve Testing — Admin Report', 14, 19);
        doc.text(`Generated: ${new Date().toLocaleString()}`, W - 14, 27, { align: 'right' });

        const result = (sess.result || 'unknown').toUpperCase();
        const rColor = result === 'PASSED' ? [0,230,118] : result === 'FAILED' ? [255,23,68] : [255,171,0];
        doc.setFillColor(...rColor);
        doc.roundedRect(W - 42, 6, 30, 10, 3, 3, 'F');
        doc.setTextColor(0,0,0); doc.setFontSize(9); doc.setFont('helvetica','bold');
        doc.text(result, W - 27, 13, { align: 'center' });

        let y = 40;
        const fmt = v => (v == null || v === '') ? '—' : String(v);
        const dur = sess.duration_seconds
            ? `${Math.floor(sess.duration_seconds/60)}m ${sess.duration_seconds%60}s` : '—';

        doc.setFontSize(11); doc.setFont('helvetica','bold'); doc.setTextColor(30,60,100);
        doc.text('Session Information', 14, y); y += 6;
        doc.autoTable({
            startY: y, head: [],
            body: [
                ['Session Code', fmt(sess.session_code),    'Operator',   fmt(sess.operator_name)],
                ['Valve ID',     fmt(sess.valve_id),        'Valve Type', fmt(sess.valve_type)],
                ['Test Type',    fmt(sess.test_type),       'Medium',     fmt(sess.medium)],
                ['Status',       fmt(sess.status),          'Result',     result],
                ['Started',      sess.started_at ? new Date(sess.started_at).toLocaleString() : '—',
                 'Ended',        sess.ended_at   ? new Date(sess.ended_at).toLocaleString()   : '—'],
                ['Duration',     dur, 'Job #', fmt(sess.job_number)],
            ],
            columnStyles: {
                0: { fontStyle:'bold', cellWidth:35, fillColor:[240,245,255], textColor:[30,60,120] },
                1: { cellWidth:55 },
                2: { fontStyle:'bold', cellWidth:35, fillColor:[240,245,255], textColor:[30,60,120] },
                3: { cellWidth:55 },
            },
            styles: { fontSize:9, cellPadding:3, lineColor:[220,230,245], lineWidth:.3 },
            theme: 'grid',
        });
        y = doc.lastAutoTable.finalY + 10;

        if (readings.length) {
            const vals = k => readings.map(r => parseFloat(r[k])).filter(v => !isNaN(v));
            const stat = arr => arr.length
                ? { min: Math.min(...arr).toFixed(2), max: Math.max(...arr).toFixed(2),
                    avg: (arr.reduce((a,b) => a+b,0)/arr.length).toFixed(2) }
                : { min:'—', max:'—', avg:'—' };

            doc.setFontSize(11); doc.setFont('helvetica','bold'); doc.setTextColor(30,60,100);
            doc.text('Measurement Summary', 14, y); y += 6;
            doc.autoTable({
                startY: y,
                head:  [['Parameter','Unit','Min','Max','Average','Count']],
                body:  [
                    ['Pressure',    'bar',    ...Object.values(stat(vals('pressure_bar'))),   vals('pressure_bar').length],
                    ['Temperature', '°C',     ...Object.values(stat(vals('temperature_c'))),  vals('temperature_c').length],
                    ['Flow Rate',   'L/min',  ...Object.values(stat(vals('flow_rate_lpm'))),  vals('flow_rate_lpm').length],
                    ['Leakage',     'mL/min', ...Object.values(stat(vals('leakage_ml_min'))), vals('leakage_ml_min').length],
                ],
                headStyles: { fillColor:[10,22,40], textColor:[0,200,255], fontSize:9 },
                styles: { fontSize:9, cellPadding:3 },
                alternateRowStyles: { fillColor:[245,248,255] },
                theme: 'striped',
            });
            y = doc.lastAutoTable.finalY + 10;

            doc.setFontSize(11); doc.setFont('helvetica','bold'); doc.setTextColor(30,60,100);
            doc.text(`Sensor Readings (${Math.min(readings.length,200)} of ${readings.length})`, 14, y); y += 4;
            doc.autoTable({
                startY: y,
                head: [['Time','Pressure (bar)','Temp (°C)','Flow (L/min)','Leakage (mL/min)','Alert']],
                body: readings.slice(0,200).map(r => [
                    r.recorded_at ? new Date(r.recorded_at).toLocaleTimeString() : '—',
                    r.pressure_bar   != null ? Number(r.pressure_bar).toFixed(2)   : '—',
                    r.temperature_c  != null ? Number(r.temperature_c).toFixed(2)  : '—',
                    r.flow_rate_lpm  != null ? Number(r.flow_rate_lpm).toFixed(3)  : '—',
                    r.leakage_ml_min != null ? Number(r.leakage_ml_min).toFixed(3) : '—',
                    r.pressure_alert || 'ok',
                ]),
                headStyles: { fillColor:[10,22,40], textColor:[0,200,255], fontSize:8 },
                styles: { fontSize:7.5, cellPadding:2 },
                alternateRowStyles: { fillColor:[247,250,255] },
                didParseCell: d => {
                    if (d.section === 'body' && d.column.index === 5) {
                        const v = d.cell.text[0];
                        if (v === 'critical') { d.cell.styles.textColor=[200,0,0]; d.cell.styles.fontStyle='bold'; }
                        else if (v === 'warning') d.cell.styles.textColor=[180,100,0];
                        else d.cell.styles.textColor=[0,160,80];
                    }
                },
                theme: 'striped',
            });
        }

        // Footer on each page
        const pages = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pages; i++) {
            doc.setPage(i);
            doc.setDrawColor(0,200,255); doc.setLineWidth(.5);
            doc.line(14, H-12, W-14, H-12);
            doc.setFontSize(8); doc.setTextColor(120,150,180); doc.setFont('helvetica','normal');
            doc.text('Testiny — Admin Report — Confidential', 14, H-7);
            doc.text(`Page ${i} of ${pages}`, W-14, H-7, { align:'right' });
        }

        doc.save(`Testiny_Admin_${code}.pdf`);
    } catch (e) {
        alert('PDF generation failed: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
    }
}

/* ═══════════════════════════════════════════════════════════
   SALES — Add Enquiry Modal
═══════════════════════════════════════════════════════════ */
function openEnquiryModal() {
    // Reuse the existing sales modal if present, otherwise open inline modal
    const existingModal = document.getElementById('salesModal');
    if (existingModal) {
        existingModal.classList.add('open');
        return;
    }
    // Fallback: inline form modal
    let m = document.getElementById('_enquiryModal');
    if (!m) {
        m = document.createElement('div');
        m.id = '_enquiryModal';
        m.className = 'modal-overlay';
        m.innerHTML = `
        <div class="modal" style="max-width:500px">
            <div class="modal-header">
                <h3><i class="fas fa-handshake"></i> New Sales Enquiry</h3>
                <button class="modal-close" onclick="document.getElementById('_enquiryModal').classList.remove('open')"><i class="fas fa-times"></i></button>
            </div>
            <div class="modal-body">
                <div class="form-row">
                    <div class="form-group"><label>Contact Name *</label><input type="text" id="enqName" placeholder="Full name"></div>
                    <div class="form-group"><label>Company</label><input type="text" id="enqCompany" placeholder="Company name"></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Email</label><input type="email" id="enqEmail" placeholder="email@company.com"></div>
                    <div class="form-group"><label>Phone</label><input type="tel" id="enqPhone" placeholder="+91 9876543210"></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Product Interest</label><input type="text" id="enqProduct" placeholder="e.g., Ball Valve 2-inch"></div>
                    <div class="form-group"><label>Est. Value (&#8377;)</label><input type="number" id="enqValue" placeholder="0" min="0"></div>
                </div>
                <div class="form-group"><label>Status</label>
                    <select id="enqStatus">
                        <option value="new">New</option>
                        <option value="contacted">Contacted</option>
                        <option value="quotation">Quotation Sent</option>
                    </select>
                </div>
                <div class="form-group"><label>Notes</label><textarea id="enqNotes" rows="3" placeholder="Additional notes…"></textarea></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline-dark" onclick="document.getElementById('_enquiryModal').classList.remove('open')">Cancel</button>
                <button class="btn btn-primary" onclick="submitEnquiry()"><i class="fas fa-save"></i> Save Enquiry</button>
            </div>
        </div>`;
        document.body.appendChild(m);
        m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); });
    }
    m.classList.add('open');
}

async function submitEnquiry() {
    const name = document.getElementById('enqName')?.value.trim();
    if (!name) { alert('Contact name is required'); return; }
    const payload = {
        contact_name:    name,
        company_name:    document.getElementById('enqCompany')?.value.trim() || '',
        email:           document.getElementById('enqEmail')?.value.trim() || '',
        phone:           document.getElementById('enqPhone')?.value.trim() || '',
        product_interest:document.getElementById('enqProduct')?.value.trim() || '',
        estimated_value: parseFloat(document.getElementById('enqValue')?.value) || 0,
        status:          document.getElementById('enqStatus')?.value || 'new',
        notes:           document.getElementById('enqNotes')?.value.trim() || '',
    };
    try {
        const res = await fetch('/api/admin/enquiries', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            showToastV3('Enquiry saved!', 'success');
            document.getElementById('_enquiryModal').classList.remove('open');
            if (typeof loadSalesData === 'function') loadSalesData();
        } else {
            const d = await res.json();
            alert('Error: ' + (d.error || res.status));
        }
    } catch(e) { alert('Request failed: ' + e.message); }
}

/* ═══════════════════════════════════════════════════════════
   ASSEMBLY — Add Checklist Modal
═══════════════════════════════════════════════════════════ */
function openAssemblyModal() {
    const existingModal = document.getElementById('assemblyModal');
    if (existingModal) {
        // Reset for new entry
        document.getElementById('asmId')?.removeAttribute('value');
        const title = document.getElementById('assemblyModalTitle');
        if (title) title.textContent = 'New Assembly Checklist';
        existingModal.classList.add('open');
        return;
    }
    // Fallback inline modal
    let m = document.getElementById('_assemblyModal');
    if (!m) {
        m = document.createElement('div');
        m.id = '_assemblyModal';
        m.className = 'modal-overlay';
        m.innerHTML = `
        <div class="modal" style="max-width:500px">
            <div class="modal-header">
                <h3><i class="fas fa-screwdriver-wrench"></i> New Assembly Checklist</h3>
                <button class="modal-close" onclick="document.getElementById('_assemblyModal').classList.remove('open')"><i class="fas fa-times"></i></button>
            </div>
            <div class="modal-body">
                <div class="form-row">
                    <div class="form-group"><label>Order # *</label><input type="text" id="asmOrder" placeholder="e.g., ORD-2026-001"></div>
                    <div class="form-group"><label>Assigned To</label><input type="text" id="asmAssigned" placeholder="Technician name"></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Progress (0–100%)</label><input type="number" id="asmProgress" min="0" max="100" value="0"></div>
                    <div class="form-group"><label>Status</label>
                        <select id="asmStatus">
                            <option value="pending">Pending</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                        </select>
                    </div>
                </div>
                <div class="form-group"><label>Notes</label><textarea id="asmNotes" rows="3" placeholder="Assembly notes…"></textarea></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline-dark" onclick="document.getElementById('_assemblyModal').classList.remove('open')">Cancel</button>
                <button class="btn btn-primary" onclick="submitAssembly()"><i class="fas fa-save"></i> Save</button>
            </div>
        </div>`;
        document.body.appendChild(m);
        m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); });
    }
    m.classList.add('open');
}

async function submitAssembly() {
    const order = document.getElementById('asmOrder')?.value.trim();
    if (!order) { alert('Order # is required'); return; }
    const payload = {
        order_number:  order,
        assigned_to:   document.getElementById('asmAssigned')?.value.trim() || '',
        progress:      parseInt(document.getElementById('asmProgress')?.value) || 0,
        status:        document.getElementById('asmStatus')?.value || 'pending',
        notes:         document.getElementById('asmNotes')?.value.trim() || '',
    };
    try {
        const res = await fetch('/api/admin/assembly', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            showToastV3('Assembly checklist saved!', 'success');
            document.getElementById('_assemblyModal').classList.remove('open');
            if (typeof loadAssemblyData === 'function') loadAssemblyData();
        } else {
            const d = await res.json();
            alert('Error: ' + (d.error || res.status));
        }
    } catch(e) { alert('Request failed: ' + e.message); }
}

/* ═══════════════════════════════════════════════════════════
   AI INSIGHTS
═══════════════════════════════════════════════════════════ */
async function loadAIInsights() {
    // Ollama status check
    try {
        const sr   = await fetch('/api/admin/ai/status');
        const sd   = await sr.json();
        const isOn = sd.ollama === 'online';
        document.getElementById('insightsOllamaStatus').innerHTML = `
            <div class="alert alert-${isOn ? 'success' : 'warning'}" style="display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:8px;font-size:13px">
                <i class="fas fa-${isOn ? 'circle-check' : 'triangle-exclamation'}"></i>
                Ollama AI: <strong>${isOn ? 'Online' : 'Offline'}</strong>
                ${!isOn ? '— Start Ollama with <code>ollama serve</code> to generate insights.' : `(${sd.model})`}
            </div>`;
    } catch { /* silent */ }

    const data = await (await fetch('/api/admin/ai-insights')).json();
    const list = document.getElementById('insightsList');

    // Update nav badge
    const iBadge = document.getElementById('insightBadge');
    if (iBadge) {
        iBadge.textContent   = data.unread_count || '';
        iBadge.style.display = data.unread_count ? 'inline-block' : 'none';
    }

    if (!data.insights.length) {
        list.innerHTML = '<div class="card-box text-center" style="padding:2rem;color:var(--text-muted)"><i class="fas fa-microchip" style="font-size:2rem;margin-bottom:.5rem;display:block;opacity:.4"></i>No insights yet. Click <strong>Generate Insights</strong> to run AI analysis.</div>';
        return;
    }

    const colorMap = { info:'#0066ff', warning:'#ff9500', critical:'#ff3b30' };
    list.innerHTML = data.insights.map(ins => `
        <div class="card-box" style="margin-bottom:1rem;border-left:4px solid ${colorMap[ins.severity]||'#0066ff'};${ins.is_read ? 'opacity:.65' : ''}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
                <div>
                    ${statusBadge(ins.severity)}
                    <strong style="margin-left:8px">${ins.title}</strong>
                    <span style="font-size:11px;color:var(--text-muted);margin-left:8px">${fmtDate(ins.generated_at)}</span>
                </div>
                <div style="display:flex;gap:6px;flex-shrink:0">
                    ${!ins.is_read ? `<button class="btn btn-xs btn-outline-dark" onclick="markInsightRead(${ins.id})"><i class="fas fa-check"></i></button>` : ''}
                    <button class="btn btn-xs btn-outline-dark" onclick="dismissInsight(${ins.id})"><i class="fas fa-trash"></i></button>
                </div>
            </div>
            <p style="font-size:13px;line-height:1.6;white-space:pre-line">${ins.body}</p>
        </div>`).join('');
}

async function generateInsights() {
    const btn = document.getElementById('btnGenInsights');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating…';
    try {
        const res  = await fetch('/api/admin/ai/generate', { method:'POST', headers:{'Content-Type':'application/json'}, body:'{}' });
        const data = await res.json();
        if (res.ok) {
            showToastV3(`Generated: ${data.generated.join(', ')}`, 'success');
            loadAIInsights();
        } else {
            showToastV3(data.error || 'Generation failed', 'error');
        }
    } catch { showToastV3('Could not reach AI endpoint', 'error'); }
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-sparkles"></i> Generate Insights';
}

async function markInsightRead(id) {
    await fetch(`/api/admin/ai-insights/${id}/read`, { method:'PUT' });
    loadAIInsights();
}

async function markAllInsightsRead() {
    await fetch('/api/admin/ai-insights/read-all', { method:'PUT' });
    loadAIInsights();
}

async function dismissInsight(id) {
    await fetch(`/api/admin/ai-insights/${id}`, { method:'DELETE' });
    loadAIInsights();
}

/* ═══════════════════════════════════════════════════════════
   ACTIVITY LOG
═══════════════════════════════════════════════════════════ */
async function loadActivityLog() {
    const entityType = document.getElementById('activityEntityFilter')?.value || '';
    const params     = new URLSearchParams({ limit: 50 });
    if (entityType) params.set('entity_type', entityType);

    const data  = await (await fetch(`/api/admin/activity?${params}`)).json();
    const tbody = document.getElementById('activityTbody');

    tbody.innerHTML = data.activity.length
        ? data.activity.map(a => `
            <tr>
                <td style="font-size:12px;white-space:nowrap">${fmtDate(a.created_at)}</td>
                <td><span style="font-size:12px;background:var(--bg-light,#f5f5f5);padding:2px 8px;border-radius:4px">${a.actor}</span></td>
                <td style="font-family:monospace;font-size:12px">${a.action}</td>
                <td style="font-size:12px">${a.entity_type || '—'}</td>
                <td style="font-size:12px;color:var(--text-muted)">${a.description || '—'}</td>
            </tr>`).join('')
        : '<tr><td colspan="5" class="text-center">No activity recorded yet</td></tr>';
}

/* ─── Pagination helper (reuses pattern from existing admin) ─ */
function renderPagination(containerId, pages, currentPage, loader) {
    const el = document.getElementById(containerId);
    if (!el || pages <= 1) { if (el) el.innerHTML = ''; return; }
    let html = '';
    for (let i = 1; i <= pages; i++) {
        html += `<button class="page-btn${i === currentPage ? ' active' : ''}" onclick="${loader.name}(${i})">${i}</button>`;
    }
    el.innerHTML = html;
}

/* ─── Extra CSS injected inline for nav badges ─────────────── */
const style = document.createElement('style');
style.textContent = `
.nav-badge {
    display:inline-block; min-width:18px; height:18px; line-height:18px; text-align:center;
    border-radius:9px; font-size:10px; font-weight:700; margin-left:auto;
    background: var(--danger-color, #ff3b30); color:#fff; padding:0 5px;
}
.nav-badge--warning { background: var(--warning-color, #ff9500); }
.btn-xs { padding:3px 8px !important; font-size:11px !important; }
.alert-success { background:rgba(0,200,81,.1); border:1px solid rgba(0,200,81,.3); color:var(--success-color,#00c851); }
.alert-warning { background:rgba(255,149,0,.1); border:1px solid rgba(255,149,0,.3); color:var(--warning-color,#ff9500); }
`;
document.head.appendChild(style);
