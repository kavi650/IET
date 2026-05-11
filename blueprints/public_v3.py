"""
blueprints/public_v3.py
New public-facing page routes for Platform v3:
  /process           → Company workflow page
  /projects          → Case studies
  /industries        → Industries served
  /downloads         → File download centre
  /testing-access    → Access request form page

Also serves API data for the above pages.
"""
from flask import Blueprint, jsonify, render_template, request, send_from_directory, abort
from models import db
from models_v3 import Project, Download, Industry

public_v3_bp = Blueprint('public_v3', __name__)


# ── Page Routes ────────────────────────────────────────────────

@public_v3_bp.route('/process')
def process_page():
    return render_template('process.html')


@public_v3_bp.route('/projects')
def projects_page():
    return render_template('projects.html')


@public_v3_bp.route('/industries')
def industries_page():
    return render_template('industries.html')


@public_v3_bp.route('/downloads')
def downloads_page():
    return render_template('downloads.html')


@public_v3_bp.route('/testing-access')
def testing_access_page():
    return render_template('testing_access.html')


# ── API: Projects ──────────────────────────────────────────────

@public_v3_bp.route('/api/projects', methods=['GET'])
def api_projects():
    industry = request.args.get('industry')
    q = Project.query.filter_by(is_published=True)
    if industry:
        q = q.filter_by(industry=industry)
    items = q.order_by(Project.sort_order.asc(), Project.created_at.desc()).all()
    return jsonify({'projects': [p.to_dict() for p in items], 'total': len(items)})


@public_v3_bp.route('/api/projects/<int:project_id>', methods=['GET'])
def api_project_detail(project_id):
    p = Project.query.get_or_404(project_id)
    if not p.is_published:
        abort(404)
    return jsonify(p.to_dict())


# ── API: Industries ────────────────────────────────────────────

@public_v3_bp.route('/api/industries', methods=['GET'])
def api_industries():
    items = Industry.query.filter_by(is_active=True).order_by(Industry.sort_order).all()
    return jsonify({'industries': [i.to_dict() for i in items]})


# ── API: Downloads ─────────────────────────────────────────────

@public_v3_bp.route('/api/downloads', methods=['GET'])
def api_downloads():
    category = request.args.get('category')
    q = Download.query.filter_by(is_published=True)
    if category:
        q = q.filter_by(category=category)
    items = q.order_by(Download.created_at.desc()).all()
    return jsonify({
        'downloads': [d.to_dict() for d in items],
        'total':     len(items),
        'categories': Download.VALID_CATEGORIES,
    })


@public_v3_bp.route('/api/downloads/<int:dl_id>/track', methods=['POST'])
def api_track_download(dl_id):
    """Increment download counter when user clicks download."""
    dl = Download.query.get_or_404(dl_id)
    dl.download_count += 1
    try:
        db.session.commit()
        return jsonify({'success': True, 'file_url': dl.file_url})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
