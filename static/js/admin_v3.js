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
            </tr>`).join('')
        : '<tr><td colspan="8" class="text-center">No sessions found</td></tr>';

    renderPagination('testSessionsPagination', data.pages, page, loadTestSessions);
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
