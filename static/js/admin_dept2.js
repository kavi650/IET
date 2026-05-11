/**
 * admin_dept2.js  Part 2 — Production, Assembly, Electrical, Maintenance, Reports
 */

/* ============================================================
   PRODUCTION
   ============================================================ */
let prodPage = 1;

async function loadProduction(page = 1) {
    prodPage = page;
    const tbody  = document.getElementById('productionTableBody');
    const pager  = document.getElementById('productionPagination');
    if (!tbody) return;

    const filterEl = document.getElementById('prodStatusFilter');
    if (filterEl && !filterEl._wired) {
        filterEl._wired = true;
        filterEl.addEventListener('change', () => loadProduction(1));
    }

    // Wire Add Order button once
    const addBtn = document.getElementById('addOrderBtn');
    if (addBtn && !addBtn._wired) {
        addBtn._wired = true;
        addBtn.addEventListener('click', () => openOrderModal());
    }

    const status = (filterEl || {}).value || '';
    let url = `/api/production/orders?page=${page}&per_page=15`;
    if (status) url += `&status=${status}`;

    try {
        const res  = await fetch(url);
        const data = await res.json();

        if (!res.ok || data.error) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color:red;">Error: ${data.error || res.statusText}</td></tr>`;
            if (pager) pager.innerHTML = '';
            return;
        }

        if (!data.orders || !data.orders.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding:1.5rem;">No orders found.</td></tr>';
            if (pager) pager.innerHTML = '';
            return;
        }

        tbody.innerHTML = (data.orders || []).map(o => `
            <tr>
                <td><strong>#${o.id}</strong></td>
                <td>${o.product_name}</td>
                <td>${o.quantity}</td>
                <td>${o.due_date || '-'}</td>
                <td>
                    <div class="mini-progress-wrap">
                        <div class="mini-progress-bar-wrap">
                            <div class="mini-progress-bar" style="width:${o.progress}%"></div>
                        </div>
                        <span class="mini-progress-label">${o.progress}%</span>
                    </div>
                </td>
                <td><span class="status-badge badge-${o.status}">${o.status.replace('_',' ')}</span></td>
                <td class="actions">
                    <button class="btn-edit" onclick="openOrderModal(${o.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        // Pagination
        if (pager) {
            pager.innerHTML = '';
            for (let i = 1; i <= data.pages; i++) {
                const btn = document.createElement('button');
                btn.className = 'page-btn' + (i === page ? ' active' : '');
                btn.textContent = i;
                btn.onclick = () => loadProduction(i);
                pager.appendChild(btn);
            }
        }
    } catch {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Failed to load orders.</td></tr>';
    }
}

async function openOrderModal(id = null) {
    document.getElementById('editOrderId').value  = id || '';
    document.getElementById('orderModalTitle').textContent = id ? 'Edit Order #' + id : 'New Production Order';

    // Populate product dropdown
    const prodSel = document.getElementById('orderProduct');
    try {
        const res  = await fetch('/api/admin/products');
        const list = await res.json();
        prodSel.innerHTML = '<option value="">Select product…</option>';
        list.forEach(p => { prodSel.innerHTML += `<option value="${p.id}">${p.name}</option>`; });
    } catch { /* ignore */ }

    if (id) {
        try {
            const res   = await fetch(`/api/production/orders/${id}`);
            const order = await res.json();
            prodSel.value = order.product_id || '';
            document.getElementById('orderQty').value      = order.quantity;
            document.getElementById('orderStart').value    = order.start_date || '';
            document.getElementById('orderDue').value      = order.due_date || '';
            document.getElementById('orderStatus').value   = order.status;
            document.getElementById('orderProgress').value = order.progress;
            document.getElementById('orderNotes').value    = order.notes || '';
        } catch { showToast('Failed to load order', 'error'); return; }
    } else {
        document.getElementById('orderQty').value      = 1;
        document.getElementById('orderStart').value    = '';
        document.getElementById('orderDue').value      = '';
        document.getElementById('orderStatus').value   = 'pending';
        document.getElementById('orderProgress').value = 0;
        document.getElementById('orderNotes').value    = '';
    }

    wireOrderModal();
    document.getElementById('orderModal').classList.add('open');
}

function wireOrderModal() {
    const saveBtn   = document.getElementById('saveOrderBtn');
    const closeBtn  = document.getElementById('closeOrderModal');
    const cancelBtn = document.getElementById('cancelOrderModal');
    if (saveBtn._wired) return;
    saveBtn._wired = closeBtn._wired = cancelBtn._wired = true;
    saveBtn.addEventListener('click',   handleSaveOrder);
    closeBtn.addEventListener('click',  () => document.getElementById('orderModal').classList.remove('open'));
    cancelBtn.addEventListener('click', () => document.getElementById('orderModal').classList.remove('open'));
}

async function handleSaveOrder() {
    const id   = document.getElementById('editOrderId').value;
    const data = {
        product_id: parseInt(document.getElementById('orderProduct').value) || null,
        quantity:   parseInt(document.getElementById('orderQty').value) || 1,
        start_date: document.getElementById('orderStart').value || null,
        due_date:   document.getElementById('orderDue').value || null,
        status:     document.getElementById('orderStatus').value,
        progress:   parseInt(document.getElementById('orderProgress').value) || 0,
        notes:      document.getElementById('orderNotes').value.trim()
    };
    if (!data.product_id) { showToast('Select a product', 'error'); return; }

    try {
        const url    = id ? `/api/production/orders/${id}` : '/api/production/orders';
        const method = id ? 'PUT' : 'POST';
        const res    = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const result = await res.json();
        if (result.success) {
            showToast(id ? 'Order updated' : 'Order created', 'success');
            document.getElementById('orderModal').classList.remove('open');
            loadProduction(prodPage);
        } else showToast(result.error || 'Failed', 'error');
    } catch { showToast('Server error', 'error'); }
}

/* ============================================================
   ASSEMBLY
   ============================================================ */
async function loadAssembly() {
    const tbody = document.getElementById('assemblyTableBody');
    if (!tbody) return;
    try {
        const res  = await fetch('/api/assembly/');
        const data = await res.json();

        if (!res.ok || data.error) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color:red;">Error: ${data.error || res.statusText}</td></tr>`;
            return;
        }

        if (!data.assemblies || !data.assemblies.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding:1.5rem;">No assembly records yet.</td></tr>';
            return;
        }
        tbody.innerHTML = (data.assemblies || []).map(a => `
            <tr>
                <td>#${a.id}</td>
                <td>Order #${a.production_id}</td>
                <td>${a.assigned_to || '-'}</td>
                <td>
                    <div class="mini-progress-wrap">
                        <div class="mini-progress-bar-wrap">
                            <div class="mini-progress-bar" style="width:${a.progress}%"></div>
                        </div>
                        <span class="mini-progress-label">${a.progress}%</span>
                    </div>
                </td>
                <td><span class="status-badge badge-${a.status}">${a.status.replace('_',' ')}</span></td>
                <td class="actions">
                    <button class="btn-edit" onclick="openAssemblyModal(${a.id})">
                        <i class="fas fa-list-check"></i> Checklist
                    </button>
                </td>
            </tr>
        `).join('');
    } catch {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Failed to load.</td></tr>';
    }
}

