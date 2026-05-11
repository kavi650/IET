-- ============================================
-- Teslead Equipments Database Schema
-- PostgreSQL
-- ============================================

-- Drop tables if they exist (for fresh setup)
DROP TABLE IF EXISTS chatbot_logs CASCADE;
DROP TABLE IF EXISTS enquiries CASCADE;
DROP TABLE IF EXISTS specifications CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CATEGORIES TABLE
-- ============================================
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50)
);

-- ============================================
-- PRODUCTS TABLE
-- ============================================
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description TEXT,
    working_principle TEXT,
    applications TEXT,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_category ON products(category_id);

-- ============================================
-- SPECIFICATIONS TABLE
-- ============================================
CREATE TABLE specifications (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,
    value VARCHAR(255) NOT NULL
);

CREATE INDEX idx_specs_product ON specifications(product_id);

-- ============================================
-- ENQUIRIES TABLE
-- ============================================
CREATE TABLE enquiries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    company VARCHAR(200),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CHATBOT LOGS TABLE
-- ============================================
CREATE TABLE chatbot_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SEED DATA: Categories
-- ============================================
INSERT INTO categories (name, description, icon) VALUES
('Test Equipment', 'Precision testing systems for industrial applications including pump testing, valve testing, and pressure testing.', 'fa-flask'),
('Hydraulic Systems', 'Complete hydraulic solutions including power packs, cylinders, boosters, and custom hydraulic assemblies.', 'fa-cogs'),
('Pneumatic Systems', 'Air-powered systems including control valves, air preparation units, and pneumatic actuators.', 'fa-wind'),
('Special Machines', 'Custom-engineered industrial machines designed for specific manufacturing and testing applications.', 'fa-industry');

-- ============================================
-- SEED DATA: Products
-- ============================================

-- Test Equipment
INSERT INTO products (name, category_id, description, working_principle, applications, image_url) VALUES
(
    'Pump Test Rig',
    1,
    'Advanced pump test rig designed for comprehensive performance evaluation of centrifugal, gear, vane, and piston pumps. Features automated data acquisition, real-time monitoring, and precision instrumentation for accurate flow, pressure, and efficiency measurements.',
    'The test rig operates by driving the pump under test through a variable speed motor while measuring key parameters including flow rate (via electromagnetic flowmeters), discharge pressure (via precision transducers), input torque (via inline torque sensors), and power consumption. A closed-loop hydraulic circuit with adjustable loading valves simulates various operating conditions. Data is captured via a PLC-based DAQ system and displayed on an HMI panel with trend logging.',
    'Pump manufacturers for R&D and quality assurance, Oil and gas industry for pump certification, Automotive sector for fuel pump and coolant pump testing, Power plants for boiler feed pump performance verification, Water treatment facilities for pump selection and validation.',
    '/static/images/pump_test_rig.jpg'
),
(
    'Valve Test Bench',
    1,
    'High-precision valve test bench engineered for testing safety valves, control valves, gate valves, and check valves. Supports hydrostatic, pneumatic, and functional testing with automated test sequences and digital reporting.',
    'The valve test bench uses a high-pressure hydraulic power unit to generate test pressures up to 1000 bar. The valve under test is clamped in a universal fixture and subjected to hydrostatic pressure testing (shell and seat tests per API 598/ISO 5208). Pneumatic seat leakage testing uses regulated air supply with bubble detection or mass spectrometer leak detection. An automated PLC controls pressure ramp rates, hold times, and acceptance criteria. Results are stored digitally with certificate generation.',
    'Valve manufacturers for production testing and certification, Oil and gas refineries for valve maintenance and recertification, Power generation plants for safety valve verification, Chemical processing plants for valve integrity assurance, Pipeline operators for valve compliance testing.',
    '/static/images/valve_test_bench.jpg'
),
(
    'Pressure Testing System',
    1,
    'Industrial pressure testing system capable of hydrostatic and pneumatic testing up to 2000 bar. Designed for pressure vessels, pipelines, hoses, fittings, and other pressure-containing components with full traceability and automated reporting.',
    'The system employs air-driven hydraulic pumps or electric-driven intensifiers to generate high test pressures. Test pressure is applied gradually per code requirements (ASME, EN, API) with precise control via proportional valves. Calibrated digital pressure transducers monitor test pressure with ±0.25% accuracy. Automated pressure hold and decay monitoring detects even micro-leaks. A chart recorder and digital logging system provide full test documentation.',
    'Pressure vessel manufacturers, Pipeline construction and integrity testing, Hose and fitting manufacturers, Aerospace component testing, Defense equipment pressure qualification, Fire extinguisher testing and recertification.',
    '/static/images/pressure_testing.jpg'
);

