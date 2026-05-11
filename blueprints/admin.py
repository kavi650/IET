"""
blueprints/admin.py
Admin panel: products, categories, enquiries, chat logs, dashboard stats.
All existing admin APIs preserved; dashboard cards added.
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import func, text
from models import (
    db, Category, Product, Specification,
    Enquiry, ChatbotLog, ProductionOrder, SiteConfig
)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ============================================================
# DASHBOARD STATS
# ============================================================

@admin_bp.route('/dashboard', methods=['GET'])
def dashboard_stats():
    """Aggregate counts for admin dashboard cards."""
    low_stock      = Product.query.filter(Product.stock < Product.reorder_level).count()
    new_enquiries  = Enquiry.query.filter_by(status='new').count()
    active_orders  = ProductionOrder.query.filter(
        ProductionOrder.status.in_(['pending', 'in_progress'])
    ).count()
    completed      = ProductionOrder.query.filter_by(status='completed').count()
    total_products = Product.query.count()
    total_enquiries= Enquiry.query.count()

    return jsonify({
        'low_stock_count':     low_stock,
        'new_enquiries':       new_enquiries,
        'active_orders':       active_orders,
        'completed_orders':    completed,
        'total_products':      total_products,
        'total_enquiries':     total_enquiries,
    })


# ============================================================
# PRODUCTS  (existing routes preserved)
# ============================================================

@admin_bp.route('/products', methods=['GET'])
def admin_products():
    """Get all products for admin management."""
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])


@admin_bp.route('/products', methods=['POST'])
def admin_add_product():
    """Add a new product."""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Product name is required'}), 400

    product = Product(
        name              = data['name'],
        category_id       = data.get('category_id'),
        description       = data.get('description', ''),
        working_principle = data.get('working_principle', ''),
        applications      = data.get('applications', ''),
        image_url         = data.get('image_url', '/static/images/default_product.jpg'),
        stock             = data.get('stock', 0),
        reorder_level     = data.get('reorder_level', 10),
    )

    try:
        db.session.add(product)
        db.session.flush()

        for spec in data.get('specifications', []):
            if spec.get('key') and spec.get('value'):
                db.session.add(Specification(product_id=product.id, key=spec['key'], value=spec['value']))

        db.session.commit()
        return jsonify({'success': True, 'product': product.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
def admin_update_product(product_id):
    """Update an existing product."""
    product = Product.query.get_or_404(product_id)
    data    = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    product.name              = data.get('name', product.name)
    product.category_id       = data.get('category_id', product.category_id)
    product.description       = data.get('description', product.description)
    product.working_principle = data.get('working_principle', product.working_principle)
    product.applications      = data.get('applications', product.applications)
    product.image_url         = data.get('image_url', product.image_url)
    product.reorder_level     = data.get('reorder_level', product.reorder_level)

    if 'specifications' in data:
        Specification.query.filter_by(product_id=product.id).delete()
        for spec in data['specifications']:
            if spec.get('key') and spec.get('value'):
                db.session.add(Specification(product_id=product.id, key=spec['key'], value=spec['value']))

    try:
        db.session.commit()
        return jsonify({'success': True, 'product': product.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
def admin_delete_product(product_id):
    """Delete a product."""
    product = Product.query.get_or_404(product_id)

    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# CATEGORIES  (existing routes preserved)
# ============================================================

@admin_bp.route('/categories', methods=['GET'])
def admin_categories():
    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories])


@admin_bp.route('/categories', methods=['POST'])
def admin_add_category():
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Category name is required'}), 400

    category = Category(
        name        = data['name'],
        description = data.get('description', ''),
        icon        = data.get('icon', 'fa-cog')
    )

    try:
        db.session.add(category)
        db.session.commit()
        return jsonify({'success': True, 'category': category.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
def admin_update_category(category_id):
    category = Category.query.get_or_404(category_id)
    data     = request.get_json()

    category.name        = data.get('name', category.name)
    category.description = data.get('description', category.description)
    category.icon        = data.get('icon', category.icon)

    try:
        db.session.commit()
        return jsonify({'success': True, 'category': category.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def admin_delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# ENQUIRIES  (existing + new status update)
# ============================================================

@admin_bp.route('/enquiries', methods=['GET'])
def admin_enquiries():
    """Get enquiries with optional status filter, search, pagination."""
    status   = request.args.get('status')
    search   = request.args.get('search', '')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Enquiry.query

    if status:
        query = query.filter_by(status=status)

    if search:
        query = query.filter(
            Enquiry.name.ilike(f'%{search}%') |
            Enquiry.company.ilike(f'%{search}%') |
            Enquiry.email.ilike(f'%{search}%')
        )

    pagination = query.order_by(Enquiry.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'enquiries': [e.to_dict() for e in pagination.items],
        'total':     pagination.total,
        'pages':     pagination.pages,
        'page':      page
    })


@admin_bp.route('/enquiries/<int:enquiry_id>/read', methods=['PUT'])
def admin_mark_read(enquiry_id):
    enquiry         = Enquiry.query.get_or_404(enquiry_id)
    enquiry.is_read = True

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# CHAT LOGS  (existing)
# ============================================================

@admin_bp.route('/chatlog', methods=['GET'])
def admin_chatlog():
    """Get chatbot logs with basic analytics."""
    # ChatbotLog has a column named 'query' which shadows .query — use db.session.query()
    logs = db.session.query(ChatbotLog).order_by(ChatbotLog.created_at.desc()).all()

    # Top 5 most-asked words (simple frequency)
    from collections import Counter
    import re
    all_words = []
    for log in logs:
        words = re.findall(r'\b[a-z]{4,}\b', log.query.lower())
        all_words.extend(words)

    stop_words = {'what', 'does', 'your', 'have', 'this', 'that', 'with', 'from', 'about', 'tell', 'more'}
    top_words  = [(w, c) for w, c in Counter(all_words).most_common(10) if w not in stop_words][:5]

    return jsonify({
        'logs':          [l.to_dict() for l in logs],
        'total_queries': len(logs),
        'top_questions': [{'word': w, 'count': c} for w, c in top_words]
    })


@admin_bp.route('/chatlog', methods=['DELETE'])
def admin_clear_chatlog():
    """Bulk-delete all chat logs."""
    try:
        db.session.query(ChatbotLog).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'All chat logs cleared'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# MAINTENANCE / SITE CONFIG
# ============================================================

@admin_bp.route('/config', methods=['GET'])
def get_config():
    cfg = SiteConfig.get()
    return jsonify(cfg.to_dict())


@admin_bp.route('/config', methods=['PUT'])
def update_config():
    data = request.get_json()
    cfg  = SiteConfig.get()

    if 'maintenance_mode' in data:
        cfg.maintenance_mode = bool(data['maintenance_mode'])

    if 'maintenance_message' in data:
        cfg.maintenance_message = data['maintenance_message']

    if 'affected_pages' in data:
        cfg.affected_pages = data['affected_pages']   # expects a list of strings

    try:
        db.session.commit()
        return jsonify({'success': True, 'config': cfg.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# REPORTS
# ============================================================

@admin_bp.route('/reports/enquiries', methods=['GET'])
def report_enquiries():
    """Monthly enquiry counts for the past 12 months."""
    rows = db.session.execute(text("""
        SELECT
            TO_CHAR(created_at, 'YYYY-MM') AS month,
            COUNT(*)                        AS total,
            COUNT(*) FILTER (WHERE status = 'won')  AS won,
            COUNT(*) FILTER (WHERE status = 'lost') AS lost,
            SUM(estimated_value)            AS pipeline_value
        FROM enquiries
        WHERE created_at >= NOW() - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)).fetchall()

    return jsonify([dict(r._mapping) for r in rows])


