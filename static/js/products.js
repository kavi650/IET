/**
 * Teslead Equipments - Products Page JavaScript
 * Handles: Category filtering, search, dynamic product loading
 */

document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadProducts();
    initSearch();
});

let allProducts = [];
let currentCategory = 'all';

/* ============================================
   LOAD CATEGORIES
   ============================================ */
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();

        const filterTabs = document.getElementById('filterTabs');
        if (!filterTabs) return;

        categories.forEach(cat => {
            const btn = document.createElement('button');
            btn.className = 'filter-tab';
            btn.setAttribute('data-category', cat.id);
            btn.textContent = cat.name;
            btn.addEventListener('click', () => filterByCategory(cat.id, btn));
            filterTabs.appendChild(btn);
        });

        // Check URL params for pre-selected category
        const urlParams = new URLSearchParams(window.location.search);
        const catId = urlParams.get('category');
        if (catId) {
            const tab = filterTabs.querySelector(`[data-category="${catId}"]`);
            if (tab) filterByCategory(parseInt(catId), tab);
        }
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

/* ============================================
   LOAD PRODUCTS
   ============================================ */
async function loadProducts(categoryId = null, search = '') {
    const grid = document.getElementById('productsGrid');
    const noResults = document.getElementById('noResults');

    // Show loading
    grid.innerHTML = `
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
    `;
    noResults?.classList.add('hidden');

    try {
        let url = '/api/products';
        const params = new URLSearchParams();
        if (categoryId) params.set('category_id', categoryId);
        if (search) params.set('search', search);
        if (params.toString()) url += '?' + params.toString();

        const response = await fetch(url);
        const products = await response.json();
        allProducts = products;

        renderProducts(products);
    } catch (error) {
        console.error('Failed to load products:', error);
        grid.innerHTML = '<p class="text-center" style="grid-column:1/-1; padding:var(--space-2xl); color:var(--text-muted);">Failed to load products. Make sure the server is running.</p>';
    }
}

/* ============================================
   RENDER PRODUCTS
   ============================================ */
function renderProducts(products) {
    const grid = document.getElementById('productsGrid');
    const noResults = document.getElementById('noResults');

    if (products.length === 0) {
        grid.innerHTML = '';
        noResults?.classList.remove('hidden');
        return;
    }

    noResults?.classList.add('hidden');

    grid.innerHTML = products.map((product, index) => `
        <div class="card product-card reveal visible" style="animation-delay: ${index * 0.1}s;">
            <div class="card-img-wrapper">
                <img src="${product.image_url || '/static/images/default_product.jpg'}" 
                     alt="${product.name}" 
                     class="card-img"
                     onerror="this.style.background='linear-gradient(135deg, #0B3D91, #1a5cc8)'; this.style.display='flex'; this.style.alignItems='center'; this.style.justifyContent='center'; this.innerHTML='<i class=\\'fas fa-cogs\\' style=\\'font-size:3rem;color:rgba(255,255,255,0.4)\\'></i>'">
            </div>
            <div class="card-body">
                <span class="card-badge">${product.category_name || 'General'}</span>
                <h3 class="card-title">${product.name}</h3>
                <p class="card-text">${product.description || 'Industrial equipment product.'}</p>
                <a href="/product/${product.id}" class="btn btn-outline-dark btn-sm">
                    View Details <i class="fas fa-arrow-right"></i>
                </a>
            </div>
        </div>
    `).join('');
}

/* ============================================
   FILTER BY CATEGORY
   ============================================ */
function filterByCategory(categoryId, clickedTab) {
    // Update active tab
    document.querySelectorAll('.filter-tab').forEach(tab => tab.classList.remove('active'));
    clickedTab.classList.add('active');

    currentCategory = categoryId;

    if (categoryId === 'all') {
        loadProducts();
    } else {
        loadProducts(categoryId);
    }
}

// Handle "All Products" tab
document.addEventListener('DOMContentLoaded', () => {
    const allTab = document.querySelector('[data-category="all"]');
    if (allTab) {
        allTab.addEventListener('click', () => filterByCategory('all', allTab));
    }
});

/* ============================================
   SEARCH
   ============================================ */
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    let debounceTimer;

    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = searchInput.value.trim();
            const categoryId = currentCategory === 'all' ? null : currentCategory;
            loadProducts(categoryId, query);
        }, 300);
    });
}
