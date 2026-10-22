import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import waktu
from app.database import get_db
from app.deps import require_manager
from app.models import (
    STATUS_AKTIF,
    Booking,
    BookingSlot,
    Court,
    CourtClosure,
    StatusBooking,
    User,
    Venue,
    VenueSchedule,
)
from app.routers.venues import ke_detail
from app.schemas import (
    AgendaOut,
    AlasanWajibIn,
    BookingManagerDetailOut,
    ClosureIn,
    ClosureOut,
    CourtIn,
    CourtOut,
    CourtUpdate,
    DashboardOut,
    HalamanBooking,
    JadwalIn,
    JadwalOut,
    PaymentIn,
    VenueIn,
    VenueManagerOut,
    VenueUpdate,
)
from app.services import booking as layanan
from app.services import dashboard, ketersediaan

router = APIRouter(
    prefix="/api/v1/manager",
    tags=["manager"],
    dependencies=[Depends(require_manager)],
)

NAMA_COURT_DIPAKAI = "Nama court sudah dipakai di venue ini"

# ---------- penjaga kepemilikan (BOLA): manager hanya bisa menyentuh venue miliknya

def venue_milik(db: Session, venue_id: int, manager: User) -> Venue:
    venue = db.scalars(
        select(Venue)
        .options(selectinload(Venue.courts), selectinload(Venue.jadwal))
        .where(Venue.id == venue_id)
    ).first()
    if venue is None or venue.manager_id != manager.id:
        raise HTTPException(status_code=404, detail="Venue tidak ditemukan")
    return venue

def court_milik(db: Session, court_id: int, manager: User) -> Court:
    court = db.scalars(
        select(Court).options(selectinload(Court.venue)).where(Court.id == court_id)
    ).first()
    if court is None or court.venue.manager_id != manager.id:
        raise HTTPException(status_code=404, detail="Court tidak ditemukan")
    return court

def booking_milik(db: Session, kode: str, manager: User) -> Booking:
    booking = layanan.ambil_booking(db, kode)
    if booking is None or booking.venue.manager_id != manager.id:
        raise HTTPException(status_code=404, detail="Booking tidak ditemukan")
    return booking

def gabung_fasilitas(daftar: list[str]) -> str | None:
    bersih = [" ".join(f.replace(",", " ").split()) for f in daftar if f.strip()]
    return ", ".join(bersih)[:255] or None

def buat_slug(db: Session, nama: str) -> str:
    dasar = re.sub(r"[^a-z0-9]+", "-", nama.lower()).strip("-")[:120] or "venue"
    slug, nomor = dasar, 2
    while db.scalar(select(Venue.id).where(Venue.slug == slug)):
        slug = f"{dasar}-{nomor}"
        nomor += 1
    return slug

# ---------- venue

@router.get("/venues", response_model=list[VenueManagerOut], summary="Venue yang saya kelola")
def daftar_venue(db: Session = Depends(get_db), manager: User = Depends(require_manager)):
    venues = db.scalars(
        select(Venue)
        .options(selectinload(Venue.courts), selectinload(Venue.jadwal))
        .where(Venue.manager_id == manager.id)
        .order_by(Venue.nama)
    ).all()
    return [ke_detail(v, semua_court=True) for v in venues]

@router.post(
    "/venues",
    response_model=VenueManagerOut,
    status_code=201,
    summary="Tambah venue",
    description="Jadwal awal otomatis 08:00 sampai 22:00 setiap hari, bisa diubah setelahnya.",
)
def tambah_venue(
    data: VenueIn, db: Session = Depends(get_db), manager: User = Depends(require_manager)
):
    venue = Venue(
        manager_id=manager.id,
        slug=buat_slug(db, data.nama),
        **data.model_dump(exclude={"fasilitas"}),
        fasilitas=gabung_fasilitas(data.fasilitas),
    )
    venue.jadwal = [VenueSchedule(hari=h, jam_buka=8, jam_tutup=22) for h in range(7)]
    db.add(venue)
    db.commit()
    return ke_detail(venue_milik(db, venue.id, manager), semua_court=True)

@router.get("/venues/{venue_id}", response_model=VenueManagerOut, summary="Detail venue saya")
def detail_venue(
    venue_id: int, db: Session = Depends(get_db), manager: User = Depends(require_manager)
):
    return ke_detail(venue_milik(db, venue_id, manager), semua_court=True)

