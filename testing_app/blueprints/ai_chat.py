"""
testing_app/blueprints/ai_chat.py
Ollama AI chat endpoint for the testing software.
  POST /api/tests/ai/chat   → send a prompt, get a response
  GET  /api/admin/ai/status → Ollama health (re-exported here for the testing app)
"""
import json
import urllib.request
from flask import Blueprint, jsonify, request, current_app
from testing_app.auth import require_token

ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/api/tests/ai')

SYSTEM_PROMPT = """You are an expert industrial testing engineer AI assistant for Testiny Equipments.
You specialise in hydraulic, pneumatic, water, air, and gas valve testing.
You interpret test data (pressure, temperature, flow rate, leakage) and provide concise, technical, actionable responses.
When analysing sessions, focus on safety, compliance, and practical recommendations.
Keep responses clear and professional. Use bullet points for recommendations.
Do NOT speculate beyond the data provided."""


def _call_ollama(prompt: str) -> str:
    """Send prompt to Ollama and return the plain-text response."""
    ollama_url   = current_app.config.get('OLLAMA_URL', 'http://127.0.0.1:11434') + '/api/generate'
    model        = current_app.config.get('OLLAMA_MODEL', 'llama3')
    full_prompt  = f"{SYSTEM_PROMPT}\n\nUser: {prompt}\nAssistant:"

    payload = json.dumps({
        'model':  model,
        'prompt': full_prompt,
        'stream': False,
        'options': { 'temperature': 0.3, 'num_predict': 512 },
    }).encode()

    req = urllib.request.Request(
        ollama_url,
        data=payload,
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
            return data.get('response', '').strip()
    except urllib.error.URLError:
        return '⚠️ Ollama is offline. Start it with: `ollama serve`'
    except Exception as e:
        return f'⚠️ AI error: {str(e)}'


@ai_chat_bp.route('/chat', methods=['POST'])
@require_token
def chat():
    """Main chat endpoint — send any prompt, get Ollama response."""
    data   = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'prompt is required'}), 400
    response = _call_ollama(prompt)
    return jsonify({ 'response': response })


@ai_chat_bp.route('/analyse-session/<int:session_id>', methods=['POST'])
@require_token
def analyse_session(session_id):
    """
    Auto-generates an AI analysis report for a completed test session.
    Saves the result to TestResult.ai_summary.
    """
    from testing_app.extensions import db
    from testing_app.models import TestSession, TestResult

    session = TestSession.query.get_or_404(session_id)
    result  = session.result_record

    if not result:
        return jsonify({'error': 'No result record found. Complete the session first.'}), 404

    def _f(v): return float(v) if v is not None else None

    prompt = f"""Analyse this completed valve test:
Session: {session.session_code}
Valve ID: {session.valve_id or 'N/A'} | Type: {session.valve_type or 'N/A'} | Size: {session.valve_size or 'N/A'}
Test Type: {session.test_type} | Medium: {session.medium}
Target Pressure: {_f(session.target_pressure)} bar | Target Duration: {session.target_duration}s

Results:
- Max Pressure: {_f(result.max_pressure_bar)} bar (limit: {_f(result.pressure_limit_bar)} bar)
- Avg Pressure: {_f(result.avg_pressure_bar)} bar
- Max Temperature: {_f(result.max_temperature_c)} °C
- Max Leakage: {_f(result.max_leakage_ml_min)} mL/min (limit: {_f(result.leakage_limit_ml_min)} mL/min)
- Avg Flow Rate: {_f(result.avg_flow_rate_lpm)} L/min
- Duration Achieved: {result.duration_achieved_sec}s
- Pressure Hold OK: {result.pressure_hold_ok}
- Leakage Within Limit: {result.leakage_within_limit}
- Temperature OK: {result.temperature_ok}
- Overall Result: {session.result}

Provide:
1. A 2-sentence technical summary of the test.
2. Any anomalies or concerns (bullet points).
3. Recommendation (1-2 sentences).
Keep it concise and technical."""

    ai_response = _call_ollama(prompt)

    # Detect anomalies from response keywords (simple heuristic)
    anomalies = []
    lower = ai_response.lower()
    if 'leakage' in lower and ('exceed' in lower or 'high' in lower):
        anomalies.append('Elevated leakage detected')
    if 'pressure' in lower and ('drop' in lower or 'unstable' in lower):
        anomalies.append('Pressure instability noted')
    if 'temperature' in lower and ('high' in lower or 'exceed' in lower):
        anomalies.append('Temperature concern noted')

    result.ai_summary    = ai_response
    result.ai_anomalies  = anomalies
    result.ai_confidence = 0.78   # static for now; real scoring needs a trained model

    try:
        db.session.commit()
        return jsonify({
            'success':      True,
            'ai_summary':   ai_response,
            'ai_anomalies': anomalies,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@ai_chat_bp.route('/status', methods=['GET'])
def ai_status():
    """Testing app's own Ollama status check."""
    try:
        urllib.request.urlopen('http://127.0.0.1:11434', timeout=3)
        model = current_app.config.get('OLLAMA_MODEL', 'llama3')
        return jsonify({'ollama': 'online', 'model': model})
    except Exception:
        return jsonify({'ollama': 'offline', 'model': None}), 503
