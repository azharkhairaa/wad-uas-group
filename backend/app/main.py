import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import CORS_ORIGINS, STATIC_DIR
from app.database import get_db
from app.errors import AppError
from app.limiter import limiter, rate_limit_handler
from app.routers import admin, auth, bookings, manager, venues

log = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Lapangin API",
    description=(
        "Backend booking lapang olahraga (tennis, padel, futsal, golf driving, badminton, "
        "voli, basket). Fokus pada ketersediaan slot per jam dan pencegahan bentrok jadwal."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Register, login (cookie atau Bearer), logout"},
        {"name": "venues", "description": "Katalog venue, court, tarif dan ketersediaan slot"},
        {"name": "bookings", "description": "Booking milik customer dan pembayaran simulasi"},
        {"name": "manager", "description": "Khusus venue manager, kelola court sampai dashboard"},
        {"name": "admin", "description": "Khusus superadmin, kelola akun pengguna dan manager"},
        {"name": "system", "description": "Health check"},
    ],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# allow frontend Vite (5173), credentials untuk cookie sesi
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    # halaman /docs butuh script dari CDN, CSP ketat hanya untuk respons API
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
    return response

@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.pesan})

@app.exception_handler(Exception)
def server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # detail error cukup di log server, tidak dikirim ke klien
    log.exception("error tak terduga di %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Terjadi error di server"})

app.include_router(auth.router)
app.include_router(venues.router)
app.include_router(bookings.router)
app.include_router(manager.router)
app.include_router(admin.router)

@app.get("/api/health", tags=["system"], summary="Cek API dan koneksi database")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

# di image produksi FastAPI ikut menyajikan build Vue, cookie sesi dan CSRF tetap satu origin
web = Path(STATIC_DIR) if STATIC_DIR else None
if web and (web / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path == "api" or path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        berkas = (web / path).resolve()
        if path and berkas.is_file() and berkas.is_relative_to(web.resolve()):
            return FileResponse(berkas)
        # route Vue (history mode) dijawab index.html, router di browser yang memilih halaman
        return FileResponse(web / "index.html", headers={"Cache-Control": "no-cache"})
