"""
combined_app.py
Mounts both Flask apps on the same domain:
  /         → main app (iet-seven.vercel.app)
  /testing  → testing app (iet-seven.vercel.app/testing/...)
"""
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from app import app as main_app
from testing_app.app import app as testing_app

# Mount testing app under /testing prefix.
# DispatcherMiddleware strips the prefix and sets SCRIPT_NAME so
# Flask's url_for() and redirect() generate correct /testing/... URLs.
app = DispatcherMiddleware(main_app, {
    '/testing': testing_app,
})