-- Hydraulic Systems
INSERT INTO products (name, category_id, description, working_principle, applications, image_url) VALUES
(
    'Hydraulic Power Pack',
    2,
    'Custom-engineered hydraulic power packs ranging from 1 HP to 500 HP. Available in standard and compact configurations with options for variable displacement pumps, proportional valves, accumulator circuits, and integrated cooling systems.',
    'The hydraulic power pack consists of an electric motor driving a hydraulic pump (gear, vane, or piston type) that draws fluid from a reservoir through a suction filter. The pump converts mechanical energy to hydraulic energy, pressurizing the fluid which is then directed through a valve manifold to actuators. The manifold houses directional control valves, pressure relief valves, and flow control valves. Return fluid passes through return-line filters and may pass through a heat exchanger before returning to the reservoir.',
    'Machine tool industry for press and clamp operations, Steel mills for rolling mill equipment, Marine applications for deck machinery, Plastic injection molding machines, Industrial automation and material handling, Construction equipment power units.',
    '/static/images/hydraulic_power_pack.jpg'
),
(
    'Hydraulic Cylinders',
    2,
    'Precision-manufactured hydraulic cylinders in tie-rod, welded, and telescopic configurations. Bore sizes from 25mm to 500mm with stroke lengths up to 6000mm. Rated pressures up to 350 bar with custom mounting options.',
    'Hydraulic cylinders convert hydraulic pressure energy into linear mechanical force and motion. Pressurized hydraulic fluid enters the cylinder through ports and acts on the piston face, creating force proportional to the pressure multiplied by the piston area. The piston is connected to a rod that extends through a gland assembly with seals to prevent leakage. Double-acting cylinders allow force in both extend and retract directions. Cushioning mechanisms decelerate the piston near end-of-stroke to prevent impact damage.',
    'Press manufacturing for stamping and forming, Construction equipment (excavators, loaders), Agricultural machinery, Marine steering systems, Industrial lifting and positioning, Dam gates and flood control systems.',
    '/static/images/hydraulic_cylinders.jpg'
),
(
    'Hydraulic Pressure Boosters',
    2,
    'Hydraulic intensifiers and pressure boosters that amplify existing system pressure by ratios of 2:1 to 10:1. Compact design, no external power required, ideal for localized high-pressure needs in existing hydraulic circuits.',
    'Pressure boosters operate on the principle of differential area pistons. A large-area driven piston receives system pressure from the primary circuit. This piston is mechanically connected to a smaller-area output piston. Since force equals pressure times area, the smaller output piston generates proportionally higher pressure. The boost ratio equals the area ratio of the two pistons. An internal shuttle valve provides automatic reciprocation for continuous high-pressure output.',
    'Clamping and workholding in CNC machines, Hydroforming operations, Pressure testing where higher pressures are needed intermittently, Punching and riveting operations, Emergency hydraulic systems, Intensified circuits for specific actuators in complex systems.',
    '/static/images/hydraulic_boosters.jpg'
);

-- Pneumatic Systems
INSERT INTO products (name, category_id, description, working_principle, applications, image_url) VALUES
(
    'Pneumatic Control Systems',
    3,
    'Complete pneumatic control systems featuring precision regulators, directional control valves (3/2, 5/2, 5/3 way), proportional valves, and FRL units. Available as individual components or pre-assembled manifold solutions with IoT-ready monitoring.',
    'Pneumatic control systems use compressed air as the working medium. Air from a compressor is filtered, regulated, and lubricated by the FRL unit. Directional control valves (solenoid or pilot-operated) route air to actuators. 5/2 valves provide double-acting cylinder control while 3/2 valves control single-acting cylinders. Proportional valves allow variable pressure and flow control for precise motion control. Speed control is achieved through flow control valves (meter-in or meter-out). Quick exhaust valves increase actuator speed for high-cycle applications.',
    'Packaging machinery for pick-and-place operations, Food and beverage processing automation, Pharmaceutical manufacturing clean-room equipment, Textile machinery automation, Printing press automation, Assembly line automation in automotive manufacturing.',
    '/static/images/pneumatic_control.jpg'
),
(
    'Air Preparation Units',
    3,
    'Industrial air preparation units combining filters (5μm to 0.01μm), regulators (with precision and tamper-proof options), and lubricators. Available in modular configurations for flow rates from 500 to 15,000 l/min with auto-drain and monitoring options.',
    'Air preparation units condition compressed air for optimal pneumatic system performance. The filter element removes solid particles and water droplets through centrifugal separation and coalescence filtering. The regulator maintains constant downstream pressure using a diaphragm-spring mechanism, automatically adjusting a poppet valve to compensate for supply pressure variations and downstream flow changes. The lubricator injects a metered amount of oil mist into the air stream using a venturi principle for actuator lubrication.',
    'All pneumatic systems requiring clean, regulated, and lubricated air supply, Process industries, Manufacturing plants, Compressed air distribution networks, Paint spray systems, Pneumatic tool operation.',
    '/static/images/air_preparation.jpg'
);