@router.patch(
    "/venues/{venue_id}",
    response_model=VenueManagerOut,
    summary="Ubah profil venue, mode konfirmasi dan deposit",
)
def ubah_venue(
    venue_id: int,
    data: VenueUpdate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    venue = venue_milik(db, venue_id, manager)
    perubahan = data.model_dump(exclude_unset=True)
    if "fasilitas" in perubahan:
        perubahan["fasilitas"] = gabung_fasilitas(perubahan["fasilitas"] or [])
    for kolom, nilai in perubahan.items():
        setattr(venue, kolom, nilai)
    db.commit()
    return ke_detail(venue_milik(db, venue_id, manager), semua_court=True)

# ---------- jadwal operasional

@router.get(
    "/venues/{venue_id}/schedule", response_model=list[JadwalOut], summary="Jam operasional"
)
def jadwal(venue_id: int, db: Session = Depends(get_db), manager: User = Depends(require_manager)):
    return venue_milik(db, venue_id, manager).jadwal

@router.put(
    "/venues/{venue_id}/schedule",
    response_model=list[JadwalOut],
    summary="Atur jam buka dan tutup mingguan",
    description=(
        "Kirim tepat 7 baris (hari 0 = Senin sampai 6 = Minggu). Ditolak 409 kalau ada "
        "booking aktif yang jatuh di luar jam baru."
    ),
)
def ubah_jadwal(
    venue_id: int,
    data: list[JadwalIn],
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    if sorted(j.hari for j in data) != list(range(7)):
        raise HTTPException(
            status_code=422, detail="Jadwal harus berisi 7 hari, Senin sampai Minggu"
        )
    venue = venue_milik(db, venue_id, manager)
    baru = {j.hari: j for j in data}

    mendatang = db.scalars(
        select(Booking)
        .join(Court, Court.id == Booking.court_id)
        .where(
            Court.venue_id == venue.id,
            Booking.tanggal >= waktu.hari_ini(),
            Booking.status.in_(STATUS_AKTIF),
        )
    ).all()
    terdampak = [
        b.kode
        for b in mendatang
        if (j := baru[b.tanggal.weekday()]).is_tutup
        or b.jam_mulai < j.jam_buka
        or b.jam_selesai > j.jam_tutup
    ]
    if terdampak:
        raise HTTPException(
            status_code=409,
            detail=f"Ada {len(terdampak)} booking aktif di luar jam baru, mis. {terdampak[0]}. "
            "Selesaikan atau batalkan dulu booking tersebut.",
        )
    for jadwal_lama in venue.jadwal:
        j = baru[jadwal_lama.hari]
        jadwal_lama.jam_buka, jadwal_lama.jam_tutup, jadwal_lama.is_tutup = (
            j.jam_buka,
            j.jam_tutup,
            j.is_tutup,
        )
    db.commit()
    return venue_milik(db, venue_id, manager).jadwal

# ---------- court & tarif

@router.get(
    "/venues/{venue_id}/courts", response_model=list[CourtOut], summary="Court di venue saya"
)
def daftar_court(
    venue_id: int, db: Session = Depends(get_db), manager: User = Depends(require_manager)
):
    return venue_milik(db, venue_id, manager).courts

@router.post(
    "/venues/{venue_id}/courts",
    response_model=CourtOut,
    status_code=201,
    summary="Tambah court beserta tarif weekday dan weekend",
)
def tambah_court(
    venue_id: int,
    data: CourtIn,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    venue = venue_milik(db, venue_id, manager)
    court = Court(venue_id=venue.id, **data.model_dump())
    db.add(court)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=NAMA_COURT_DIPAKAI) from None
    db.refresh(court)
    return court

@router.patch("/courts/{court_id}", response_model=CourtOut, summary="Ubah court atau tarif")
def ubah_court(
    court_id: int,
    data: CourtUpdate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    court = court_milik(db, court_id, manager)
    for kolom, nilai in data.model_dump(exclude_unset=True).items():
        if nilai is None and kolom not in ("kapasitas", "deskripsi"):
            continue
        setattr(court, kolom, nilai)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=NAMA_COURT_DIPAKAI) from None
    db.refresh(court)
    return court

@router.delete(
    "/courts/{court_id}",
    status_code=204,
    summary="Hapus court",
    description="Court yang sudah punya riwayat booking tidak bisa dihapus, nonaktifkan saja.",
)
def hapus_court(
    court_id: int, db: Session = Depends(get_db), manager: User = Depends(require_manager)
):
    court = court_milik(db, court_id, manager)
    ada_booking = db.scalar(select(Booking.id).where(Booking.court_id == court.id).limit(1))
    if ada_booking:
        raise HTTPException(
            status_code=409,
            detail="Court ini sudah punya riwayat booking. "
            "Nonaktifkan saja supaya riwayat tetap utuh.",
        )
    db.delete(court)
    db.commit()
    return Response(status_code=204)

# ---------- penutupan sementara

@router.get(
    "/venues/{venue_id}/closures",
    response_model=list[ClosureOut],
    summary="Daftar penutupan court",
)
def daftar_penutupan(
    venue_id: int,
    dari: date | None = None,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    venue = venue_milik(db, venue_id, manager)
    return db.scalars(
        select(CourtClosure)
        .options(selectinload(CourtClosure.court))
        .join(Court, Court.id == CourtClosure.court_id)
        .where(Court.venue_id == venue.id, CourtClosure.tanggal >= (dari or waktu.hari_ini()))
        .order_by(CourtClosure.tanggal, CourtClosure.jam_mulai)
    ).all()

@router.post(
    "/venues/{venue_id}/closures",
    response_model=ClosureOut,
    status_code=201,
    summary="Tutup court sementara (maintenance, turnamen)",
    description="Ditolak 409 kalau masih ada booking aktif di rentang yang ditutup.",
)
def tambah_penutupan(
    venue_id: int,
    data: ClosureIn,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    venue = venue_milik(db, venue_id, manager)
    if data.court_id not in {c.id for c in venue.courts}:
        raise HTTPException(status_code=404, detail="Court tidak ditemukan di venue ini")
    if data.tanggal < waktu.hari_ini():
        raise HTTPException(status_code=400, detail="Tanggal penutupan sudah lewat")
    penutupan = CourtClosure(**data.model_dump())
    stmt = (
        select(Booking.kode)
        .join(BookingSlot, BookingSlot.booking_id == Booking.id)
        .where(
            BookingSlot.court_id == data.court_id,
            BookingSlot.tanggal == data.tanggal,
            BookingSlot.aktif.is_(True),
        )
        .distinct()
    )
    if data.jam_mulai is not None:
        stmt = stmt.where(BookingSlot.jam >= data.jam_mulai, BookingSlot.jam < data.jam_selesai)
    bentrok = db.scalars(stmt).all()
    if bentrok:
        raise HTTPException(
            status_code=409,
            detail=f"Masih ada booking aktif di jam tersebut ({', '.join(bentrok[:3])}). "
            "Batalkan atau pindahkan dulu.",
        )
    db.add(penutupan)
    db.commit()
    db.refresh(penutupan)
    return penutupan

@router.delete("/closures/{closure_id}", status_code=204, summary="Buka lagi court yang ditutup")
def hapus_penutupan(
    closure_id: int, db: Session = Depends(get_db), manager: User = Depends(require_manager)
):
    penutupan = db.get(CourtClosure, closure_id)
    if penutupan is None:
        raise HTTPException(status_code=404, detail="Penutupan tidak ditemukan")
    court_milik(db, penutupan.court_id, manager)
    db.delete(penutupan)
    db.commit()
    return Response(status_code=204)

# ---------- booking masuk

@router.get(
    "/bookings",
    response_model=HalamanBooking,
    summary="Booking masuk di venue saya",
    description="Urut dari yang terbaru dibuat. q mencari kode booking atau nama customer.",
)
def booking_masuk(
    venue_id: int | None = None,
    status: StatusBooking | None = None,
    tanggal: date | None = None,
    court_id: int | None = None,
    q: str | None = Query(default=None, max_length=60),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    ketersediaan.kedaluwarsakan_booking(db)
    if venue_id is not None:
        venue_ids = [venue_milik(db, venue_id, manager).id]
    else:
        venue_ids = db.scalars(select(Venue.id).where(Venue.manager_id == manager.id)).all()

    filter_ = [Court.venue_id.in_(venue_ids)]
    if status:
        filter_.append(Booking.status == status)
    if tanggal:
        filter_.append(Booking.tanggal == tanggal)
    if court_id:
        filter_.append(Booking.court_id == court_id)
    if q:
        pola = f"%{q.strip()}%"
        filter_.append(or_(Booking.kode.ilike(pola), User.nama.ilike(pola)))

    dasar = (
        select(Booking)
        .join(Court, Court.id == Booking.court_id)
        .join(User, User.id == Booking.customer_id)
        .where(*filter_)
    )
    total = db.scalar(select(func.count()).select_from(dasar.subquery()))
    items = db.scalars(
        dasar.options(*layanan.opsi_muat_booking())
        .order_by(Booking.created_at.desc(), Booking.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()
    return {"items": items, "total": total, "page": page, "per_page": per_page}

@router.get("/bookings/{kode}", response_model=BookingManagerDetailOut, summary="Detail booking")
def detail_booking(
    kode: str, db: Session = Depends(get_db), manager: User = Depends(require_manager)
):
    return booking_milik(db, kode, manager)

@router.post(
    "/bookings/{kode}/approve",
    response_model=BookingManagerDetailOut,
    summary="Setujui booking",
    description="Untuk booking menunggu pembayaran (bayar di lokasi) atau menunggu persetujuan.",
)
def setujui(kode: str, db: Session = Depends(get_db), manager: User = Depends(require_manager)):
    return layanan.setujui(db, booking_milik(db, kode, manager))

@router.post(
    "/bookings/{kode}/reject",
    response_model=BookingManagerDetailOut,
    summary="Tolak booking",
    description="Slot dilepas dan pembayaran yang sudah masuk dikembalikan penuh.",
)
def tolak(
    kode: str,
    data: AlasanWajibIn,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    return layanan.tolak(db, booking_milik(db, kode, manager), data.alasan)

@router.post(
    "/bookings/{kode}/complete",
    response_model=BookingManagerDetailOut,
    summary="Tandai booking selesai",
)
def selesai(kode: str, db: Session = Depends(get_db), manager: User = Depends(require_manager)):
    return layanan.selesaikan(db, booking_milik(db, kode, manager))

@router.post(
    "/bookings/{kode}/payments",
    response_model=BookingManagerDetailOut,
    summary="Catat pembayaran pelunasan oleh manager",
    description="Manager mencatat pelunasan langsung jika customer membayar di lokasi venue.",
)
def catat_pelunasan(
    kode: str,
    data: PaymentIn,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    return layanan.bayar(db, booking_milik(db, kode, manager), data)


@router.post(
    "/bookings/{kode}/cancel",
    response_model=BookingManagerDetailOut,
    summary="Batalkan booking terkonfirmasi",
    description="Misalnya court rusak. Pembayaran dikembalikan penuh.",
)
def batalkan(
    kode: str,
    data: AlasanWajibIn,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    return layanan.batalkan_oleh_manager(db, booking_milik(db, kode, manager), data.alasan)

# ---------- agenda & dashboard

@router.get(
    "/venues/{venue_id}/agenda",
    response_model=AgendaOut,
    summary="Agenda harian semua court",
)
def agenda(
    venue_id: int,
    tanggal: date | None = None,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    ketersediaan.kedaluwarsakan_booking(db)
    venue = venue_milik(db, venue_id, manager)
    return dashboard.agenda(db, venue, tanggal or waktu.hari_ini())

@router.get(
    "/venues/{venue_id}/dashboard",
    response_model=DashboardOut,
    summary="Ringkasan okupansi dan booking",
    description=(
        "Okupansi = jam terisi (booking terkonfirmasi atau selesai) dibagi jam buka court. "
        "Default 14 hari ke belakang sampai 7 hari ke depan."
    ),
)
def ringkasan(
    venue_id: int,
    dari: date | None = None,
    sampai: date | None = None,
    db: Session = Depends(get_db),
    manager: User = Depends(require_manager),
):
    hari_ini = waktu.hari_ini()
    dari = dari or hari_ini - timedelta(days=13)
    sampai = sampai or hari_ini + timedelta(days=7)
    if sampai < dari or (sampai - dari).days > 92:
        raise HTTPException(status_code=400, detail="Rentang tanggal maksimal 93 hari")
    ketersediaan.kedaluwarsakan_booking(db)
    venue = venue_milik(db, venue_id, manager)
    return dashboard.ringkasan(db, venue, dari, sampai)
