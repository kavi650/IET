/**
 * admin.js — Original admin panel logic (Products, Categories, Enquiries, Chat Logs)
 * All existing functions preserved unchanged.
 * Dashboard load + extended nav routing added at bottom.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAdminNav();
    initModals();
    loadDashboard();          // default section is now dashboard
});

/* ============================================================
   ADMIN NAVIGATION
   ============================================================ */
function initAdminNav() {
    const navLinks = document.querySelectorAll('#adminNav a');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            const sectionId = link.getAttribute('data-section');
            document.querySelectorAll('.admin-section').forEach(s => s.style.display = 'none');
            const section = document.getElementById(`section-${sectionId}`);
            if (section) section.style.display = 'block';

            switch (sectionId) {
                case 'dashboard':   loadDashboard();           break;
                case 'products':    loadAdminProducts();        break;
                case 'categories':  loadAdminCategories();      break;
                case 'enquiries':   loadAdminEnquiries();       break;
                case 'chatlogs':    loadAdminChatLogs();        break;
                // Department sections handled in admin_dept.js
                case 'stores':      loadStores();               break;
                case 'sales':       loadSales();                break;
                case 'production':  loadProduction();           break;
                case 'assembly':    loadAssembly();             break;
                case 'electrical':  loadElectrical();           break;
                case 'maintenance': loadMaintenance();          break;
                case 'reports':     loadReports();              break;
            }
        });
    });
}

/* ============================================================
   DASHBOARD
   ============================================================ */
async function loadDashboard() {
    try {
        const res  = await fetch('/api/admin/dashboard');
        const data = await res.json();
        document.getElementById('dc-lowstock').textContent  = data.low_stock_count   ?? '—';
        document.getElementById('dc-enquiries').textContent = data.new_enquiries      ?? '—';
        document.getElementById('dc-active').textContent    = data.active_orders      ?? '—';
        document.getElementById('dc-completed').textContent = data.completed_orders   ?? '—';
    } catch {
        // silently fail — server may not be up
    }
}

/* ============================================================
   MODAL MANAGEMENT
   ============================================================ */
function initModals() {
    bindModal('addProductBtn',    'productModal',  'closeProductModal',  'cancelProductModal');
    bindModal('addCategoryBtn',   'categoryModal', 'closeCategoryModal', 'cancelCategoryModal');

    const saveProduct  = document.getElementById('saveProduct');
    const saveCategory = document.getElementById('saveCategory');
    const addProductBtn = document.getElementById('addProductBtn');

    if (addProductBtn) {
        addProductBtn.addEventListener('click', () => {
            document.getElementById('modalTitle').textContent = 'Add Product';
            document.getElementById('productForm').reset();
            document.getElementById('editProductId').value = '';
            loadCategoryOptions();
        });
    }

    if (saveProduct)  saveProduct.addEventListener('click', handleSaveProduct);
    if (saveCategory) saveCategory.addEventListener('click', handleSaveCategory);

    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('open');
        });
    });
}

function bindModal(openId, overlayId, closeId, cancelId) {
    const open   = document.getElementById(openId);
    const overlay = document.getElementById(overlayId);
    const close  = document.getElementById(closeId);
    const cancel = document.getElementById(cancelId);
    if (open)   open.addEventListener('click',   () => overlay && overlay.classList.add('open'));
    if (close)  close.addEventListener('click',  () => overlay && overlay.classList.remove('open'));
    if (cancel) cancel.addEventListener('click', () => overlay && overlay.classList.remove('open'));
}

/* ============================================================
   PRODUCTS CRUD  (original, unchanged)
   ============================================================ */
