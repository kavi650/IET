"""
seed_data.py — Insert sample Assembly & ElectricalTest records
Run: python seed_data.py

- Reads existing production_orders and creates one Assembly + one ElectricalTest per order.
- If no production orders exist, it creates some dummy orders first.
- Safe to run: skips if records already exist for an order.
"""

import sys
from datetime import date, datetime
from app import app, db
from models import Product, ProductionOrder, Assembly, ElectricalTest

# ─────────────────────────────────────────────────────────────
# Realistic sample data pools
# ─────────────────────────────────────────────────────────────

ASSEMBLY_TEMPLATES = [
    {
        "assigned_to": "Ravi Kumar",
        "notes": "Follow standard wiring layout for MCC panel.",
        "checklist": [
            {"item": "Frame & Enclosure installation",       "done": True},
            {"item": "Bus bar mounting & torque check",      "done": True},
            {"item": "Circuit breaker installation",         "done": True},
            {"item": "Cable tray & cable routing",           "done": True},
            {"item": "Control wiring (DIN rail components)", "done": False},
            {"item": "PLC rack mounting & I/O wiring",       "done": False},
            {"item": "HMI panel mounting & connection",      "done": False},
            {"item": "Earth bonding & continuity check",     "done": False},
            {"item": "Internal label & ferruling",           "done": False},
            {"item": "Final inspection & sign-off",          "done": False},
        ],
    },
    {
        "assigned_to": "Sundar Raj",
        "notes": "Use copper lugs for all power terminations.",
        "checklist": [
            {"item": "Sheet metal enclosure preparation",   "done": True},
            {"item": "Component layout as per drawing",     "done": True},
            {"item": "MCB / MCCB installation",             "done": True},
            {"item": "Relay & timer mounting",              "done": True},
            {"item": "Power wiring (L1, L2, L3, N, PE)",   "done": True},
            {"item": "Control circuit wiring",              "done": True},
            {"item": "Terminal block installation",         "done": False},
            {"item": "Cable ferruling & markers",           "done": False},
            {"item": "Quality check – wiring correctness",  "done": False},
            {"item": "Panel door & gasket fitment",         "done": False},
        ],
    },
    {
        "assigned_to": "Murugan S",
        "notes": "Panel for pump control with SCADA integration.",
        "checklist": [
            {"item": "Base plate & back plate preparation", "done": True},
            {"item": "VFD mounting & cooling arrangement",  "done": True},
            {"item": "Contactor & overload relay fitting",  "done": True},
            {"item": "Selector switch & push button wiring","done": True},
            {"item": "Analog I/O wiring (4–20 mA loops)",  "done": True},
            {"item": "RS-485 / Modbus cable routing",       "done": True},
            {"item": "Power factor capacitor bank wiring",  "done": False},
            {"item": "Cable schedule verification",         "done": False},
            {"item": "Loop test with field instruments",    "done": False},
            {"item": "Commissioning readiness sign-off",    "done": False},
        ],
    },
    {
        "assigned_to": "Karthik V",
        "notes": "Fully automated conveyor control panel.",
        "checklist": [
            {"item": "DIN rail cutting & mounting",         "done": True},
            {"item": "Servo drive & motor wiring",          "done": True},
            {"item": "Safety relay & E-stop circuit",       "done": True},
            {"item": "PLC CPU & expansion modules wiring",  "done": True},
            {"item": "Ethernet switch & PROFINET wiring",   "done": True},
            {"item": "24 V DC power supply wiring",         "done": True},
            {"item": "I/O module loop testing",             "done": True},
            {"item": "Program download & initial run",      "done": True},
            {"item": "Interlocking logic verification",     "done": False},
            {"item": "FAT documentation & photos",          "done": False},
        ],
    },
    {
        "assigned_to": "Priya D",
        "notes": "Water treatment SCADA panel — IP65 rated.",
        "checklist": [
            {"item": "IP65 enclosure & cable glands",       "done": True},
            {"item": "RTU / PLC mounting",                  "done": True},
            {"item": "4G modem & antenna installation",     "done": True},
            {"item": "Solar charge controller wiring",      "done": True},
            {"item": "Battery bank connection",             "done": True},
            {"item": "Flow meter & level sensor wiring",    "done": True},
            {"item": "Alarm output wiring",                 "done": True},
            {"item": "Remote monitoring commissioning",     "done": True},
            {"item": "Site acceptance test",                "done": True},
            {"item": "Documentation & handover",            "done": True},
        ],
    },
]

ELECTRICAL_TEMPLATES = [
    {
        "panel_type":  "MCC (Motor Control Centre)",
        "plc_type":    "Siemens S7-1200",
        "voltage":     "415 V AC, 3-Phase, 50 Hz",
        "test_status": "passed",
        "tested_by":   "Anand T",
        "remarks":     "All phase sequence, insulation resistance, and loop tests passed. IR > 500 MΩ.",
        "test_date":   date(2026, 4, 28),
    },
    {
        "panel_type":  "PCC (Power Control Centre)",
        "plc_type":    "Allen-Bradley MicroLogix 1400",
        "voltage":     "415 V AC, 3-Phase, 50 Hz",
        "test_status": "passed",
        "tested_by":   "Vijay N",
        "remarks":     "High-voltage test at 2 kV passed. No leakage detected. Functional test OK.",
        "test_date":   date(2026, 4, 30),
    },
    {
        "panel_type":  "VFD Panel",
        "plc_type":    "Mitsubishi FX5U",
        "voltage":     "415 V AC, 3-Phase, 50 Hz",
        "test_status": "failed",
        "tested_by":   "Bala S",
        "remarks":     "Phase-to-phase IR test failed on L2. Rewiring required for bus bar section 3.",
        "test_date":   date(2026, 5,  2),
    },
    {
        "panel_type":  "APFC Panel",
        "plc_type":    "Schneider Modicon M221",
        "voltage":     "415 V AC, 3-Phase, 50 Hz",
        "test_status": "passed",
        "tested_by":   "Anand T",
        "remarks":     "Power factor corrected to 0.98. Capacitor banks energised. No trip on load test.",
        "test_date":   date(2026, 5,  3),
    },
    {
        "panel_type":  "SCADA RTU Panel",
        "plc_type":    "Siemens S7-300",
        "voltage":     "24 V DC (internal), 415 V AC supply",
        "test_status": "pending",
        "tested_by":   "Murugan S",
        "remarks":     "Awaiting site power availability for load test.",
        "test_date":   None,
    },
]


