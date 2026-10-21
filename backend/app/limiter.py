import os

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

def alamat_klien(request: Request) -> str:
    # di Vercel IP asli ada di x-real-ip yang ditulis ulang Vercel, request.client milik proxy
    if os.getenv("VERCEL"):
        return request.headers.get("x-real-ip") or get_remote_address(request)
    return get_remote_address(request)

limiter = Limiter(key_func=alamat_klien)

def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Retry-After ditaruh langsung di response supaya frontend tahu kapan boleh mencoba lagi
    return JSONResponse(
        status_code=429,
        content={"detail": "Terlalu banyak percobaan. Tunggu satu menit lalu coba lagi."},
        headers={"Retry-After": "60"},
    )
