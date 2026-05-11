"""
testing_app/app.py
Industrial Testing Software — standalone Flask app on port 8501.
Shares the same PostgreSQL database as the main app.
Access is gated by token verification against the main app.
"""
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from testing_app.config import TestingConfig
from testing_app.extensions import db

socketio = SocketIO()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(TestingConfig)
    CORS(app)
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')

    # ── Register blueprints ───────────────────────────────────
    from testing_app.blueprints.dashboard  import dashboard_bp
    from testing_app.blueprints.sessions   import sessions_bp
    from testing_app.blueprints.readings   import readings_bp
    from testing_app.blueprints.results    import results_bp
    from testing_app.blueprints.analysis   import analysis_bp
    from testing_app.blueprints.logs       import logs_bp
    from testing_app.blueprints.settings   import settings_bp
    from testing_app.blueprints.pages      import pages_bp
    from testing_app.blueprints.ai_chat    import ai_chat_bp

    for bp in [dashboard_bp, sessions_bp, readings_bp, results_bp,
               analysis_bp, logs_bp, settings_bp, pages_bp, ai_chat_bp]:
        app.register_blueprint(bp)

    # ── SocketIO events ───────────────────────────────────────
    from testing_app.realtime import register_events
    register_events(socketio)

    return app


app      = create_app()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8501, debug=True, use_reloader=False)