async function loadAdminProducts() {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) return;

    // search wiring
    const searchInput = document.getElementById('productSearch');
    if (searchInput && !searchInput._wired) {
        searchInput._wired = true;
        searchInput.addEventListener('input', debounce(loadAdminProducts, 350));
    }

    const search = (document.getElementById('productSearch') || {}).value || '';

    try {
        const res      = await fetch(`/api/admin/products${search ? '?search=' + encodeURIComponent(search) : ''}`);
        const products = await res.json();

        if (!products.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding:var(--space-xl);">No products found.</td></tr>';
            return;
        }

        tbody.innerHTML = products.map(p => `
            <tr>
                <td><strong>#${p.id}</strong></td>
                <td>${p.name}</td>
                <td><span class="badge badge-info">${p.category_name || 'N/A'}</span></td>
                <td>
                    ${p.is_low_stock
                        ? `<span class="low-stock-pill">${p.stock} ⚠ Low</span>`
                        : `<span class="ok-pill">${p.stock}</span>`
                    }
                </td>
                <td>${new Date(p.created_at).toLocaleDateString()}</td>
                <td class="actions">
                    <button class="btn-edit"   onclick="editProduct(${p.id})"><i class="fas fa-edit"></i> Edit</button>
                    <button class="btn-delete" onclick="deleteProduct(${p.id}, '${esc(p.name)}')"><i class="fas fa-trash"></i> Delete</button>
                </td>
            </tr>
        `).join('');
    } catch {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Failed to load products.</td></tr>';
    }
}

async function handleSaveProduct() {
    const editId = document.getElementById('editProductId').value;
    const data   = {
        name:              document.getElementById('prodName').value.trim(),
        category_id:       parseInt(document.getElementById('prodCategory').value) || null,
        description:       document.getElementById('prodDescription').value.trim(),
        working_principle: document.getElementById('prodPrinciple').value.trim(),
        applications:      document.getElementById('prodApplications').value.trim(),
        image_url:         document.getElementById('prodImage').value.trim() || '/static/images/default_product.jpg',
        stock:             parseInt(document.getElementById('prodStock').value) || 0,
        reorder_level:     parseInt(document.getElementById('prodReorder').value) || 10,
    };

    if (!data.name) { showToast('Product name is required', 'error'); return; }

    try {
        const url    = editId ? `/api/admin/products/${editId}` : '/api/admin/products';
        const method = editId ? 'PUT' : 'POST';
        const res    = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const result = await res.json();
        if (result.success) {
            showToast(editId ? 'Product updated!' : 'Product added!', 'success');
            document.getElementById('productModal').classList.remove('open');
            loadAdminProducts();
        } else { showToast(result.error || 'Failed to save', 'error'); }
    } catch { showToast('Server error', 'error'); }
}

async function editProduct(id) {
    try {
        const res     = await fetch(`/api/product/${id}`);
        const product = await res.json();
        document.getElementById('modalTitle').textContent       = 'Edit Product';
        document.getElementById('editProductId').value          = id;
        document.getElementById('prodName').value               = product.name || '';
        document.getElementById('prodDescription').value        = product.description || '';
        document.getElementById('prodPrinciple').value          = product.working_principle || '';
        document.getElementById('prodApplications').value       = product.applications || '';
        document.getElementById('prodImage').value              = product.image_url || '';
        document.getElementById('prodStock').value              = product.stock || 0;
        document.getElementById('prodReorder').value            = product.reorder_level || 10;
        await loadCategoryOptions();
        document.getElementById('prodCategory').value = product.category_id || '';
        document.getElementById('productModal').classList.add('open');
    } catch { showToast('Failed to load product', 'error'); }
}

async function deleteProduct(id, name) {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
        const res    = await fetch(`/api/admin/products/${id}`, { method: 'DELETE' });
        const result = await res.json();
        if (result.success) { showToast('Product deleted', 'success'); loadAdminProducts(); }
        else showToast(result.error || 'Failed to delete', 'error');
    } catch { showToast('Server error', 'error'); }
}

async function loadCategoryOptions() {
    const select = document.getElementById('prodCategory');
    if (!select) return;
    try {
        const res        = await fetch('/api/admin/categories');
        const categories = await res.json();
        select.innerHTML = '<option value="">Select Category</option>';
        categories.forEach(cat => select.innerHTML += `<option value="${cat.id}">${cat.name}</option>`);
    } catch { console.error('Failed to load categories'); }
}

/* ============================================================
   CATEGORIES  (original, unchanged)
   ============================================================ */
async function loadAdminCategories() {
    const tbody = document.getElementById('categoriesTableBody');
    if (!tbody) return;
    try {
        const res        = await fetch('/api/admin/categories');
        const categories = await res.json();
        tbody.innerHTML  = categories.map(c => `
            <tr>
                <td><strong>#${c.id}</strong></td>
                <td>${c.name}</td>
                <td>${c.description || '-'}</td>
                <td><i class="fas ${c.icon || 'fa-cog'}"></i> ${c.icon || 'fa-cog'}</td>
            </tr>
        `).join('');
    } catch { tbody.innerHTML = '<tr><td colspan="4" class="text-center">Failed to load</td></tr>'; }
}