# ─────────────────────────────────────────────────────────────
# Dummy production orders (created only if none exist)
# ─────────────────────────────────────────────────────────────

DUMMY_ORDERS = [
    {"quantity": 1, "status": "in_progress", "progress": 45,  "notes": "MCC panel for pharma plant.",    "start_date": date(2026, 4, 1),  "due_date": date(2026, 5, 15)},
    {"quantity": 2, "status": "in_progress", "progress": 65,  "notes": "PCC for textile factory.",       "start_date": date(2026, 4, 5),  "due_date": date(2026, 5, 20)},
    {"quantity": 1, "status": "in_progress", "progress": 80,  "notes": "VFD panel for pump station.",    "start_date": date(2026, 4, 10), "due_date": date(2026, 5, 10)},
    {"quantity": 1, "status": "completed",   "progress": 100, "notes": "APFC panel for cement plant.",   "start_date": date(2026, 3, 20), "due_date": date(2026, 4, 30)},
    {"quantity": 1, "status": "pending",     "progress": 0,   "notes": "SCADA RTU for water treatment.", "start_date": date(2026, 5, 5),  "due_date": date(2026, 6, 1)},
]


def seed():
    with app.app_context():
        print("=" * 58)
        print("  Teslead — Seed Assembly & Electrical Test Data")
        print("=" * 58)

        # ── Step 1: Ensure production orders exist ────────────────
        orders = ProductionOrder.query.order_by(ProductionOrder.id).all()

        if not orders:
            print("\n⚠  No production orders found. Creating dummy orders...")
            # Pick first product if any, else leave product_id null
            first_product = Product.query.first()
            for tmpl in DUMMY_ORDERS:
                o = ProductionOrder(
                    product_id = first_product.id if first_product else None,
                    **tmpl
                )
                db.session.add(o)
            db.session.commit()
            orders = ProductionOrder.query.order_by(ProductionOrder.id).all()
            print(f"  ✅ {len(orders)} production orders created.")

        print(f"\n  Found {len(orders)} production order(s). Seeding up to {len(ASSEMBLY_TEMPLATES)} records.\n")

        asm_added = 0
        elec_added = 0

        for i, order in enumerate(orders):
            tmpl_index = i % len(ASSEMBLY_TEMPLATES)

            # ── Assembly ──────────────────────────────────────────
            existing_asm = Assembly.query.filter_by(production_id=order.id).first()
            if existing_asm:
                print(f"  ⏭  Assembly for order #{order.id} already exists — skipped.")
            else:
                asm_tmpl = ASSEMBLY_TEMPLATES[tmpl_index]
                checklist = asm_tmpl["checklist"]
                total  = len(checklist)
                done   = sum(1 for item in checklist if item.get("done"))
                progress = int((done / total) * 100) if total else 0
                if progress == 0:
                    status = "pending"
                elif progress == 100:
                    status = "completed"
                else:
                    status = "in_progress"

                asm = Assembly(
                    production_id = order.id,
                    checklist     = checklist,
                    status        = status,
                    progress      = progress,
                    assigned_to   = asm_tmpl["assigned_to"],
                    notes         = asm_tmpl["notes"],
                )
                db.session.add(asm)
                asm_added += 1
                print(f"  ✅ Assembly for order #{order.id} — {progress}% ({status}) → {asm_tmpl['assigned_to']}")

            # ── ElectricalTest ────────────────────────────────────
            existing_elec = ElectricalTest.query.filter_by(production_id=order.id).first()
            if existing_elec:
                print(f"  ⏭  ElectricalTest for order #{order.id} already exists — skipped.")
            else:
                elec_tmpl = ELECTRICAL_TEMPLATES[tmpl_index]
                elec = ElectricalTest(
                    production_id = order.id,
                    panel_type    = elec_tmpl["panel_type"],
                    plc_type      = elec_tmpl["plc_type"],
                    voltage       = elec_tmpl["voltage"],
                    test_status   = elec_tmpl["test_status"],
                    tested_by     = elec_tmpl["tested_by"],
                    remarks       = elec_tmpl["remarks"],
                    test_date     = elec_tmpl["test_date"],
                )
                db.session.add(elec)
                elec_added += 1
                print(f"  ✅ ElectricalTest for order #{order.id} — {elec_tmpl['test_status']} → {elec_tmpl['panel_type']}")

        db.session.commit()

        print("\n" + "=" * 58)
        print(f"  Done! {asm_added} assembly + {elec_added} electrical test record(s) inserted.")
        print("=" * 58)


if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"\n❌ Seed failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
