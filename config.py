import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

IS_VERCEL = bool(os.getenv("VERCEL"))
if IS_VERCEL:
    UPLOAD_DIR = Path("/tmp/uploads")
    DATA_DIR = Path("/tmp/data")
else:
    UPLOAD_DIR = BASE_DIR / "uploads"
    DATA_DIR = BASE_DIR / "data"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_TEXT_CHARS = int(os.getenv("MAX_TEXT_CHARS", "50000"))
FREE_ANALYSES_PER_MONTH = int(os.getenv("FREE_ANALYSES_PER_MONTH", "10"))
REFERRAL_DISCOUNT_PERCENT = int(os.getenv("REFERRAL_DISCOUNT_PERCENT", "15"))
PRO_PRICE_USD = float(os.getenv("PRO_PRICE_USD", "9.99"))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
