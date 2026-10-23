from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import require_superadmin
from app.models import Role, User
from app.schemas import UserAdminCreateIn, UserAdminOut, UserAdminUpdateIn
from app.security import hash_password

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_superadmin)],
)

def ke_user_admin_out(u: User) -> UserAdminOut:
    venue_names = [v.nama for v in u.venues] if u.venues else []
    return UserAdminOut(
        id=u.id,
        nama=u.nama,
        email=u.email,
        no_hp=u.no_hp,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at,
        venues=venue_names,
    )

@router.get("/users", response_model=list[UserAdminOut], summary="Daftar seluruh akun pengguna")
def daftar_users(
    role: Role | None = None,
    q: str | None = Query(default=None, max_length=60),
    db: Session = Depends(get_db),
):
    query = select(User).options(selectinload(User.venues)).order_by(User.id.desc())
    if role:
        query = query.where(User.role == role)
    if q:
        pola = f"%{q.strip()}%"
        query = query.where(or_(User.nama.ilike(pola), User.email.ilike(pola)))
    users = db.scalars(query).all()
    return [ke_user_admin_out(u) for u in users]

@router.post(
    "/users",
    response_model=UserAdminOut,
    status_code=201,
    summary="Buat akun pengguna baru (manager/customer/superadmin)",
)
def buat_user(
    data: UserAdminCreateIn,
    db: Session = Depends(get_db),
):
    email_clean = data.email.strip().lower()
    ada = db.scalar(select(User.id).where(User.email == email_clean))
    if ada:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    user = User(
        nama=data.nama.strip(),
        email=email_clean,
        no_hp=data.no_hp.strip() if data.no_hp else None,
        role=data.role,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ke_user_admin_out(user)

@router.patch("/users/{user_id}", response_model=UserAdminOut, summary="Perbarui akun pengguna")
def perbarui_user(
    user_id: int,
    data: UserAdminUpdateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    user = db.scalars(
        select(User).options(selectinload(User.venues)).where(User.id == user_id)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")

    if user.id == admin.id:
        if data.is_active is False:
            raise HTTPException(status_code=400, detail="Tidak dapat menonaktifkan akun sendiri")
        if data.role and data.role != Role.SUPERADMIN:
            raise HTTPException(status_code=400, detail="Tidak dapat mengubah role akun sendiri")

    if data.nama is not None:
        user.nama = data.nama.strip()
    if data.no_hp is not None:
        user.no_hp = data.no_hp.strip() or None
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password:
        user.password_hash = hash_password(data.password)

    db.commit()
    db.refresh(user)
    return ke_user_admin_out(user)
