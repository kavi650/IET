import os
from dotenv import load_dotenv

load_dotenv()


def _fix_db_url(url: str) -> str:
    """
    Normalize DATABASE_URL for SQLAlchemy 2.x compatibility.
    - Render/Heroku: 'postgres://' → 'postgresql://'
    - Neon/Supabase: already 'postgresql://' — no change needed
    """
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'teslead-secret-key-change-in-production')

    # PostgreSQL Database
    DB_USER     = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '852685')
    DB_HOST     = os.getenv('DB_HOST', 'localhost')
    DB_PORT     = os.getenv('DB_PORT', '5433')
    DB_NAME     = os.getenv('DB_NAME', 'teslead_db')

    _default_uri = (
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )

    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.getenv('DATABASE_URL', _default_uri)
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Enable SSL for cloud databases (Neon, Supabase, Railway)
    # SQLite / local Postgres don't need this — it's ignored safely
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,        # reconnect on stale connections (serverless)
        "pool_recycle": 300,           # recycle connections every 5 min
    }

    # Ollama AI Settings (disabled on Render — use env var to override)
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL    = os.getenv('OLLAMA_MODEL', 'llama3')

    # Admin credentials
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # Flask settings
    DEBUG   = os.getenv('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    TESTING = False