@admin_bp.route('/reports/stock', methods=['GET'])
def report_stock():
    """Stock usage over the past 30 days grouped by product."""
    rows = db.session.execute(text("""
        SELECT
            p.name                          AS product_name,
            SUM(CASE WHEN s.change_qty < 0 THEN ABS(s.change_qty) ELSE 0 END) AS consumed,
            SUM(CASE WHEN s.change_qty > 0 THEN s.change_qty ELSE 0 END)      AS added,
            p.stock                         AS current_stock,
            p.reorder_level
        FROM stock_usage_log s
        JOIN products p ON p.id = s.product_id
        WHERE s.created_at >= NOW() - INTERVAL '30 days'
        GROUP BY p.id, p.name, p.stock, p.reorder_level
        ORDER BY consumed DESC
    """)).fetchall()

    return jsonify([dict(r._mapping) for r in rows])


@admin_bp.route('/reports/production', methods=['GET'])
def report_production():
    """Production order status summary."""
    rows = db.session.execute(text("""
        SELECT
            po.status,
            COUNT(*)             AS count,
            AVG(po.progress)     AS avg_progress,
            SUM(po.quantity)     AS total_units
        FROM production_orders po
        GROUP BY po.status
    """)).fetchall()

    return jsonify([dict(r._mapping) for r in rows])
