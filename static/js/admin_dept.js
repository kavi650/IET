/**
 * admin_dept.js  Part 1 — Stores, Sales
 */

/* ============================================================
   STORES
   ============================================================ */
async function loadStores() {
    const tbody = document.getElementById('storesTableBody');
    if (!tbody) return;

    // Wire search + filter once
    const searchEl   = document.getElementById('storeSearch');
    const lowOnlyEl  = document.getElementById('lowStockOnly');
    if (searchEl && !searchEl._wired) {
        searchEl._wired = true;
        searchEl.addEventListener('input', debounce(loadStores, 350));
        lowOnlyEl && lowOnlyEl.addEventListener('change', loadStores);
    }

    const search  = (searchEl || {}).value || '';
    const lowOnly = (lowOnlyEl || {}).checked || false;
    let url = `/api/stores/inventory?low_stock=${lowOnly}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const res   = await fetch(url);
        const items = await res.json();

        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding:1.5rem;">No products found.</td></tr>';
            return;
        }

        tbody.innerHTML = items.map(p => `
            <tr>
                <td>${p.name}</td>
                <td>${p.category_name}</td>
                <td><strong>${p.stock}</strong></td>
                <td>${p.reorder_level}</td>
                <td>
                    ${p.is_low_stock
                        ? '<span class="low-stock-pill">⚠ Low Stock</span>'
                        : '<span class="ok-pill">✓ OK</span>'}
                </td>
                <td class="actions">
                    <button class="btn-edit"
                        onclick="openStockModal(${p.id},'${esc(p.name)}','add')">
                        <i class="fas fa-plus"></i> Add
                    </button>
                    <button class="btn-delete"
                        onclick="openStockModal(${p.id},'${esc(p.name)}','reduce')">
                        <i class="fas fa-minus"></i> Reduce
                    </button>
                </td>
            </tr>
        `).join('');
    } catch {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Failed to load inventory.</td></tr>';
    }
}

function openStockModal(productId, name, action) {
    document.getElementById('stockProductId').value = productId;
    document.getElementById('stockAction').value    = action;
    document.getElementById('stockQty').value       = 1;
    document.getElementById('stockReason').value    = '';
    document.getElementById('stockModalTitle').textContent =
        (action === 'add' ? 'Add Stock — ' : 'Reduce Stock — ') + name;

    // Wire confirm once
    const btn = document.getElementById('confirmStockBtn');
    if (!btn._wired) {
        btn._wired = true;
        btn.addEventListener('click', handleStockAdjust);
    }

    const closeBtn  = document.getElementById('closeStockModal');
    const cancelBtn = document.getElementById('cancelStockModal');
    if (!closeBtn._wired) {
        closeBtn._wired = cancelBtn._wired = true;
        closeBtn.addEventListener('click',  () => document.getElementById('stockModal').classList.remove('open'));
        cancelBtn.addEventListener('click', () => document.getElementById('stockModal').classList.remove('open'));
    }

    document.getElementById('stockModal').classList.add('open');
}

async function handleStockAdjust() {
    const productId = document.getElementById('stockProductId').value;
    const action    = document.getElementById('stockAction').value;
    const qty       = parseInt(document.getElementById('stockQty').value);
    const reason    = document.getElementById('stockReason').value.trim() || action;

    if (!qty || qty < 1) { showToast('Enter a valid quantity', 'error'); return; }

    try {
        const res    = await fetch(`/api/stores/stock/${productId}/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: qty, reason })
        });
        const result = await res.json();
        if (result.success) {
            showToast(`Stock ${action === 'add' ? 'added' : 'reduced'} — new stock: ${result.new_stock}`, 'success');
            document.getElementById('stockModal').classList.remove('open');
            loadStores();
        } else {
            showToast(result.error || 'Failed', 'error');
        }
    } catch {
        showToast('Server error', 'error');
    }
}

/* ============================================================
   SALES
   ============================================================ */
let salesPage = 1;

