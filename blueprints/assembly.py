"""
blueprints/assembly.py
Assembly department: checklist management per production order.
Progress is auto-calculated from checklist item completion.
"""

from flask import Blueprint, jsonify, request
from models import db, Assembly, ProductionOrder

assembly_bp = Blueprint('assembly', __name__, url_prefix='/api/assembly')


# ============================================================
# ASSEMBLY RECORDS
# ============================================================

@assembly_bp.route('/', methods=['GET'])
def list_assemblies():
    """List all assembly records with optional status filter."""
    status   = request.args.get('status')
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Assembly.query

    if status and status in Assembly.VALID_STATUSES:
        query = query.filter_by(status=status)

    pagination = query.order_by(Assembly.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'assemblies': [a.to_dict() for a in pagination.items],
        'total':      pagination.total,
        'pages':      pagination.pages,
        'page':       page
    })


@assembly_bp.route('/<int:assembly_id>', methods=['GET'])
def get_assembly(assembly_id):
    assembly = Assembly.query.get_or_404(assembly_id)
    return jsonify(assembly.to_dict())


@assembly_bp.route('/by-order/<int:production_id>', methods=['GET'])
def get_by_order(production_id):
    """Get assembly record for a specific production order."""
    assembly = Assembly.query.filter_by(production_id=production_id).first()
    if not assembly:
        return jsonify({'error': 'No assembly record for this production order'}), 404
    return jsonify(assembly.to_dict())


@assembly_bp.route('/', methods=['POST'])
def create_assembly():
    """
    Create a new assembly checklist for a production order.
    Checklist format: [{"item": "Motor", "done": false}, ...]
    """
    data = request.get_json()

    if not data or not data.get('production_id'):
        return jsonify({'error': 'production_id is required'}), 400

    # Validate production order exists
    ProductionOrder.query.get_or_404(data['production_id'])

    # Check for duplicate
    if Assembly.query.filter_by(production_id=data['production_id']).first():
        return jsonify({'error': 'Assembly record already exists for this production order'}), 409

    checklist = data.get('checklist', [])
    assembly  = Assembly(
        production_id = data['production_id'],
        checklist     = checklist,
        assigned_to   = data.get('assigned_to', ''),
        notes         = data.get('notes', '')
    )
    assembly.recalculate_progress()

    try:
        db.session.add(assembly)
        db.session.commit()
        return jsonify({'success': True, 'assembly': assembly.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@assembly_bp.route('/<int:assembly_id>/checklist', methods=['PUT'])
def update_checklist(assembly_id):
    """
    Replace the full checklist (used when editing all items at once).
    Progress is auto-recalculated.
    """
    assembly  = Assembly.query.get_or_404(assembly_id)
    data      = request.get_json()
    checklist = data.get('checklist')

    if checklist is None or not isinstance(checklist, list):
        return jsonify({'error': 'checklist must be a list'}), 400

    assembly.checklist = checklist
    assembly.recalculate_progress()

    try:
        db.session.commit()
        return jsonify({'success': True, 'assembly': assembly.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@assembly_bp.route('/<int:assembly_id>/toggle/<int:item_index>', methods=['PUT'])
def toggle_item(assembly_id, item_index):
    """
    Toggle the 'done' state of a single checklist item by its index.
    This is the primary interaction: clicking a checkbox in the UI.
    """
    assembly = Assembly.query.get_or_404(assembly_id)

    checklist = list(assembly.checklist or [])

    if item_index < 0 or item_index >= len(checklist):
        return jsonify({'error': f'Item index {item_index} out of range'}), 400

    checklist[item_index]['done'] = not checklist[item_index].get('done', False)
    assembly.checklist = checklist
    assembly.recalculate_progress()

    try:
        db.session.commit()
        return jsonify({
            'success':  True,
            'item':     checklist[item_index],
            'progress': assembly.progress,
            'status':   assembly.status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@assembly_bp.route('/<int:assembly_id>', methods=['PUT'])
def update_assembly(assembly_id):
    """Update assigned_to or notes."""
    assembly = Assembly.query.get_or_404(assembly_id)
    data     = request.get_json()

    if 'assigned_to' in data:
        assembly.assigned_to = data['assigned_to']
    if 'notes' in data:
        assembly.notes = data['notes']

    try:
        db.session.commit()
        return jsonify({'success': True, 'assembly': assembly.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
