import secrets

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.security import decode_access_token

ACCESS_COOKIE = "access_token"
CSRF_COOKIE = "csrf_token"
METODE_AMAN = ("GET", "HEAD", "OPTIONS")

# auto_error=False: header kosong belum tentu 401, cek cookie dulu
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

def _belum_login() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Belum login atau sesi sudah berakhir",
        headers={"WWW-Authenticate": "Bearer"},
    )

def _baca_user(
    request: Request, token: str | None, x_csrf_token: str | None, db: Session
) -> User | None:
    dari_cookie = token is None
    if dari_cookie:
        token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    # token dari cookie wajib membawa CSRF token untuk request yang mengubah data
    if dari_cookie and request.method not in METODE_AMAN:
        cookie_csrf = request.cookies.get(CSRF_COOKIE, "")
        if not x_csrf_token or not secrets.compare_digest(
            cookie_csrf.encode(), x_csrf_token.encode()
        ):
            raise HTTPException(status_code=403, detail="Token CSRF tidak valid")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user

def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    x_csrf_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    user = _baca_user(request, token, x_csrf_token, db)
    if user is None:
        raise _belum_login()
    return user

def get_optional_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    # dipakai di endpoint publik (GET), token rusak dianggap tamu
    return _baca_user(request, token, None, db)

def require_customer(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.CUSTOMER:
        raise HTTPException(status_code=403, detail="Fitur ini khusus akun customer")
    return user

def require_manager(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.MANAGER:
        raise HTTPException(status_code=403, detail="Fitur ini khusus venue manager")
    return user
