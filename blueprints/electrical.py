"""
blueprints/electrical.py
Electrical department: test records per production order.
Test status: pending → passed / failed
"""

from flask import Blueprint, jsonify, request
from models import db, ElectricalTest, ProductionOrder
from datetime import date

electrical_bp = Blueprint('electrical', __name__, url_prefix='/api/electrical')


# ============================================================
# ELECTRICAL TEST RECORDS
# ============================================================

@electrical_bp.route('/', methods=['GET'])
def list_tests():
    """List all electrical test records with optional status filter."""
    status   = request.args.get('status')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = ElectricalTest.query

    if status and status in ElectricalTest.VALID_STATUSES:
        query = query.filter_by(test_status=status)

    pagination = query.order_by(ElectricalTest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'tests': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page':  page
    })


@electrical_bp.route('/<int:test_id>', methods=['GET'])
def get_test(test_id):
    test = ElectricalTest.query.get_or_404(test_id)
    return jsonify(test.to_dict())


@electrical_bp.route('/by-order/<int:production_id>', methods=['GET'])
def get_by_order(production_id):
    """Get electrical test for a specific production order."""
    test = ElectricalTest.query.filter_by(production_id=production_id).first()
    if not test:
        return jsonify({'error': 'No electrical test for this production order'}), 404
    return jsonify(test.to_dict())


@electrical_bp.route('/', methods=['POST'])
def create_test():
    """Create a new electrical test record for a production order."""
    data = request.get_json()

    if not data or not data.get('production_id'):
        return jsonify({'error': 'production_id is required'}), 400

    # Validate production order exists
    ProductionOrder.query.get_or_404(data['production_id'])

    # Check duplicate
    if ElectricalTest.query.filter_by(production_id=data['production_id']).first():
        return jsonify({'error': 'Electrical test already exists for this production order'}), 409

    test = ElectricalTest(
        production_id = data['production_id'],
        panel_type    = data.get('panel_type', ''),
        plc_type      = data.get('plc_type', ''),
        voltage       = data.get('voltage', ''),
        test_status   = data.get('test_status', 'pending'),
        remarks       = data.get('remarks', ''),
        tested_by     = data.get('tested_by', ''),
        test_date     = data.get('test_date')
    )

    try:
        db.session.add(test)
        db.session.commit()
        return jsonify({'success': True, 'test': test.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@electrical_bp.route('/<int:test_id>', methods=['PUT'])
def update_test(test_id):
    """Update test details or result."""
    test = ElectricalTest.query.get_or_404(test_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'test_status' in data:
        if data['test_status'] not in ElectricalTest.VALID_STATUSES:
            return jsonify({'error': 'Invalid test_status'}), 400
        test.test_status = data['test_status']

    if 'panel_type' in data:
        test.panel_type = data['panel_type']
    if 'plc_type' in data:
        test.plc_type = data['plc_type']
    if 'voltage' in data:
        test.voltage = data['voltage']
    if 'remarks' in data:
        test.remarks = data['remarks']
    if 'tested_by' in data:
        test.tested_by = data['tested_by']
    if 'test_date' in data:
        test.test_date = data['test_date']

    try:
        db.session.commit()
        return jsonify({'success': True, 'test': test.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@electrical_bp.route('/<int:test_id>', methods=['DELETE'])
def delete_test(test_id):
    test = ElectricalTest.query.get_or_404(test_id)

    try:
        db.session.delete(test)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
