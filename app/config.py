import os
from dotenv import load_dotenv

load_dotenv(override=True)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORDS = os.getenv("DB_PASSWORDS", "")
DB_NAME = os.getenv("DB_NAME", "investech")

BRAPI_BASE_URL = os.getenv("BRAPI_BASE_URL", "https://brapi.dev")
BRAPI_API_TOKEN = os.getenv("BRAPI_API_TOKEN", "")

DECISAO_URL = os.getenv("DECISAO_URL", "http://localhost:8080/api/decisoes")

MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))
DECISION_COOLDOWN_SECONDS = int(os.getenv("DECISION_COOLDOWN_SECONDS", "300"))
DEFAULT_QUANTITY = float(os.getenv("DEFAULT_QUANTITY", "1"))
