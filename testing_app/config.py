"""testing_app/config.py — configuration for the testing software."""
import os
from dotenv import load_dotenv
load_dotenv()

class TestingConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'testing-app-secret-key')

    # Same PostgreSQL DB as main app
    _user = os.getenv('DB_USER', 'postgres')
    _pass = os.getenv('DB_PASSWORD', '852685')
    _host = os.getenv('DB_HOST', 'localhost')
    _port = os.getenv('DB_PORT', '5433')
    _name = os.getenv('DB_NAME', 'teslead_db')

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'postgresql://{_user}:{_pass}@{_host}:{_port}/{_name}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Main app URL — used to verify access tokens
    MAIN_APP_URL = os.getenv('MAIN_APP_URL', 'http://127.0.0.1:5000')

    # Ollama
    OLLAMA_URL   = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