-- Special Machines
INSERT INTO products (name, category_id, description, working_principle, applications, image_url) VALUES
(
    'Custom SPM Machines',
    4,
    'Special Purpose Machines (SPMs) custom-designed and manufactured for specific industrial operations. We engineer complete turnkey solutions including mechanical design, hydraulic/pneumatic actuation, PLC automation, HMI interfaces, and safety systems. Each machine is designed to maximize productivity and ensure operator safety.',
    'Each SPM is engineered from scratch based on the customer''s specific manufacturing process requirements. The design process involves: process analysis and cycle time optimization, 3D modeling and FEA simulation, prototype development and validation, and final manufacturing with full documentation. Machines typically integrate servo or hydraulic drives, precision guideways, automated feeding systems, and PLC-based control with operator-friendly HMI touchscreens.',
    'Automotive component manufacturing (pressing, forming, assembly), Aerospace precision machining operations, Defense equipment manufacturing and testing, Specialized testing machines for R&D laboratories, Assembly automation for consumer goods, Material handling and sorting systems for logistics.',
    '/static/images/custom_spm.jpg'
),
(
    'Industrial Flushing Rigs',
    4,
    'Hydraulic flushing rigs designed for high-velocity oil flushing of pipes, tubes, and hydraulic systems per NAS 1638 and ISO 4406 cleanliness standards. Features dual-stage filtration, temperature control, and online particle counting for verified cleanliness.',
    'The flushing rig circulates heated hydraulic oil at high velocity (achieving turbulent flow with Reynolds number > 4000) through the target piping system. Dual-stage filtration (typically 10μm absolute followed by 3μm absolute) progressively removes particulate contamination. Temperature cycling (alternating hot and cold flushing) helps dislodge embedded particles through thermal expansion/contraction of pipe walls. An online laser particle counter continuously monitors fluid cleanliness and provides real-time NAS/ISO class readings to confirm when target cleanliness is achieved.',
    'Pre-commissioning of hydraulic systems in steel plants, Oil and gas pipeline flushing, Power plant hydraulic system flushing, Marine vessel hydraulic circuit cleaning, New machinery hydraulic system preparation, Maintenance flushing of contaminated hydraulic systems.',
    '/static/images/flushing_rig.jpg'
);

-- ============================================
-- SEED DATA: Specifications
-- ============================================

-- Pump Test Rig specs (product_id = 1)
INSERT INTO specifications (product_id, key, value) VALUES
(1, 'Flow Range', '0.5 - 5000 LPM'),
(1, 'Pressure Range', '0 - 500 bar'),
(1, 'Drive Motor', '1 HP - 200 HP (AC/DC Variable Speed)'),
(1, 'Accuracy', '±0.5% of full scale'),
(1, 'Data Acquisition', 'PLC-based with HMI touchscreen'),
(1, 'Test Medium', 'Water / Hydraulic Oil / Custom Fluids'),
(1, 'Power Supply', '415V AC, 50Hz, 3-Phase');

-- Valve Test Bench specs (product_id = 2)
INSERT INTO specifications (product_id, key, value) VALUES
(2, 'Test Pressure', 'Up to 1000 bar (Hydrostatic)'),
(2, 'Pneumatic Test', 'Up to 50 bar'),
(2, 'Valve Size Range', 'DN15 - DN600'),
(2, 'Pressure Class', '150# to 2500#'),
(2, 'Test Standards', 'API 598, ISO 5208, BS EN 12266'),
(2, 'Clamping', 'Hydraulic universal clamping system'),
(2, 'Reporting', 'Automated digital test certificates');

-- Pressure Testing System specs (product_id = 3)
INSERT INTO specifications (product_id, key, value) VALUES
(3, 'Max Pressure', '2000 bar'),
(3, 'Pressure Accuracy', '±0.25% FS'),
(3, 'Pump Type', 'Air-driven / Electric-driven intensifier'),
(3, 'Test Standards', 'ASME B31.3, EN 13480, API 6A'),
(3, 'Chart Recording', 'Digital with pressure-time graph'),
(3, 'Safety Features', 'Burst disc, pressure relief, emergency stop'),
(3, 'Test Medium', 'Water / Glycol / Hydraulic Oil');

