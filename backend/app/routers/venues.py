from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app import waktu
from app.database import get_db
from app.deps import get_optional_user
from app.models import Court, Olahraga, User, Venue
from app.schemas import KalenderHari, KetersediaanVenue, VenueDetail, VenueRingkas
from app.services import ketersediaan

router = APIRouter(prefix="/api/v1/venues", tags=["venues"])

def court_aktif(venue: Venue, olahraga: Olahraga | None = None) -> list[Court]:
    return [
        c for c in venue.courts if c.is_active and (olahraga is None or c.olahraga == olahraga)
    ]

def ke_ringkas(venue: Venue) -> dict:
    courts = court_aktif(venue)
    return {
        "id": venue.id,
        "slug": venue.slug,
        "nama": venue.nama,
        "kota": venue.kota,
        "alamat": venue.alamat,
        "mode_konfirmasi": venue.mode_konfirmasi,
        "persen_deposit": venue.persen_deposit,
        "fasilitas": venue.daftar_fasilitas,
        "olahraga": sorted({c.olahraga for c in courts}, key=list(Olahraga).index),
        "jumlah_court": len(courts),
        "tarif_mulai": min((c.tarif_weekday for c in courts), default=None),
    }

def ke_detail(venue: Venue, semua_court: bool = False) -> dict:
    return {
        "id": venue.id,
        "slug": venue.slug,
        "nama": venue.nama,
        "kota": venue.kota,
        "alamat": venue.alamat,
        "deskripsi": venue.deskripsi,
        "telepon": venue.telepon,
        "fasilitas": venue.daftar_fasilitas,
        "mode_konfirmasi": venue.mode_konfirmasi,
        "persen_deposit": venue.persen_deposit,
        "batas_bayar_menit": venue.batas_bayar_menit,
        "is_active": venue.is_active,
        "jadwal": venue.jadwal,
        "courts": venue.courts if semua_court else court_aktif(venue),
    }

def ambil_venue_publik(db: Session, slug: str) -> Venue:
    venue = db.scalars(
        select(Venue)
        .options(selectinload(Venue.courts), selectinload(Venue.jadwal))
        .where(Venue.slug == slug, Venue.is_active.is_(True))
    ).first()
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue tidak ditemukan")
    return venue

@router.get(
    "",
    response_model=list[VenueRingkas],
    summary="Daftar venue",
    description="Bisa disaring dengan kata kunci (nama atau alamat), kota dan jenis olahraga.",
)
def daftar_venue(
    q: str | None = Query(default=None, max_length=60),
    kota: str | None = Query(default=None, max_length=60),
    olahraga: Olahraga | None = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Venue)
        .options(selectinload(Venue.courts))
        .where(Venue.is_active.is_(True))
        .order_by(Venue.nama)
    )
    if q:
        pola = f"%{q.strip()}%"
        stmt = stmt.where(or_(Venue.nama.ilike(pola), Venue.alamat.ilike(pola)))
    if kota:
        stmt = stmt.where(Venue.kota.ilike(kota.strip()))
    if olahraga:
        stmt = stmt.where(
            Venue.courts.any((Court.olahraga == olahraga) & Court.is_active.is_(True))
        )
    return [ke_ringkas(v) for v in db.scalars(stmt).all()]

@router.get("/{slug}", response_model=VenueDetail, summary="Detail venue beserta court dan tarif")
def detail_venue(slug: str, db: Session = Depends(get_db)):
    return ke_detail(ambil_venue_publik(db, slug))

@router.get(
    "/{slug}/availability",
    response_model=KetersediaanVenue,
    summary="Ketersediaan slot per court untuk satu tanggal",
    description=(
        "Status slot: tersedia, menunggu (ditahan booking lain yang belum selesai), dipesan, "
        "milik_saya (booking milik pengguna yang login), ditutup (maintenance) dan lewat."
    ),
)
def ketersediaan_slot(
    slug: str,
    tanggal: date,
    olahraga: Olahraga | None = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if abs((tanggal - waktu.hari_ini()).days) > 366:
        raise HTTPException(status_code=400, detail="Tanggal di luar rentang yang didukung")
    ketersediaan.kedaluwarsakan_booking(db)
    venue = ambil_venue_publik(db, slug)
    return ketersediaan.ketersediaan_venue(
        db, venue, tanggal, court_aktif(venue, olahraga), user.id if user else None
    )

@router.get(
    "/{slug}/calendar",
    response_model=list[KalenderHari],
    summary="Kalender ketersediaan per hari",
    description="Jumlah slot tersedia per tanggal, dipakai untuk strip kalender di halaman venue.",
)
def kalender(
    slug: str,
    mulai: date | None = None,
    hari: int = Query(default=14, ge=1, le=31),
    olahraga: Olahraga | None = None,
    court_id: int | None = None,
    db: Session = Depends(get_db),
):
    mulai = mulai or waktu.hari_ini()
    if abs((mulai - waktu.hari_ini()).days) > 366:
        raise HTTPException(status_code=400, detail="Tanggal di luar rentang yang didukung")
    ketersediaan.kedaluwarsakan_booking(db)
    venue = ambil_venue_publik(db, slug)
    courts = court_aktif(venue, olahraga)
    if court_id is not None:
        courts = [c for c in courts if c.id == court_id]
    return ketersediaan.kalender_venue(db, venue, courts, mulai, hari)
