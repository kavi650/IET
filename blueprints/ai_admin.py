"""
blueprints/ai_admin.py
On-demand AI Insight generation for the admin panel using Ollama LLaMA.

  POST /api/admin/ai/generate   → trigger AI analysis (all types or specific)
  GET  /api/admin/ai/status     → Ollama health check

AI analyses DB data and writes AIInsight rows that the admin can read.
"""
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from models import db, Product, ProductionOrder
from models_v3 import AIInsight, TestSession, TestResult, log_activity

ai_admin_bp = Blueprint('ai_admin', __name__, url_prefix='/api/admin/ai')

OLLAMA_URL   = 'http://127.0.0.1:11434/api/generate'
OLLAMA_MODEL = 'llama3'


# ── Ollama helper ───────────────────────────────────────────────

def _call_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Send a prompt to Ollama and return the plain-text response."""
    try:
        import urllib.request
        payload = json.dumps({'model': model, 'prompt': prompt, 'stream': False}).encode()
        req     = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data.get('response', '').strip()
    except Exception as e:
        return f'[Ollama unavailable: {e}]'


def _save_insight(insight_type, title, body, severity='info'):
    """Persist one AI insight row."""
    insight = AIInsight(
        insight_type=insight_type,
        title=title,
        body=body,
        severity=severity,
    )
    db.session.add(insight)
    return insight


# ── Individual analysis functions ───────────────────────────────

def _analyse_stock():
    """Flag products that are at or below reorder level."""
    low = Product.query.filter(Product.stock <= Product.reorder_level).all()
    if not low:
        return

    names = ', '.join(p.name for p in low[:10])
    prompt = (
        f"You are an industrial inventory AI. The following products are at or below "
        f"their reorder level: {names}. "
        f"Provide 2-3 short bullet-point recommendations for the operations team "
        f"to prevent production delays. Be concise and practical."
    )
    body = _call_ollama(prompt)
    severity = 'critical' if len(low) >= 3 else 'warning'
    _save_insight(
        'stock_alert',
        f'{len(low)} Product(s) Below Reorder Level',
        body,
        severity=severity,
    )


def _analyse_production():
    """Suggest improvements based on current production order statuses."""
    orders = ProductionOrder.query.filter(
        ProductionOrder.status.in_(['pending', 'in_progress'])
    ).all()
    if not orders:
        return

    overdue = [
        o for o in orders
        if o.due_date and o.due_date < datetime.utcnow().date() and o.status != 'completed'
    ]
    summary = (
        f"{len(orders)} active orders, {len(overdue)} overdue."
    )
    prompt = (
        f"You are an industrial production AI. Current status: {summary}. "
        f"Give 2-3 practical suggestions to improve production efficiency and reduce delays."
    )
    body     = _call_ollama(prompt)
    severity = 'warning' if overdue else 'info'
    _save_insight(
        'production_suggestion',
        f'Production Status: {len(orders)} Active, {len(overdue)} Overdue',
        body,
        severity=severity,
    )


def _analyse_test_failures():
    """Identify patterns in recent test failures."""
    failed = (TestResult.query
              .join(TestSession)
              .filter(TestSession.result == 'failed')
              .order_by(TestResult.created_at.desc())
              .limit(20).all())

    if not failed:
        return

    # Aggregate: what types of failures are most common?
    leakage_fails = sum(1 for r in failed if r.leakage_within_limit is False)
    pressure_fails= sum(1 for r in failed if r.pressure_hold_ok is False)
    temp_fails    = sum(1 for r in failed if r.temperature_ok is False)

    prompt = (
        f"You are an industrial valve testing AI. In the last {len(failed)} failed tests: "
        f"{leakage_fails} had leakage issues, {pressure_fails} had pressure issues, "
        f"{temp_fails} had temperature issues. "
        f"Provide 2-3 concise recommendations to reduce failure rates."
    )
    body = _call_ollama(prompt)
    _save_insight(
        'test_failure_pattern',
        f'Test Failure Pattern: {len(failed)} Recent Failures Analysed',
        body,
        severity='warning' if len(failed) > 5 else 'info',
    )


def _analyse_demand():
    """Simple demand forecast based on enquiry data."""
    from models import Enquiry
    from sqlalchemy import func

    # Top enquired products in last 90 days
    rows = (
        db.session.query(Product.name, func.count(Enquiry.id).label('cnt'))
        .join(Enquiry, Enquiry.product_id == Product.id)
        .group_by(Product.name)
        .order_by(func.count(Enquiry.id).desc())
        .limit(5).all()
    )
    if not rows:
        return

    top = ', '.join(f"{name} ({cnt})" for name, cnt in rows)
    prompt = (
        f"You are an industrial sales AI. Top requested products: {top}. "
        f"Give 2 short recommendations on stock and production planning."
    )
    body = _call_ollama(prompt)
    _save_insight(
        'demand_forecast',
        f'Top Demand: {rows[0][0]} leads with {rows[0][1]} enquiries',
        body,
        severity='info',
    )


# ── Routes ──────────────────────────────────────────────────────

@ai_admin_bp.route('/generate', methods=['POST'])
def generate_insights():
    """
    Trigger AI insight generation.
    Body: {"types": ["stock_alert", "production_suggestion"]}  (empty = all)
    """
    data        = request.get_json() or {}
    types_req   = data.get('types', [])   # empty list = run all

    all_types = {
        'stock_alert':          _analyse_stock,
        'production_suggestion': _analyse_production,
        'test_failure_pattern': _analyse_test_failures,
        'demand_forecast':      _analyse_demand,
    }

    to_run = {k: v for k, v in all_types.items() if not types_req or k in types_req}

    generated = []
    errors    = []
    for name, fn in to_run.items():
        try:
            fn()
            generated.append(name)
        except Exception as e:
            errors.append({'type': name, 'error': str(e)})

    try:
        log_activity(
            action='generated_ai_insights',
            description=f"Generated: {', '.join(generated)}",
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'success':   True,
        'generated': generated,
        'errors':    errors,
    })


@ai_admin_bp.route('/status', methods=['GET'])
def ollama_status():
    """Quick health check — is Ollama reachable?"""
    try:
        import urllib.request
        urllib.request.urlopen('http://127.0.0.1:11434', timeout=3)
        return jsonify({'ollama': 'online', 'model': OLLAMA_MODEL})
    except Exception:
        return jsonify({'ollama': 'offline', 'model': OLLAMA_MODEL}), 503
