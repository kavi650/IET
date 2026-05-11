# 🏭 Teslead Equipments — Comprehensive Industrial Platform

A complete full-stack industrial web application and enterprise operational system for **Teslead Equipments Private Limited**, specializing in industrial machines, hydraulic systems, pneumatic systems, and advanced testing equipment.

This project encompasses a public-facing corporate website, an internal administrative ERP portal, a specialized industrial testing software suite, and an AI-powered chatbot.

---

## 🏗️ System Architecture

The application is built around a modular monolithic architecture using **Python, Flask, and PostgreSQL**. The codebase is structured using Flask Blueprints to cleanly separate different departments and functional areas.

**Core Technologies:**
- **Backend**: Python 3.10+, Flask, SQLAlchemy (ORM)
- **Database**: PostgreSQL (Relational + JSONB for flexible schema)
- **Frontend**: HTML5, Vanilla JavaScript, Custom CSS (Responsive, Dark Mode)
- **AI Integration**: Ollama (LLaMA3) for the chatbot and test data analysis

---

## 🚀 Quick Start

### 1. Setup PostgreSQL Database

```bash
# Create the database in your PostgreSQL instance
createdb teslead_db

# Run the schema and initial seed data (if setting up from scratch)
psql -d teslead_db -f schema_v3.sql
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `.env` with your PostgreSQL credentials:

```env
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=teslead_db
```

### 4. Run the Application

You can use the provided batch files or run it directly:

```bash
# Runs the main Flask server on port 5000
python app.py
```
*Alternatively, run `run_main.bat` or `run_testing.bat` if configured.*

Open **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```text
d:\Teslead\
├── app.py                    # Main Flask application entry point
├── config.py                 # Configuration settings (DB, AI, etc.)
├── chatbot.py                # Ollama AI chatbot logic & integrations
├── models.py                 # SQLAlchemy core database models
├── models_v3.py              # Extended models for Testing & Advanced features
├── schema_v3.sql             # PostgreSQL schema + seed data
├── requirements.txt          # Python dependencies
├── migrate_v3.py             # Database migration script for v3 schema
│
├── blueprints/               # 🏢 Departmental & Routing Modules
│   ├── main.py               # Core public routes (Home, About, Products)
│   ├── admin.py              # Core System Admin dashboard
│   ├── stores.py             # Inventory & Stores Management
│   ├── sales.py              # Sales Enquiry & Quote Management
│   ├── production.py         # Production Orders Management
│   ├── assembly.py           # Assembly Checklists & Tracking
│   ├── electrical.py         # Electrical Component Verification
│   ├── public_v3.py          # V3 Public Pages (Process, Industries, Portfolio)
│   ├── access.py             # Testing Hub Access Token Management
│   ├── testing_admin.py      # Admin Controls for Test Sessions & Users
│   └── ai_admin.py           # AI Insights & Prompt Management
│
├── testing_app/              # 🔬 Specialized Testing Software Suite
│   ├── realtime.py           # Real-time WebSocket/Polling simulation
│   ├── simulate_readings.py  # Test rig sensor data generator
│   ├── blueprints/           # Testing Hub Specific Blueprints
│   │   ├── dashboard.py      # Operator Testing Dashboard
│   │   ├── sessions.py       # Live Test Session Management
│   │   ├── readings.py       # Sensor Data Logging API
│   │   └── results.py        # Post-Test Analysis & Reporting
│   └── templates/testing/    # Testing UI HTML Views
│
├── templates/                # 🎨 Main HTML Templates
│   ├── index.html            # Public landing page
│   ├── admin.html            # Main Administrative ERP UI
│   ├── testing_access.html   # Access Request portal for testing suite
│   └── ... (Other public/admin views)
│
└── static/                   # 🖼️ Static Assets (CSS, JS, Images)
    ├── css/                  # Styling (style.css, admin_extra.css, etc.)
    ├── js/                   # Frontend Logic (admin.js, admin_v3.js, etc.)
    └── images/               # Product and branding imagery
