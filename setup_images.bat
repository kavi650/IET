@echo off
echo ============================================
echo  Teslead Equipments - Image Setup Script
echo ============================================
echo.
echo Copying generated images to static/images...
echo.

set SRC=C:\Users\KAVIYARASU\.gemini\antigravity\brain\b35f9400-769f-4e08-ae43-9f088f0d095f

copy "%SRC%\hero_bg_1776869233729.png" "d:\Teslead\static\images\hero_bg.jpg" /Y
copy "%SRC%\pump_test_rig_1776869253038.png" "d:\Teslead\static\images\pump_test_rig.jpg" /Y
copy "%SRC%\valve_test_bench_1776869275706.png" "d:\Teslead\static\images\valve_test_bench.jpg" /Y
copy "%SRC%\hydraulic_power_pack_1776869297100.png" "d:\Teslead\static\images\hydraulic_power_pack.jpg" /Y
copy "%SRC%\pressure_testing_1776869327032.png" "d:\Teslead\static\images\pressure_testing.jpg" /Y
copy "%SRC%\hydraulic_cylinders_1776869350248.png" "d:\Teslead\static\images\hydraulic_cylinders.jpg" /Y
copy "%SRC%\pneumatic_control_1776869371059.png" "d:\Teslead\static\images\pneumatic_control.jpg" /Y

echo.
echo ============================================
echo  Images copied successfully!
echo ============================================
echo.
echo Next steps:
echo   1. Create PostgreSQL database: createdb teslead_db
echo   2. Run schema: psql -d teslead_db -f schema.sql
echo   3. Install Python deps: pip install -r requirements.txt
echo   4. Start server: python app.py
echo   5. Open http://localhost:5000
echo.
pause