async function openAssemblyModal(id) {
    try {
        const res      = await fetch(`/api/assembly/${id}`);
        const assembly = await res.json();

        document.getElementById('assemblyId').value       = id;
        document.getElementById('assemblyOrderId').textContent = assembly.production_id;
        document.getElementById('assemblyAssigned').value = assembly.assigned_to || '';

        renderChecklist(assembly.checklist, assembly.progress);

        // Wire buttons once
        const closeBtn  = document.getElementById('closeAssemblyModal');
        const cancelBtn = document.getElementById('cancelAssemblyModal');
        const saveBtn   = document.getElementById('saveAssemblyMeta');
        if (!saveBtn._wired) {
            saveBtn._wired = closeBtn._wired = cancelBtn._wired = true;
            closeBtn.addEventListener('click',  () => document.getElementById('assemblyModal').classList.remove('open'));
            cancelBtn.addEventListener('click', () => document.getElementById('assemblyModal').classList.remove('open'));
            saveBtn.addEventListener('click', async () => {
                const aId      = document.getElementById('assemblyId').value;
                const assigned = document.getElementById('assemblyAssigned').value.trim();
                await fetch(`/api/assembly/${aId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ assigned_to: assigned })
                });
                showToast('Details saved', 'success');
                loadAssembly();
            });
        }

        document.getElementById('assemblyModal').classList.add('open');
    } catch { showToast('Failed to load checklist', 'error'); }
}

function renderChecklist(checklist, progress) {
    const ul   = document.getElementById('assemblyChecklist');
    const bar  = document.getElementById('assemblyProgressBar');
    const text = document.getElementById('assemblyProgressText');

    bar.style.width    = progress + '%';
    text.textContent   = progress + '% complete';

    ul.innerHTML = (checklist || []).map((item, idx) => `
        <li class="${item.done ? 'done' : ''}" onclick="toggleCheckItem(${idx})">
            <input type="checkbox" ${item.done ? 'checked' : ''} onclick="event.stopPropagation();toggleCheckItem(${idx})">
            <span>${item.item}</span>
        </li>
    `).join('');
}

async function toggleCheckItem(index) {
    const id = document.getElementById('assemblyId').value;
    try {
        const res    = await fetch(`/api/assembly/${id}/toggle/${index}`, { method: 'PUT' });
        const result = await res.json();
        if (result.success) {
            document.getElementById('assemblyProgressBar').style.width = result.progress + '%';
            document.getElementById('assemblyProgressText').textContent = result.progress + '% complete';
            // Refresh checklist display
            const res2     = await fetch(`/api/assembly/${id}`);
            const assembly = await res2.json();
            renderChecklist(assembly.checklist, assembly.progress);
            loadAssembly();
        }
    } catch { showToast('Failed to update checklist', 'error'); }
}

/* ============================================================
   ELECTRICAL
   ============================================================ */
async function loadElectrical() {
    const tbody  = document.getElementById('electricalTableBody');
    if (!tbody) return;

    const filterEl = document.getElementById('elecStatusFilter');
    if (filterEl && !filterEl._wired) {
        filterEl._wired = true;
        filterEl.addEventListener('change', loadElectrical);
    }

    const addBtn = document.getElementById('addElecBtn');
    if (addBtn && !addBtn._wired) {
        addBtn._wired = true;
        addBtn.addEventListener('click', () => openElecModal());
    }

    const status = (filterEl || {}).value || '';
    const url    = `/api/electrical/${status ? '?status=' + status : ''}`;

    try {
        const res  = await fetch(url);
        const data = await res.json();

        if (!data.tests.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:1.5rem;">No test records yet.</td></tr>';
            return;
        }
        tbody.innerHTML = data.tests.map(t => `
            <tr>
                <td>#${t.id}</td>
                <td>Order #${t.production_id}</td>
                <td>${t.panel_type || '-'}</td>
                <td>${t.plc_type || '-'}</td>
                <td>${t.voltage || '-'}</td>
                <td><span class="status-badge badge-${t.test_status}">${t.test_status}</span></td>
                <td>${t.tested_by || '-'}</td>
                <td class="actions">
                    <button class="btn-edit" onclick="openElecModal(${t.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">Failed to load.</td></tr>';
    }
}

async function openElecModal(id = null) {
    document.getElementById('editElecId').value = id || '';
    document.getElementById('elecModalTitle').textContent = id ? 'Edit Electrical Test #' + id : 'Add Electrical Test';

    if (id) {
        try {
            const res  = await fetch(`/api/electrical/${id}`);
            const test = await res.json();
            document.getElementById('elecOrderId').value  = test.production_id;
            document.getElementById('elecPanel').value    = test.panel_type || '';
            document.getElementById('elecPlc').value      = test.plc_type || '';
            document.getElementById('elecVoltage').value  = test.voltage || '';
            document.getElementById('elecDate').value     = test.test_date || '';
            document.getElementById('elecStatus').value   = test.test_status;
            document.getElementById('elecTestedBy').value = test.tested_by || '';
            document.getElementById('elecRemarks').value  = test.remarks || '';
        } catch { showToast('Failed to load test', 'error'); return; }
    } else {
        document.getElementById('elecOrderId').value  = '';
        document.getElementById('elecPanel').value    = '';
        document.getElementById('elecPlc').value      = '';
        document.getElementById('elecVoltage').value  = '';
        document.getElementById('elecDate').value     = '';
        document.getElementById('elecStatus').value   = 'pending';
        document.getElementById('elecTestedBy').value = '';
        document.getElementById('elecRemarks').value  = '';
    }

    wireElecModal();
    document.getElementById('elecModal').classList.add('open');
}

function wireElecModal() {
    const saveBtn   = document.getElementById('saveElecBtn');
    const closeBtn  = document.getElementById('closeElecModal');
    const cancelBtn = document.getElementById('cancelElecModal');
    if (saveBtn._wired) return;
    saveBtn._wired = closeBtn._wired = cancelBtn._wired = true;
    saveBtn.addEventListener('click',   handleSaveElec);
    closeBtn.addEventListener('click',  () => document.getElementById('elecModal').classList.remove('open'));
    cancelBtn.addEventListener('click', () => document.getElementById('elecModal').classList.remove('open'));
}

async function handleSaveElec() {
    const id   = document.getElementById('editElecId').value;
    const data = {
        production_id: parseInt(document.getElementById('elecOrderId').value),
        panel_type:    document.getElementById('elecPanel').value.trim(),
        plc_type:      document.getElementById('elecPlc').value.trim(),
        voltage:       document.getElementById('elecVoltage').value.trim(),
        test_date:     document.getElementById('elecDate').value || null,
        test_status:   document.getElementById('elecStatus').value,
        tested_by:     document.getElementById('elecTestedBy').value.trim(),
        remarks:       document.getElementById('elecRemarks').value.trim()
    };
    if (!data.production_id) { showToast('Production Order ID required', 'error'); return; }

    try {
        const url    = id ? `/api/electrical/${id}` : '/api/electrical/';
        const method = id ? 'PUT' : 'POST';
        const res    = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const result = await res.json();
        if (result.success) {
            showToast(id ? 'Test updated' : 'Test created', 'success');
            document.getElementById('elecModal').classList.remove('open');
            loadElectrical();
        } else showToast(result.error || 'Failed', 'error');
    } catch { showToast('Server error', 'error'); }
}

/* ============================================================
   MAINTENANCE
   ============================================================ */
async function loadMaintenance() {
    try {
        const res = await fetch('/api/admin/config');
        const cfg = await res.json();
        document.getElementById('maintenanceToggle').checked = cfg.maintenance_mode;
        document.getElementById('maintenanceMsg').value      = cfg.maintenance_message || '';
        document.getElementById('affectedPages').value       = (cfg.affected_pages || []).join(',');
    } catch { showToast('Failed to load config', 'error'); }

    const saveBtn = document.getElementById('saveConfigBtn');
    if (saveBtn && !saveBtn._wired) {
        saveBtn._wired = true;
        saveBtn.addEventListener('click', handleSaveConfig);
    }
}

async function handleSaveConfig() {
    const pages = document.getElementById('affectedPages').value
        .split(',').map(s => s.trim()).filter(Boolean);
    const data = {
        maintenance_mode:    document.getElementById('maintenanceToggle').checked,
        maintenance_message: document.getElementById('maintenanceMsg').value.trim(),
        affected_pages:      pages
    };
    try {
        const res    = await fetch('/api/admin/config', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const result = await res.json();
        if (result.success) showToast('Config saved', 'success');
        else showToast(result.error || 'Failed', 'error');
    } catch { showToast('Server error', 'error'); }
}

/* ============================================================
   REPORTS
   ============================================================ */
async function loadReports() {
    loadReportEnquiries();
    loadReportStock();
    loadReportProduction();
}

async function loadReportEnquiries() {
    const el = document.getElementById('reportEnquiries');
    try {
        const res  = await fetch('/api/admin/reports/enquiries');
        const rows = await res.json();
        if (!rows.length) { el.innerHTML = '<p>No data yet.</p>'; return; }
        el.innerHTML = rows.map(r => `
            <div class="report-row">
                <span>${r.month}</span>
                <span>${r.total} enquiries — ${r.won} won</span>
            </div>
        `).join('');
    } catch { el.innerHTML = '<p>Failed to load.</p>'; }
}

async function loadReportStock() {
    const el = document.getElementById('reportStock');
    try {
        const res  = await fetch('/api/admin/reports/stock');
        const rows = await res.json();
        if (!rows.length) { el.innerHTML = '<p>No stock movements in the last 30 days.</p>'; return; }
        el.innerHTML = rows.map(r => `
            <div class="report-row">
                <span>${r.product_name}</span>
                <span>Used: ${r.consumed} | Added: ${r.added} | Stock: ${r.current_stock}</span>
            </div>
        `).join('');
    } catch { el.innerHTML = '<p>Failed to load.</p>'; }
}

async function loadReportProduction() {
    const el = document.getElementById('reportProduction');
    try {
        const res  = await fetch('/api/admin/reports/production');
        const rows = await res.json();
        if (!rows.length) { el.innerHTML = '<p>No production orders yet.</p>'; return; }
        el.innerHTML = rows.map(r => `
            <div class="report-row">
                <span class="status-badge badge-${r.status}">${r.status.replace('_',' ')}</span>
                <span>${r.count} orders · Avg ${Math.round(r.avg_progress || 0)}% complete</span>
            </div>
        `).join('');
    } catch { el.innerHTML = '<p>Failed to load.</p>'; }
}