-- Hydraulic Power Pack specs (product_id = 4)
INSERT INTO specifications (product_id, key, value) VALUES
(4, 'Power Range', '1 HP - 500 HP'),
(4, 'Operating Pressure', 'Up to 350 bar'),
(4, 'Pump Type', 'Gear / Vane / Axial Piston'),
(4, 'Reservoir Capacity', '10L - 5000L'),
(4, 'Cooling', 'Air-cooled / Water-cooled heat exchangers'),
(4, 'Filtration', '10μm return line, 3μm pressure line'),
(4, 'Noise Level', '< 72 dB(A) at 1m');

-- Hydraulic Cylinders specs (product_id = 5)
INSERT INTO specifications (product_id, key, value) VALUES
(5, 'Bore Size', '25mm - 500mm'),
(5, 'Stroke Length', 'Up to 6000mm'),
(5, 'Operating Pressure', 'Up to 350 bar'),
(5, 'Rod Material', 'Chrome-plated C45 / Stainless Steel'),
(5, 'Seal Type', 'Polyurethane / PTFE / Viton'),
(5, 'Mounting Styles', 'Flange, Trunnion, Clevis, Foot'),
(5, 'Standards', 'ISO 6020/6022, DIN 24554');

-- Hydraulic Pressure Boosters specs (product_id = 6)
INSERT INTO specifications (product_id, key, value) VALUES
(6, 'Boost Ratio', '2:1 to 10:1'),
(6, 'Input Pressure', '50 - 250 bar'),
(6, 'Output Pressure', 'Up to 2500 bar'),
(6, 'No External Power', 'Driven by existing system pressure'),
(6, 'Output Flow', '0.1 - 5 LPM (depending on ratio)'),
(6, 'Seal Material', 'PTFE / Polyurethane'),
(6, 'Body Material', 'Alloy Steel, Hardened & Ground');

-- Pneumatic Control Systems specs (product_id = 7)
INSERT INTO specifications (product_id, key, value) VALUES
(7, 'Operating Pressure', '0 - 10 bar'),
(7, 'Valve Types', '3/2, 5/2, 5/3 way (Solenoid/Pilot)'),
(7, 'Connection Sizes', 'M5, G1/8, G1/4, G3/8, G1/2'),
(7, 'Response Time', '< 25ms typical'),
(7, 'Flow Rate', 'Up to 3500 Nl/min per valve'),
(7, 'IP Rating', 'IP65 standard, IP67 available'),
(7, 'Operating Temperature', '-10°C to +60°C');

-- Air Preparation Units specs (product_id = 8)
INSERT INTO specifications (product_id, key, value) VALUES
(8, 'Filter Grade', '5μm / 0.3μm / 0.01μm (staged)'),
(8, 'Pressure Range', '0.5 - 10 bar (regulated)'),
(8, 'Flow Capacity', '500 - 15,000 Nl/min'),
(8, 'Auto-drain', 'Available (float or timer-based)'),
(8, 'Bowl Material', 'Polycarbonate / Metal (high-temperature)'),
(8, 'Monitoring', 'Pressure differential indicator, IoT-ready'),
(8, 'Port Sizes', 'G1/4, G3/8, G1/2, G3/4, G1');

-- Custom SPM specs (product_id = 9)
INSERT INTO specifications (product_id, key, value) VALUES
(9, 'Design', 'Custom-engineered per requirement'),
(9, 'Automation', 'PLC (Siemens/Allen-Bradley) + HMI'),
(9, 'Drive System', 'Servo / Hydraulic / Pneumatic'),
(9, 'Safety', 'CE compliant, light curtains, interlock guards'),
(9, 'Software', 'Custom PLC programs with recipe management'),
(9, 'Documentation', 'GA drawings, electrical schematics, user manual'),
(9, 'Warranty', '12 months standard, AMC available');

-- Flushing Rig specs (product_id = 10)
INSERT INTO specifications (product_id, key, value) VALUES
(10, 'Flow Rate', '50 - 1000 LPM'),
(10, 'Flushing Pressure', 'Up to 100 bar'),
(10, 'Filtration', 'Dual-stage: 10μm + 3μm absolute'),
(10, 'Temperature Range', '40°C - 80°C (controlled)'),
(10, 'Cleanliness Verification', 'Online laser particle counter'),
(10, 'Standards', 'NAS 1638, ISO 4406'),
(10, 'Heating', 'Electric immersion heaters with thermostat');

-- ============================================
-- SEED DATA: Default Admin User
-- ============================================
INSERT INTO users (name, email, password) VALUES
('Admin', 'admin@teslead.com', 'admin123');
