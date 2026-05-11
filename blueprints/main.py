"""
blueprints/main.py
Public-facing page routes and public APIs (products, categories, contact, chat).
All routes that existed in the original app.py are preserved here unchanged.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, Category, Product, Enquiry, ChatbotLog
from chatbot import get_chat_response

main_bp = Blueprint('main', __name__)


# ============================================================
# PUBLIC PAGE ROUTES
# ============================================================

@main_bp.route('/')
def home():
    return render_template('index.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/products')
def products_page():
    return render_template('products.html')


@main_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    return render_template('product_detail.html', product_id=product_id)


@main_bp.route('/compare')
def compare():
    return render_template('compare.html')


@main_bp.route('/chat')
def chat():
    return render_template('chatbot.html')


@main_bp.route('/contact')
def contact():
    return render_template('contact.html')


@main_bp.route('/admin')
def admin():
    return render_template('admin.html')


# ── New frontend pages (STEP 6) ──────────────────────────────

@main_bp.route('/process')
def process():
    return render_template('process.html')


@main_bp.route('/projects')
def projects():
    return render_template('projects.html')


@main_bp.route('/industries')
def industries():
    return render_template('industries.html')


@main_bp.route('/downloads')
def downloads():
    return render_template('downloads.html')


# ============================================================
# PUBLIC API ROUTES  (unchanged from original)
# ============================================================

@main_bp.route('/api/products', methods=['GET'])
def api_products():
    """Get all products, optionally filtered by category or search term."""
    category_id = request.args.get('category_id', type=int)
    search      = request.args.get('search', '')

    query = Product.query

    if category_id:
        query = query.filter_by(category_id=category_id)

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.all()
    return jsonify([p.to_card_dict() for p in products])


@main_bp.route('/api/product/<int:product_id>', methods=['GET'])
def api_product(product_id):
    """Get a single product with full details and specifications."""
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())


@main_bp.route('/api/categories', methods=['GET'])
def api_categories():
    """Get all product categories."""
    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories])


@main_bp.route('/api/contact', methods=['POST'])
def api_contact():
    """Save a contact/enquiry form submission."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    for field in ['name', 'email', 'message']:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    enquiry = Enquiry(
        name    = data['name'],
        email   = data['email'],
        company = data.get('company', ''),
        phone   = data.get('phone', ''),
        message = data['message'],
        status  = 'new'
    )

    try:
        db.session.add(enquiry)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Enquiry submitted successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/chat', methods=['POST'])
def api_chat():
    """AI chatbot endpoint using Ollama."""
    data = request.get_json()

    if not data or not data.get('query'):
        return jsonify({'error': 'Query is required'}), 400

    query  = data['query']
    result = get_chat_response(
        query,
        ollama_base_url=current_app.config['OLLAMA_BASE_URL'],
        model=current_app.config['OLLAMA_MODEL']
    )

    try:
        log = ChatbotLog(query=query, response=result['response'])
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({'response': result['response'], 'source': result['source']})
