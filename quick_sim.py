"""
quick_sim.py — No token needed for local dev testing.
Just run:  python quick_sim.py
It will find the latest running session and push readings directly via DB.
"""
import math, random, time, sys, os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from testing_app.config import TestingConfig
from flask import Flask
from testing_app.extensions import db
from testing_app.models import TestSession, TestReading
from datetime import datetime

app = Flask(__name__)
app.config.from_object(TestingConfig)
db.init_app(app)

INTERVAL = 1      # seconds between readings
DURATION  = 300   # total seconds (5 min)

with app.app_context():
    # Find latest running session
    session = TestSession.query.filter_by(status='running').order_by(TestSession.id.desc()).first()
    if not session:
        print("❌  No running session found. Go to http://localhost:8501/live and start a test first.")
        sys.exit(1)

    print(f"✅  Found session: {session.session_code} (ID={session.id})")
    print(f"    Pushing {DURATION} readings at 1/sec. Open http://localhost:8501/live\n")

    for i in range(DURATION):
        t = i / 10.0

        pressure    = 80  + 60  * math.sin(t * 0.3)  + random.uniform(-3, 3)
        temperature = 35  + 20  * math.sin(t * 0.15) + random.uniform(-1, 1)
        flow_rate   = 100 + 50  * math.cos(t * 0.2)  + random.uniform(-5, 5)
        leakage     = max(0, 0.5 + 0.8 * math.sin(t * 0.5) + random.uniform(-0.1, 0.1))

        # Alert thresholds (from defaults)
        p_warn, p_crit = 212.5, 250.0
        t_warn, t_crit = 65.0,  80.0
        l_warn, l_crit = 2.0,   5.0

        def alert(v, w, c):
            if v is None: return 'ok'
            return 'critical' if v >= c else ('warning' if v >= w else 'ok')

        r = TestReading(
            session_id     = session.id,
            recorded_at    = datetime.utcnow(),
            pressure_bar   = round(pressure,   2),
            temperature_c  = round(temperature,2),
            flow_rate_lpm  = round(flow_rate,  2),
            leakage_ml_min = round(leakage,    3),
            pressure_alert = alert(pressure,    p_warn, p_crit),
            temp_alert     = alert(temperature, t_warn, t_crit),
            leakage_alert  = alert(leakage,     l_warn, l_crit),
        )

        db.session.add(r)
        db.session.commit()

        # Emit via SocketIO
        try:
            from testing_app.app import socketio
            socketio.emit('new_reading', r.to_dict(), room=f'session_{session.id}')
            if 'critical' in [r.pressure_alert, r.temp_alert, r.leakage_alert]:
                socketio.emit('critical_alert', r.to_dict(), room=f'session_{session.id}')
        except Exception:
            pass  # SocketIO not available in this process; readings still saved to DB

        p_sym = '🔴' if r.pressure_alert == 'critical' else ('🟡' if r.pressure_alert == 'warning' else '🟢')
        print(f"  [{i+1:03d}] {p_sym}  P={pressure:7.2f} bar  T={temperature:5.1f}°C  "
              f"F={flow_rate:6.2f} L/min  L={leakage:.3f} mL/min")

        time.sleep(INTERVAL)

    print("\n✅  Simulation complete.")
