"""testing_app/config.py — configuration for the testing software."""
import os
from dotenv import load_dotenv

load_dotenv()


def _fix_db_url(url: str) -> str:
    """Render supplies 'postgres://...' — SQLAlchemy 2.x needs 'postgresql://'."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _fix_main_url(url: str) -> str:
    """Ensure MAIN_APP_URL always has a scheme (https by default on Render)."""
    if url and not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url


class TestingConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'testing-app-secret-key')

    # Same PostgreSQL DB as main app
    _user = os.getenv('DB_USER', 'postgres')
    _pass = os.getenv('DB_PASSWORD', '852685')
    _host = os.getenv('DB_HOST', 'localhost')
    _port = os.getenv('DB_PORT', '5433')
    _name = os.getenv('DB_NAME', 'teslead_db')

    _default_uri = f'postgresql://{_user}:{_pass}@{_host}:{_port}/{_name}'

    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.getenv('DATABASE_URL', _default_uri)
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings for cloud databases (Neon, Supabase, Railway)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Main app URL — used to verify access tokens
    MAIN_APP_URL = _fix_main_url(
        os.getenv('MAIN_APP_URL', 'http://127.0.0.1:5000')
    )

    # Ollama (disabled on Render unless running a self-hosted instance)
    OLLAMA_URL   = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

    DEBUG   = os.getenv('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    TESTING = False
