"""
testing_app/app.py
Industrial Testing Software — standalone Flask app.
Works as a package (local dev / Railway) and standalone (Vercel).
"""
import os
from flask import Flask
from flask_cors import CORS

# ── Dual-mode imports ─────────────────────────────────────────
# Works when called as 'testing_app' package OR as standalone root
try:
    from testing_app.config import TestingConfig
    from testing_app.extensions import db
except ImportError:
    from config import TestingConfig       # noqa: F401
    from extensions import db             # noqa: F401

# ── SocketIO (disabled on Vercel — no persistent WS support) ──
_IS_VERCEL = os.getenv('VERCEL') == '1'

if not _IS_VERCEL:
    from flask_socketio import SocketIO
    socketio = SocketIO()
else:
    socketio = None


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(TestingConfig)
    CORS(app)
    db.init_app(app)

    if not _IS_VERCEL and socketio is not None:
        socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')

    # ── Register blueprints ───────────────────────────────────
    try:
        from testing_app.blueprints.dashboard  import dashboard_bp
        from testing_app.blueprints.sessions   import sessions_bp
        from testing_app.blueprints.readings   import readings_bp
        from testing_app.blueprints.results    import results_bp
        from testing_app.blueprints.analysis   import analysis_bp
        from testing_app.blueprints.logs       import logs_bp
        from testing_app.blueprints.settings   import settings_bp
        from testing_app.blueprints.pages      import pages_bp
        from testing_app.blueprints.ai_chat    import ai_chat_bp
    except ImportError:
        from blueprints.dashboard  import dashboard_bp
        from blueprints.sessions   import sessions_bp
        from blueprints.readings   import readings_bp
        from blueprints.results    import results_bp
        from blueprints.analysis   import analysis_bp
        from blueprints.logs       import logs_bp
        from blueprints.settings   import settings_bp
        from blueprints.pages      import pages_bp
        from blueprints.ai_chat    import ai_chat_bp

    for bp in [dashboard_bp, sessions_bp, readings_bp, results_bp,
               analysis_bp, logs_bp, settings_bp, pages_bp, ai_chat_bp]:
        app.register_blueprint(bp)

    # ── SocketIO events (skip on Vercel) ──────────────────────
    if not _IS_VERCEL and socketio is not None:
        try:
            from testing_app.realtime import register_events
        except ImportError:
            from realtime import register_events
        register_events(socketio)

    # ── Auto-init DB (non-fatal on Vercel cold start) ────────
    try:
        with app.app_context():
            db.create_all()
    except Exception as _e:
        print(f'⚠️  DB init skipped at startup: {_e}')

    # ── Lazy DB init on first request (Vercel fallback) ──────
    _db_done = {'done': False}

    @app.before_request
    def ensure_db():
        if not _db_done['done']:
            try:
                db.create_all()
                _db_done['done'] = True
            except Exception as e:
                print(f'⚠️  DB init on request failed: {e}')

    return app


app = create_app()


if __name__ == '__main__':
    if socketio:
        socketio.run(app, host='0.0.0.0', port=8501, debug=True, use_reloader=False)
    else:
        app.run(host='0.0.0.0', port=8501, debug=True)