async function handleSaveCategory() {
    const data = {
        name:        document.getElementById('catName').value.trim(),
        description: document.getElementById('catDescription').value.trim(),
        icon:        document.getElementById('catIcon').value.trim() || 'fa-cog'
    };
    if (!data.name) { showToast('Category name is required', 'error'); return; }
    try {
        const res    = await fetch('/api/admin/categories', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        const result = await res.json();
        if (result.success) {
            showToast('Category added!', 'success');
            document.getElementById('categoryModal').classList.remove('open');
            loadAdminCategories();
        } else showToast(result.error || 'Failed', 'error');
    } catch { showToast('Server error', 'error'); }
}

/* ============================================================
   ENQUIRIES  (original, enhanced with status badge)
   ============================================================ */
async function loadAdminEnquiries() {
    const tbody = document.getElementById('enquiriesTableBody');
    if (!tbody) return;
    try {
        const res  = await fetch('/api/admin/enquiries');
        const data = await res.json();
        const list = data.enquiries || data;   // handle both old + new response shapes

        if (!list.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="padding:var(--space-xl);">No enquiries yet.</td></tr>';
            return;
        }
        tbody.innerHTML = list.map(e => `
            <tr>
                <td>#${e.id}</td>
                <td>${e.name}</td>
                <td>${e.email}</td>
                <td>${e.company || '-'}</td>
                <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${e.message}">${e.message}</td>
                <td><span class="status-badge badge-${e.status || 'new'}">${e.status || 'new'}</span></td>
                <td>${new Date(e.created_at).toLocaleDateString()}</td>
                <td>
                    ${!e.is_read ? `<button class="btn-edit" onclick="markRead(${e.id})"><i class="fas fa-check"></i> Read</button>` : ''}
                </td>
            </tr>
        `).join('');
    } catch { tbody.innerHTML = '<tr><td colspan="8" class="text-center">Failed to load</td></tr>'; }
}

async function markRead(id) {
    try {
        await fetch(`/api/admin/enquiries/${id}/read`, { method: 'PUT' });
        showToast('Marked as read', 'success');
        loadAdminEnquiries();
    } catch { showToast('Failed to update', 'error'); }
}

/* ============================================================
   CHAT LOGS  (original, enhanced with analytics)
   ============================================================ */
async function loadAdminChatLogs() {
    const tbody    = document.getElementById('chatlogsTableBody');
    const analytics = document.getElementById('chatAnalytics');
    if (!tbody) return;

    // Wire up clear button
    const clearBtn = document.getElementById('clearLogsBtn');
    if (clearBtn && !clearBtn._wired) {
        clearBtn._wired = true;
        clearBtn.addEventListener('click', async () => {
            if (!confirm('Clear ALL chat logs?')) return;
            await fetch('/api/admin/chatlog', { method: 'DELETE' });
            showToast('All logs cleared', 'success');
            loadAdminChatLogs();
        });
    }

    try {
        const res  = await fetch('/api/admin/chatlog');
        const data = await res.json();
        const logs = data.logs || data;

        // Analytics strip
        if (analytics && data.total_queries !== undefined) {
            analytics.innerHTML = `
                <div class="chat-stat"><strong>${data.total_queries}</strong>Total Queries</div>
                ${(data.top_questions || []).map(q =>
                    `<div class="chat-stat"><strong>${q.count}</strong>"${q.word}"</div>`
                ).join('')}
            `;
        }

        if (!logs.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center" style="padding:var(--space-xl);">No chat logs yet.</td></tr>';
            return;
        }
        tbody.innerHTML = logs.map(l => `
            <tr>
                <td>#${l.id}</td>
                <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${esc(l.query)}">${l.query}</td>
                <td style="max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${esc(l.response)}">${l.response.substring(0, 100)}…</td>
                <td>${new Date(l.created_at).toLocaleString()}</td>
            </tr>
        `).join('');
    } catch { tbody.innerHTML = '<tr><td colspan="4" class="text-center">Failed to load</td></tr>'; }
}

/* ============================================================
   UTILITIES
   ============================================================ */
function esc(str) {
    return String(str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function debounce(fn, delay) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}
