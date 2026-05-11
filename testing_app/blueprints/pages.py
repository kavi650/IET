"""testing_app/blueprints/pages.py — HTML page routes for the testing software UI."""
from flask import Blueprint, render_template, redirect, url_for, request

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    return redirect(url_for('pages.dashboard'))


@pages_bp.route('/login')
def login():
    return redirect(url_for('pages.dashboard'))


@pages_bp.route('/dashboard')
def dashboard():
    return render_template('testing/dashboard.html', active='dashboard')


@pages_bp.route('/live')
def live_test():
    return render_template('testing/live_test.html', active='live')


@pages_bp.route('/analysis')
def analysis():
    session_id = request.args.get('session_id')
    return render_template('testing/analysis.html', session_id=session_id, active='analysis')


@pages_bp.route('/results')
def results():
    return render_template('testing/results.html', active='results')


@pages_bp.route('/logs')
def logs():
    return render_template('testing/logs.html', active='logs')


@pages_bp.route('/ai-assistant')
def ai_assistant():
    return render_template('testing/ai_assistant.html', active='ai')


@pages_bp.route('/settings')
def settings():
    return render_template('testing/settings.html', active='settings')


@pages_bp.route('/access')
def access():
    return render_template('testing/access.html', active='access')


@pages_bp.route('/access/request')
def access_request():
    return render_template('testing/access_request.html', active='request')
