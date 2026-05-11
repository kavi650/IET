"""
blueprints/production.py
Production department: manage production orders.
Orders are created automatically when a sales enquiry is marked 'won',
but can also be created manually here.
"""

from flask import Blueprint, jsonify, request
from models import db, ProductionOrder, Assembly, ElectricalTest

production_bp = Blueprint('production', __name__, url_prefix='/api/production')


# ============================================================
# PRODUCTION ORDERS — CRUD
# ============================================================

@production_bp.route('/orders', methods=['GET'])
def list_orders():
    """List all production orders with optional filters and pagination."""
    status   = request.args.get('status')
    search   = request.args.get('search', '')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = ProductionOrder.query

    if status and status in ProductionOrder.VALID_STATUSES:
        query = query.filter_by(status=status)

    if search:
        # Outer-join products to search by product name
        from models import Product
        query = query.outerjoin(Product, ProductionOrder.product_id == Product.id)\
                     .filter(Product.name.ilike(f'%{search}%'))

    pagination = query.order_by(ProductionOrder.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'orders': [o.to_dict() for o in pagination.items],
        'total':  pagination.total,
        'pages':  pagination.pages,
        'page':   page
    })


@production_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a single production order with its assembly and electrical test."""
    order = ProductionOrder.query.get_or_404(order_id)

    data = order.to_dict()
    data['assembly']        = order.assembly.to_dict() if order.assembly else None
    data['electrical_test'] = order.electrical_test.to_dict() if order.electrical_test else None

    return jsonify(data)


@production_bp.route('/orders', methods=['POST'])
def create_order():
    """Manually create a production order."""
    data = request.get_json()

    if not data or not data.get('product_id'):
        return jsonify({'error': 'product_id is required'}), 400

    order = ProductionOrder(
        product_id = data['product_id'],
        enquiry_id = data.get('enquiry_id'),
        quantity   = data.get('quantity', 1),
        start_date = data.get('start_date'),
        due_date   = data.get('due_date'),
        status     = data.get('status', 'pending'),
        progress   = data.get('progress', 0),
        notes      = data.get('notes', '')
    )

    try:
        db.session.add(order)
        db.session.commit()
        return jsonify({'success': True, 'order': order.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@production_bp.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """Update production order status or progress."""
    order = ProductionOrder.query.get_or_404(order_id)
    data  = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'status' in data:
        if data['status'] not in ProductionOrder.VALID_STATUSES:
            return jsonify({'error': 'Invalid status'}), 400
        order.status = data['status']

    if 'progress' in data:
        progress = int(data['progress'])
        if not (0 <= progress <= 100):
            return jsonify({'error': 'progress must be 0–100'}), 400
        order.progress = progress

    if 'start_date' in data:
        order.start_date = data['start_date']
    if 'due_date' in data:
        order.due_date = data['due_date']
    if 'notes' in data:
        order.notes = data['notes']
    if 'quantity' in data:
        order.quantity = data['quantity']

    try:
        db.session.commit()
        return jsonify({'success': True, 'order': order.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@production_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = ProductionOrder.query.get_or_404(order_id)

    try:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# SUMMARY (for dashboard)
# ============================================================

@production_bp.route('/summary', methods=['GET'])
def summary():
    """Quick counts grouped by status."""
    from sqlalchemy import func
    rows = (
        db.session.query(ProductionOrder.status, func.count(ProductionOrder.id))
        .group_by(ProductionOrder.status)
        .all()
    )
    counts = {s: 0 for s in ProductionOrder.VALID_STATUSES}
    for status, count in rows:
        counts[status] = count
    return jsonify(counts)
