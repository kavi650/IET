"""Copy generated product images to static/images directory."""
import shutil
import os

SRC = r"C:\Users\KAVIYARASU\.gemini\antigravity\brain\b35f9400-769f-4e08-ae43-9f088f0d095f"
DST = r"d:\Teslead\static\images"

os.makedirs(DST, exist_ok=True)

files = {
    "hero_bg_1776869233729.png": "hero_bg.jpg",
    "pump_test_rig_1776869253038.png": "pump_test_rig.jpg",
    "valve_test_bench_1776869275706.png": "valve_test_bench.jpg",
    "hydraulic_power_pack_1776869297100.png": "hydraulic_power_pack.jpg",
    "pressure_testing_1776869327032.png": "pressure_testing.jpg",
    "hydraulic_cylinders_1776869350248.png": "hydraulic_cylinders.jpg",
    "pneumatic_control_1776869371059.png": "pneumatic_control.jpg",
}

for src_name, dst_name in files.items():
    src = os.path.join(SRC, src_name)
    dst = os.path.join(DST, dst_name)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"✅ Copied {dst_name}")
    else:
        print(f"❌ Not found: {src_name}")

print("\nDone! Restart the Flask server to see images.")
