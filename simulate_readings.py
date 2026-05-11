"""
simulate_readings.py
====================
Pushes simulated sensor readings to the Testing App every second.
Usage:
    python simulate_readings.py --session 1 --token YOUR_TOKEN
    python simulate_readings.py --session 1 --token YOUR_TOKEN --duration 120
"""
import argparse, math, random, time, requests

BASE_URL = "http://localhost:8501"


def simulate(session_id: int, token: str, duration: int):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = f"{BASE_URL}/api/tests/sessions/{session_id}/readings"

    print(f"[SIM] Pushing readings to session {session_id} for {duration}s ...")
    print(f"      Open http://localhost:8501/live in your browser.\n")

    for i in range(duration):
        t = i / 10  # time factor

        # Simulated sensor values with slight noise
        pressure    = 80 + 60 * math.sin(t * 0.3) + random.uniform(-3, 3)
        temperature = 35 + 20 * math.sin(t * 0.15) + random.uniform(-1, 1)
        flow_rate   = 100 + 50 * math.cos(t * 0.2) + random.uniform(-5, 5)
        leakage     = max(0, 0.5 + 0.8 * math.sin(t * 0.5) + random.uniform(-0.1, 0.1))

        payload = {
            "pressure_bar":   round(pressure, 2),
            "temperature_c":  round(temperature, 2),
            "flow_rate_lpm":  round(flow_rate, 2),
            "leakage_ml_min": round(leakage, 3),
        }

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=3)
            status = "✓" if r.status_code == 201 else f"✗ {r.status_code}"
            print(f"  [{i+1:03d}] {status}  P={payload['pressure_bar']:7.2f} bar  "
                  f"T={payload['temperature_c']:5.1f}°C  "
                  f"F={payload['flow_rate_lpm']:6.2f} L/min  "
                  f"L={payload['leakage_ml_min']:.3f} mL/min")
        except requests.exceptions.ConnectionError:
            print(f"  [{i+1:03d}] ✗ Cannot connect to {BASE_URL} — is the Testing App running?")

        time.sleep(1)

    print("\n[SIM] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Testiny Live Reading Simulator")
    parser.add_argument("--session",  type=int, required=True, help="Session ID (from the Live Test banner)")
    parser.add_argument("--token",    type=str, required=True, help="Auth token (from browser sessionStorage)")
    parser.add_argument("--duration", type=int, default=60,   help="How many seconds to simulate (default 60)")
    args = parser.parse_args()
    simulate(args.session, args.token, args.duration)
