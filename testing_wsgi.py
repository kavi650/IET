"""
testing_wsgi.py
Entry point for gunicorn to serve the Testing App on Render.

Flask-SocketIO with async_mode='threading' works correctly with
gunicorn's gthread worker. The socketio object wraps the Flask app
transparently, so we just export the Flask app directly.

Gunicorn command (used in Procfile / render.yaml):
  gunicorn testing_wsgi:app --worker-class gthread --workers 1 --threads 4 --timeout 120
"""
import sys
import os

# Ensure the project root is on the path so `testing_app` package is importable
sys.path.insert(0, os.path.dirname(__file__))

from testing_app.app import app  # noqa: F401 — gunicorn targets `testing_wsgi:app`
