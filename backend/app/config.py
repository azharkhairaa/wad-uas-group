import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/lapangin",
)

SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY belum diatur atau kurang dari 32 karakter. "
        "Salin .env.example menjadi .env lalu isi SECRET_KEY."
    )

ALGORITHM = "HS256"
TOKEN_MENIT = int(os.getenv("TOKEN_MENIT", "120"))

# origin frontend yang boleh memanggil API, dipisah koma
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# true kalau aplikasi sudah dilayani lewat https
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

ZONA_WAKTU = ZoneInfo("Asia/Jakarta")

# aturan booking
BATAS_HARI_BOOKING = 30
MAKS_DURASI_JAM = 4
MAKS_BOOKING_MENUNGGU = 3
BATAS_REFUND_JAM = 24
