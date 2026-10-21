from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import ALGORITHM, SECRET_KEY, TOKEN_MENIT

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# hash palsu supaya waktu login tetap sama walau email tidak terdaftar
HASH_DUMMY = hash_password("password-dummy-tidak-dipakai")

def verify_password(password: str, password_hash: str) -> bool:
    data = password.encode()
    if not password_hash or len(data) > 72:
        return False
    return bcrypt.checkpw(data, password_hash.encode())

def create_access_token(user_id: int, role: str) -> str:
    sekarang = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": sekarang,
        "exp": sekarang + timedelta(minutes=TOKEN_MENIT),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None