```

---

## ✨ Features Overview

### 1. Public Corporate Website (`/`)
- Professional, high-performance UI with responsive design.
- Dark/Light mode toggle with `localStorage` persistence.
- Complete product catalog with filtering, search, and dynamic specification display.
- Specialized pages: Process, Industries, Compare Systems, and Downloads.
- Embedded floating AI Chatbot widget.

### 2. Departmental ERP & Admin Portal (`/admin`)
Modular management interface designed for internal company operations:
- **System Admin**: Site configurations, chatbot logs, global settings.
- **Sales Dept**: Manage incoming customer enquiries and sales pipeline.
- **Stores (Inventory)**: Track product stock, raw materials, and usage logs.
- **Production Dept**: Manage internal work orders and manufacturing status.
- **Assembly Dept**: Granular assembly stage tracking and checklist verification.
- **Electrical Dept**: Pre-dispatch electrical testing and quality sign-off.

### 3. Industrial Testing Software Suite (`/testing`)
A dedicated module acting as the HMI (Human-Machine Interface) for industrial testing rigs:
- **Access Control**: Public users can request access; admins approve and issue time-limited tokens.
- **Live Testing**: Real-time sensor monitoring (Pressure, Flow, Temperature, Leakage) using high-fidelity gauge visualizations and charts.
- **Data Acquisition**: Simulates and logs high-frequency telemetry data to the database during active tests.
- **Analysis & Results**: Automated pass/fail evaluation, trend analysis, PDF/CSV report generation, and AI-driven anomaly detection.
- **Settings**: Configurable thresholds, alarm limits, and calibration data.

### 4. AI & Intelligence Integrations
- **Customer Support Chatbot**: Powered by Ollama (LLaMA3). Answers user questions based on the company's product catalog and knowledge base. Maintains chat context.
- **Test Analysis AI**: Uses LLMs to analyze test results, summarize performance characteristics, and flag anomalies in sensor data.
- **Admin Insights**: System automatically generates "AI Insights" for admins (e.g., low stock alerts, recurring failure patterns).

---

## 🗄️ Database Schema & Models

The PostgreSQL database utilizes SQLAlchemy ORM. The schema is divided logically:

- **Core Models (`models.py`)**: `User`, `Category`, `Product`, `Specification`, `Enquiry`, `ChatbotLog`, `SiteConfig`, `StockUsageLog`, `ProductionOrder`, `Assembly`, `ElectricalTest`.
- **Advanced Models (`models_v3.py`)**: `Project`, `Download`, `Industry`, `TestingAccessRequest`, `TestSession`, `TestReading`, `TestResult`, `TestSettings`, `AIInsight`, `ActivityLog`.

*Note: Heavy telemetry data (`TestReading`) is stored relationally with indexing for time-series extraction, while flexible data (like assembly checklists or AI anomalies) uses `JSONB` columns.*

---

## 🔌 API Namespace Guide

The application provides extensive RESTful endpoints, generally returning JSON.

- `/api/products/...` - Public product catalog APIs.
- `/api/chat` - Public AI Chatbot endpoint.
- `/api/contact` - Public sales enquiry submission.
- `/api/access/...` - Testing suite access request handling.
- `/api/admin/...` - Global settings and system logs.
- `/api/sales/...` - Sales department endpoints.
- `/api/stores/...` - Inventory management endpoints.
- `/api/production/...` - Production order endpoints.
- `/api/assembly/...` - Assembly tracking endpoints.
- `/api/electrical/...` - Electrical testing endpoints.
- `/api/test-sessions/...` - Live testing and telemetry endpoints.

---

## 🤖 Ollama Setup (Local AI)

To enable the AI capabilities (Chatbot & Testing Insights), you must install Ollama:

1. Download & Install from [ollama.ai](https://ollama.ai)
2. Open terminal and run: `ollama pull llama3`
3. The server runs automatically on `http://localhost:11434`. 
4. Ensure `OLLAMA_URL` in `config.py` points to this address.

*(If Ollama is unreachable, the system elegantly falls back to standard heuristic responses without crashing).*

---

**Developed for Industrial Excellence & Operational Efficiency.**
