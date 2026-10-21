from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_customer
from app.models import Booking, StatusBooking, User
from app.schemas import AlasanIn, BookingDetailOut, BookingIn, BookingOut, PaymentIn
from app.services import booking as layanan
from app.services import ketersediaan

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

def booking_milik(db: Session, kode: str, customer: User) -> Booking:
    booking = layanan.ambil_booking(db, kode)
    # milik orang lain dijawab 404 juga, supaya keberadaan kode booking tidak bocor (BOLA)
    if booking is None or booking.customer_id != customer.id:
        raise HTTPException(status_code=404, detail="Booking tidak ditemukan")
    return booking

@router.post(
    "",
    response_model=BookingDetailOut,
    status_code=201,
    summary="Buat booking",
    description=(
        "Memesan beberapa jam berurutan di satu court. Slot ditahan sampai batas bayar venue "
        "(default 30 menit). Bentrok jadwal dijawab 409."
    ),
)
def buat_booking(
    data: BookingIn,
    db: Session = Depends(get_db),
    customer: User = Depends(require_customer),
):
    return layanan.buat_booking(db, customer, data)

@router.get("", response_model=list[BookingOut], summary="Riwayat booking milik customer")
def riwayat_booking(
    status: StatusBooking | None = None,
    db: Session = Depends(get_db),
    customer: User = Depends(require_customer),
):
    ketersediaan.kedaluwarsakan_booking(db)
    stmt = (
        select(Booking)
        .options(*layanan.opsi_muat_booking())
        .where(Booking.customer_id == customer.id)
        .order_by(Booking.tanggal.desc(), Booking.jam_mulai.desc())
        .limit(200)
    )
    if status:
        stmt = stmt.where(Booking.status == status)
    return db.scalars(stmt).all()

@router.get("/{kode}", response_model=BookingDetailOut, summary="Detail booking")
def detail_booking(
    kode: str, db: Session = Depends(get_db), customer: User = Depends(require_customer)
):
    ketersediaan.kedaluwarsakan_booking(db)
    return booking_milik(db, kode, customer)

@router.post(
    "/{kode}/payments",
    response_model=BookingDetailOut,
    summary="Bayar deposit atau pelunasan (simulasi)",
    description=(
        "Pembayaran disimulasikan, tanpa payment gateway. Venue mode otomatis langsung "
        "mengonfirmasi booking begitu deposit dibayar, mode manual menunggu persetujuan manager."
    ),
)
def bayar(
    kode: str,
    data: PaymentIn,
    db: Session = Depends(get_db),
    customer: User = Depends(require_customer),
):
    return layanan.bayar(db, booking_milik(db, kode, customer), data)

@router.post(
    "/{kode}/cancel",
    response_model=BookingDetailOut,
    summary="Batalkan booking",
    description=(
        "Slot langsung dilepas. Batal paling lambat 24 jam sebelum main, uang kembali penuh. "
        "Kurang dari itu, deposit tidak dikembalikan."
    ),
)
def batalkan(
    kode: str,
    data: AlasanIn,
    db: Session = Depends(get_db),
    customer: User = Depends(require_customer),
):
    return layanan.batalkan_oleh_customer(db, booking_milik(db, kode, customer), data.alasan)
