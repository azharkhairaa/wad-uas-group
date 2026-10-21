from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Retry-After ditaruh langsung di response supaya frontend tahu kapan boleh mencoba lagi
    return JSONResponse(
        status_code=429,
        content={"detail": "Terlalu banyak percobaan. Tunggu satu menit lalu coba lagi."},
        headers={"Retry-After": "60"},
    )