async function loadSales(page = 1) {
    salesPage = page;
    const tbody  = document.getElementById('salesTableBody');
    const pager  = document.getElementById('salesPagination');
    if (!tbody) return;

    // Wire filters once
    const searchEl = document.getElementById('salesSearch');
    const filterEl = document.getElementById('salesStatusFilter');
    if (searchEl && !searchEl._wired) {
        searchEl._wired = filterEl._wired = true;
        searchEl.addEventListener('input',  debounce(() => loadSales(1), 350));
        filterEl.addEventListener('change', () => loadSales(1));
    }

    const search = (searchEl || {}).value || '';
    const status = (filterEl || {}).value || '';
    let url = `/api/sales/enquiries?page=${page}&per_page=15`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (status) url += `&status=${status}`;

    try {
        const res  = await fetch(url);
        const data = await res.json();

        if (!res.ok || data.error) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color:red;">Error: ${data.error || res.statusText}</td></tr>`;
            return;
        }

        // Pipeline bar
        await loadPipelineBar();

        if (!data.enquiries || !data.enquiries.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding:1.5rem;">No enquiries found.</td></tr>';
            pager.innerHTML = '';
            return;
        }

        tbody.innerHTML = (data.enquiries || []).map(e => `
            <tr>
                <td>#${e.id}</td>
                <td>${e.name}</td>
                <td>${e.company || '-'}</td>
                <td>${e.estimated_value ? '₹' + Number(e.estimated_value).toLocaleString('en-IN') : '-'}</td>
                <td><span class="status-badge badge-${e.status}">${e.status}</span></td>
                <td>${new Date(e.created_at).toLocaleDateString()}</td>
                <td class="actions">
                    <button class="btn-edit" onclick="openSalesModal(${e.id},'${e.status}',${e.estimated_value || 0})">
                        <i class="fas fa-edit"></i> Status
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
                btn.onclick = () => loadSales(i);
                pager.appendChild(btn);
            }
        }
    } catch {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Failed to load enquiries.</td></tr>';
    }
}

async function loadPipelineBar() {
    try {
        const res  = await fetch('/api/sales/pipeline');
        const data = await res.json();
        const bar  = document.getElementById('pipelineBar');
        if (!bar) return;
        const colors = { new:'#dbeafe', contacted:'#ffedd5', quotation:'#ede9fe', won:'#dcfce7', lost:'#fee2e2' };
        const textColors = { new:'#1d4ed8', contacted:'#c2410c', quotation:'#6d28d9', won:'#15803d', lost:'#b91c1c' };
        bar.innerHTML = Object.entries(data).map(([status, info]) => `
            <span class="pipeline-pill" style="background:${colors[status]};color:${textColors[status]};">
                ${status}: ${info.count}
                ${info.value ? ' · ₹' + Number(info.value).toLocaleString('en-IN') : ''}
            </span>
        `).join('');
    } catch { /* ignore */ }
}

function openSalesModal(id, currentStatus, currentValue) {
    document.getElementById('salesEnqId').value      = id;
    document.getElementById('salesNewStatus').value  = currentStatus;
    document.getElementById('salesValue').value      = currentValue || '';

    toggleWonHint();
    document.getElementById('salesNewStatus').onchange = toggleWonHint;

    const btn = document.getElementById('saveSalesStatus');
    if (!btn._wired) {
        btn._wired = true;
        btn.addEventListener('click', handleSalesStatus);
    }

    const closeBtn  = document.getElementById('closeSalesModal');
    const cancelBtn = document.getElementById('cancelSalesModal');
    if (!closeBtn._wired) {
        closeBtn._wired = cancelBtn._wired = true;
        closeBtn.addEventListener('click',  () => document.getElementById('salesModal').classList.remove('open'));
        cancelBtn.addEventListener('click', () => document.getElementById('salesModal').classList.remove('open'));
    }

    document.getElementById('salesModal').classList.add('open');
}

function toggleWonHint() {
    const status = document.getElementById('salesNewStatus').value;
    const hint   = document.getElementById('salesWonHint');
    if (hint) hint.style.display = (status === 'won') ? 'block' : 'none';
}

async function handleSalesStatus() {
    const id     = document.getElementById('salesEnqId').value;
    const status = document.getElementById('salesNewStatus').value;
    const value  = parseFloat(document.getElementById('salesValue').value) || 0;

    try {
        const res    = await fetch(`/api/sales/enquiries/${id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, estimated_value: value })
        });
        const result = await res.json();
        if (result.success) {
            let msg = 'Status updated!';
            if (result.production_order_created) {
                msg += ` Production Order #${result.production_order_id} created.`;
            }
            showToast(msg, 'success');
            document.getElementById('salesModal').classList.remove('open');
            loadSales(salesPage);
        } else {
            showToast(result.error || 'Failed', 'error');
        }
    } catch {
        showToast('Server error', 'error');
    }
}
