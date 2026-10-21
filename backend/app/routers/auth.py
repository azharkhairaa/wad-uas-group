import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import COOKIE_SECURE, TOKEN_MENIT
from app.database import get_db
from app.deps import ACCESS_COOKIE, CSRF_COOKIE, get_current_user
from app.limiter import limiter
from app.models import Role, User
from app.schemas import LoginIn, LoginOut, RegisterIn, TokenOut, UserOut
from app.security import HASH_DUMMY, create_access_token, hash_password, verify_password

log = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

def cek_kredensial(db: Session, email: str, password: str) -> User:
    user = db.scalars(select(User).where(User.email == email.lower())).first()
    hash_tersimpan = user.password_hash if user else ""
    # bcrypt selalu dijalankan supaya waktu respons tidak membocorkan email yang terdaftar
    benar = verify_password(password, hash_tersimpan or HASH_DUMMY)
    if user is None or not hash_tersimpan or not benar or not user.is_active:
        log.warning("login gagal email=%r", email)
        raise HTTPException(
            status_code=401,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
    summary="Daftar akun customer",
    description=(
        "Membuat akun baru dengan peran customer. Peran tidak bisa dipilih dari request, "
        "akun venue manager hanya dibuat oleh pengelola sistem."
    ),
)
@limiter.limit("10/minute")
def register(request: Request, data: RegisterIn, db: Session = Depends(get_db)):
    user = User(
        nama=data.nama,
        email=data.email,
        no_hp=data.no_hp,
        password_hash=hash_password(data.password),
        role=Role.CUSTOMER,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email sudah terdaftar") from None
    db.refresh(user)
    return user

@router.post(
    "/login",
    response_model=LoginOut,
    summary="Login untuk aplikasi web",
    description=(
        "Menyimpan JWT di cookie httpOnly dan mengirim CSRF token. Request yang mengubah data "
        "wajib membawa header X-CSRF-Token berisi nilai yang sama dengan cookie csrf_token."
    ),
)
@limiter.limit("10/minute")
def login(request: Request, response: Response, data: LoginIn, db: Session = Depends(get_db)):
    user = cek_kredensial(db, data.email, data.password)
    csrf = secrets.token_urlsafe(24)
    umur = TOKEN_MENIT * 60
    response.set_cookie(
        ACCESS_COOKIE,
        create_access_token(user.id, user.role),
        max_age=umur,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    response.set_cookie(
        CSRF_COOKIE, csrf, max_age=umur, httponly=False, samesite="lax", secure=COOKIE_SECURE
    )
    return {"user": user, "csrf_token": csrf}

@router.post(
    "/token",
    response_model=TokenOut,
    summary="Login untuk Swagger atau Postman",
    description=(
        "Mengembalikan access token untuk header Authorization: Bearer. "
        "Isi kolom username dengan email."
    ),
)
@limiter.limit("10/minute")
def token(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = cek_kredensial(db, form.username, form.password)
    return {"access_token": create_access_token(user.id, user.role)}

@router.post("/logout", summary="Logout", description="Menghapus cookie sesi.")
def logout(response: Response):
    response.delete_cookie(ACCESS_COOKIE, samesite="lax", secure=COOKIE_SECURE)
    response.delete_cookie(CSRF_COOKIE, samesite="lax", secure=COOKIE_SECURE)
    return {"pesan": "Anda sudah keluar"}

@router.get("/me", response_model=UserOut, summary="Profil pengguna yang sedang login")
def me(user: User = Depends(get_current_user)):
    return user
