/**
 * Teslead Equipments - Product Detail Page JavaScript
 * Handles: Loading product data, specs table, tabs, related products
 */

document.addEventListener('DOMContentLoaded', () => {
    const productId = getProductIdFromUrl();
    if (productId) {
        loadProductDetail(productId);
    }
    initTabs();
});

/* ============================================
   GET PRODUCT ID FROM URL
   ============================================ */
function getProductIdFromUrl() {
    const path = window.location.pathname;
    const match = path.match(/\/product\/(\d+)/);
    return match ? parseInt(match[1]) : null;
}

/* ============================================
   LOAD PRODUCT DETAIL
   ============================================ */
async function loadProductDetail(productId) {
    try {
        const response = await fetch(`/api/product/${productId}`);
        if (!response.ok) throw new Error('Product not found');

        const product = await response.json();
        renderProductDetail(product);
        loadRelatedProducts(product.category_id, productId);
    } catch (error) {
        console.error('Failed to load product:', error);
        document.getElementById('detailName').textContent = 'Product Not Found';
        document.getElementById('detailDescription').textContent = 'The requested product could not be found.';
    }
}

/* ============================================
   RENDER PRODUCT DETAIL
   ============================================ */
function renderProductDetail(product) {
    // Page header
    document.getElementById('productTitle').textContent = product.name;
    document.getElementById('breadcrumbName').textContent = product.name;
    document.title = `${product.name} | Testiny Equipments`;

    // Update meta
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
        metaDesc.setAttribute('content', product.description || `${product.name} - Testiny Equipments`);
    }

    // Product image
    const img = document.getElementById('productImage');
    if (img) {
        img.src = product.image_url || '/static/images/default_product.jpg';
        img.alt = product.name;
    }

    // Product info
    document.getElementById('detailName').textContent = product.name;
    document.getElementById('detailCategory').textContent = product.category_name || 'Industrial Equipment';
    document.getElementById('detailDescription').textContent = product.description || '';

    // Specifications table
    const specsBody = document.getElementById('specsBody');
    if (specsBody && product.specifications && product.specifications.length > 0) {
        specsBody.innerHTML = product.specifications.map(spec => `
            <tr>
                <td>${spec.key}</td>
                <td>${spec.value}</td>
            </tr>
        `).join('');
    } else if (specsBody) {
        specsBody.innerHTML = '<tr><td colspan="2" class="text-center">No specifications available</td></tr>';
    }

    // Working Principle
    const principleContent = document.getElementById('principleContent');
    if (principleContent) {
        principleContent.innerHTML = product.working_principle
            ? `<p>${product.working_principle}</p>`
            : '<p>Working principle information not available.</p>';
    }

    // Applications
    const applicationsContent = document.getElementById('applicationsContent');
    if (applicationsContent) {
        if (product.applications) {
            const apps = product.applications.split(',').map(a => a.trim()).filter(a => a);
            applicationsContent.innerHTML = `
                <ul style="list-style:none; padding:0;">
                    ${apps.map(app => `
                        <li style="display:flex; align-items:center; gap:var(--space-sm); padding:var(--space-sm) 0; border-bottom:1px solid var(--border-light);">
                            <i class="fas fa-check-circle" style="color:var(--accent);"></i>
                            <span>${app}</span>
                        </li>
                    `).join('')}
                </ul>
            `;
        } else {
            applicationsContent.innerHTML = '<p>Application information not available.</p>';
        }
    }
}

/* ============================================
   TABS
   ============================================ */
function initTabs() {
    const tabs = document.querySelectorAll('.product-tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Deactivate all
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            // Activate clicked
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            const content = document.getElementById(`tab-${tabId}`);
            if (content) content.classList.add('active');
        });
    });
}

/* ============================================
   LOAD RELATED PRODUCTS
   ============================================ */
async function loadRelatedProducts(categoryId, currentProductId) {
    const container = document.getElementById('relatedProducts');
    if (!container) return;

    try {
        const response = await fetch(`/api/products?category_id=${categoryId}`);
        const products = await response.json();

        // Filter out current product
        const related = products.filter(p => p.id !== currentProductId).slice(0, 3);

        if (related.length === 0) {
            container.innerHTML = '<p class="text-center" style="grid-column:1/-1; color:var(--text-muted);">No related products found.</p>';
            return;
        }

        container.innerHTML = related.map(product => `
            <div class="card product-card">
                <div class="card-img-wrapper">
                    <img src="${product.image_url || '/static/images/default_product.jpg'}" 
                         alt="${product.name}" 
                         class="card-img"
                         onerror="this.style.background='linear-gradient(135deg, #0B3D91, #1a5cc8)'; this.style.display='flex'; this.style.alignItems='center'; this.style.justifyContent='center'; this.innerHTML='<i class=\\'fas fa-cogs\\' style=\\'font-size:3rem;color:rgba(255,255,255,0.4)\\'></i>'">
                </div>
                <div class="card-body">
                    <span class="card-badge">${product.category_name || 'General'}</span>
                    <h3 class="card-title">${product.name}</h3>
                    <p class="card-text">${product.description || ''}</p>
                    <a href="/product/${product.id}" class="btn btn-outline-dark btn-sm">
                        View Details <i class="fas fa-arrow-right"></i>
                    </a>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load related products:', error);
        container.innerHTML = '';
    }
}
