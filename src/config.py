import os
from pathlib import Path
from dotenv import load_dotenv


# ==================================================
# PROJECT PATHS
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOG_DIR = PROJECT_DIR / "logs"

for folder in [DATA_DIR, RAW_DIR, PROCESSED_DIR, LOG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ==================================================
# ENVIRONMENT VARIABLES
# ==================================================

ENV_FILE = PROJECT_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)

API_KEY = os.getenv("APISPORTS_API_KEY")

if not API_KEY:
    raise ValueError(
        f"APISPORTS_API_KEY is missing. Check your .env file: {ENV_FILE}"
    )


# ==================================================
# API CONFIGURATION
# ==================================================

BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 39
SEASON = 2024
REQUEST_TIMEOUT = 30


# ==================================================
# SQL SERVER CONFIGURATION
# ==================================================

SERVER = os.getenv("EPL_SQL_SERVER")
DATABASE = os.getenv("EPL_SQL_DATABASE")
ODBC_DRIVER = os.getenv("EPL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
TRUST_CERTIFICATE = os.getenv("EPL_TRUST_CERTIFICATE", "yes")

if not SERVER or not DATABASE:
    raise ValueError(
        "EPL_SQL_SERVER or EPL_SQL_DATABASE is missing from your .env file."
    )

CONNECTION_STRING = (
    f"DRIVER={{{ODBC_DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    f"TrustServerCertificate={TRUST_CERTIFICATE};"
)


# ==================================================
# PIPELINE CONFIGURATION
# ==================================================

STAGING_LOAD_MODE = "refresh"
WAREHOUSE_LOAD_MODE = "upsert"
