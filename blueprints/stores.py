"""
blueprints/stores.py
Stores department: stock management for products.
APIs: add stock, reduce stock, list low-stock items.
"""

from flask import Blueprint, jsonify, request
from models import db, Product, StockUsageLog

stores_bp = Blueprint('stores', __name__, url_prefix='/api/stores')


# ============================================================
# INVENTORY LIST
# ============================================================

@stores_bp.route('/inventory', methods=['GET'])
def inventory():
    """List all products with stock levels. Supports search + low-stock filter."""
    search   = request.args.get('search', '')
    low_only = request.args.get('low_stock', 'false').lower() == 'true'

    query = Product.query

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    if low_only:
        query = query.filter(Product.stock < Product.reorder_level)

    products = query.order_by(Product.name).all()

    return jsonify([{
        'id':            p.id,
        'name':          p.name,
        'category_name': p.category.name if p.category else 'N/A',
        'stock':         p.stock,
        'reorder_level': p.reorder_level,
        'is_low_stock':  p.is_low_stock,
        'image_url':     p.image_url,
    } for p in products])


@stores_bp.route('/low-stock', methods=['GET'])
def low_stock():
    """Quick summary of low-stock items for dashboard card."""
    items = Product.query.filter(Product.stock < Product.reorder_level).all()
    return jsonify({
        'count': len(items),
        'items': [{'id': p.id, 'name': p.name, 'stock': p.stock, 'reorder_level': p.reorder_level}
                  for p in items]
    })


# ============================================================
# STOCK ADJUSTMENT
# ============================================================

@stores_bp.route('/stock/<int:product_id>/add', methods=['POST'])
def add_stock(product_id):
    """Add stock to a product."""
    product = Product.query.get_or_404(product_id)
    data    = request.get_json()

    qty = data.get('quantity')
    if not qty or not isinstance(qty, int) or qty <= 0:
        return jsonify({'error': 'quantity must be a positive integer'}), 400

    product.stock += qty

    log = StockUsageLog(
        product_id   = product.id,
        change_qty   = qty,
        reason       = data.get('reason', 'manual_add'),
        reference_id = data.get('reference_id')
    )

    try:
        db.session.add(log)
        db.session.commit()
        return jsonify({
            'success':   True,
            'new_stock': product.stock,
            'is_low_stock': product.is_low_stock
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@stores_bp.route('/stock/<int:product_id>/reduce', methods=['POST'])
def reduce_stock(product_id):
    """Reduce stock from a product."""
    product = Product.query.get_or_404(product_id)
    data    = request.get_json()

    qty = data.get('quantity')
    if not qty or not isinstance(qty, int) or qty <= 0:
        return jsonify({'error': 'quantity must be a positive integer'}), 400

    if product.stock < qty:
        return jsonify({'error': f'Insufficient stock. Available: {product.stock}'}), 400

    product.stock -= qty

    log = StockUsageLog(
        product_id   = product.id,
        change_qty   = -qty,           # negative = consumed
        reason       = data.get('reason', 'manual_reduce'),
        reference_id = data.get('reference_id')
    )

    try:
        db.session.add(log)
        db.session.commit()
        return jsonify({
            'success':      True,
            'new_stock':    product.stock,
            'is_low_stock': product.is_low_stock
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# STOCK USAGE LOG
# ============================================================

@stores_bp.route('/log', methods=['GET'])
def stock_log():
    """Paginated stock usage audit log."""
    product_id = request.args.get('product_id', type=int)
    page       = request.args.get('page', 1, type=int)
    per_page   = request.args.get('per_page', 30, type=int)

    query = StockUsageLog.query

    if product_id:
        query = query.filter_by(product_id=product_id)

    pagination = query.order_by(StockUsageLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'logs':  [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page':  page
    })
