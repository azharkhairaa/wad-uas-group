from datetime import date, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import waktu
from app.models import (
    Booking,
    BookingSlot,
    Court,
    CourtClosure,
    StatusBooking,
    Venue,
    VenueSchedule,
)
from app.services import harga

STATUS_DITAHAN = (StatusBooking.MENUNGGU_PEMBAYARAN, StatusBooking.MENUNGGU_PERSETUJUAN)

def kedaluwarsakan_booking(db: Session) -> int:
    """lepas slot milik booking yang lewat batas bayar, dipanggil sebelum membaca jadwal"""
    now = waktu.sekarang()
    ids = db.scalars(
        select(Booking.id).where(
            Booking.status == StatusBooking.MENUNGGU_PEMBAYARAN,
            Booking.batas_bayar < now,
        )
    ).all()
    if not ids:
        return 0
    db.execute(
        update(Booking)
        .where(Booking.id.in_(ids))
        .values(
            status=StatusBooking.KEDALUWARSA,
            dibatalkan_pada=now,
            alasan_batal="Batas waktu pembayaran terlewati",
        )
    )
    db.execute(update(BookingSlot).where(BookingSlot.booking_id.in_(ids)).values(aktif=False))
    db.commit()
    return len(ids)

def jadwal_hari(venue: Venue, tanggal: date) -> VenueSchedule | None:
    for jadwal in venue.jadwal:
        if jadwal.hari == tanggal.weekday():
            return jadwal
    return None

def jam_operasional(venue: Venue, tanggal: date) -> tuple[int, int] | None:
    """(jam_buka, jam_tutup) atau None kalau venue tutup hari itu"""
    jadwal = jadwal_hari(venue, tanggal)
    if jadwal is None or jadwal.is_tutup:
        return None
    return jadwal.jam_buka, jadwal.jam_tutup

def peta_terisi(
    db: Session, court_ids: list[int], dari: date, sampai: date
) -> dict[tuple[int, date, int], tuple[StatusBooking, int, str]]:
    """(court_id, tanggal, jam) -> (status booking, customer_id, kode) untuk slot aktif"""
    if not court_ids:
        return {}
    rows = db.execute(
        select(
            BookingSlot.court_id,
            BookingSlot.tanggal,
            BookingSlot.jam,
            Booking.status,
            Booking.customer_id,
            Booking.kode,
        )
        .join(Booking, Booking.id == BookingSlot.booking_id)
        .where(
            BookingSlot.court_id.in_(court_ids),
            BookingSlot.tanggal.between(dari, sampai),
            BookingSlot.aktif.is_(True),
        )
    ).all()
    return {(r.court_id, r.tanggal, r.jam): (r.status, r.customer_id, r.kode) for r in rows}

def peta_penutupan(
    db: Session, court_ids: list[int], dari: date, sampai: date
) -> dict[tuple[int, date], list[CourtClosure]]:
    if not court_ids:
        return {}
    hasil: dict[tuple[int, date], list[CourtClosure]] = {}
    penutupan = db.scalars(
        select(CourtClosure).where(
            CourtClosure.court_id.in_(court_ids),
            CourtClosure.tanggal.between(dari, sampai),
        )
    ).all()
    for p in penutupan:
        hasil.setdefault((p.court_id, p.tanggal), []).append(p)
    return hasil

def status_slot(
    court_id: int,
    tanggal: date,
    jam: int,
    terisi: dict,
    penutupan: dict,
    now: datetime,
    user_id: int | None = None,
) -> str:
    if waktu.mulai_slot(tanggal, jam) <= now:
        return "lewat"
    isi = terisi.get((court_id, tanggal, jam))
    if isi:
        status, customer_id, _ = isi
        if user_id is not None and customer_id == user_id:
            return "milik_saya"
        return "menunggu" if status in STATUS_DITAHAN else "dipesan"
    if any(p.menutup(jam) for p in penutupan.get((court_id, tanggal), [])):
        return "ditutup"
    return "tersedia"

def ketersediaan_venue(
    db: Session, venue: Venue, tanggal: date, courts: list[Court], user_id: int | None = None
) -> dict:
    jam = jam_operasional(venue, tanggal)
    hasil = {
        "tanggal": tanggal,
        "hari": waktu.NAMA_HARI[tanggal.weekday()],
        "is_weekend": waktu.is_weekend(tanggal),
        "is_tutup": jam is None,
        "jam_buka": jam[0] if jam else None,
        "jam_tutup": jam[1] if jam else None,
        "courts": [],
    }
    court_ids = [c.id for c in courts]
    terisi = peta_terisi(db, court_ids, tanggal, tanggal) if jam else {}
    penutupan = peta_penutupan(db, court_ids, tanggal, tanggal) if jam else {}
    now = waktu.sekarang()
    for court in courts:
        tarif = harga.tarif_per_jam(court, tanggal)
        slots = []
        if jam:
            for j in range(jam[0], jam[1]):
                status = status_slot(court.id, tanggal, j, terisi, penutupan, now, user_id)
                slots.append({"jam": j, "label": f"{j:02d}:00", "status": status, "harga": tarif})
        hasil["courts"].append(
            {
                "court": court,
                "tarif_per_jam": tarif,
                "slot_tersedia": sum(1 for s in slots if s["status"] == "tersedia"),
                "slots": slots,
            }
        )
    return hasil

def kalender_venue(
    db: Session, venue: Venue, courts: list[Court], mulai: date, jumlah_hari: int
) -> list[dict]:
    sampai = mulai + timedelta(days=jumlah_hari - 1)
    court_ids = [c.id for c in courts]
    terisi = peta_terisi(db, court_ids, mulai, sampai)
    penutupan = peta_penutupan(db, court_ids, mulai, sampai)
    now = waktu.sekarang()
    hasil = []
    for i in range(jumlah_hari):
        tanggal = mulai + timedelta(days=i)
        jam = jam_operasional(venue, tanggal)
        total = tersedia = 0
        if jam:
            for court in courts:
                for j in range(jam[0], jam[1]):
                    total += 1
                    if status_slot(court.id, tanggal, j, terisi, penutupan, now) == "tersedia":
                        tersedia += 1
        hasil.append(
            {
                "tanggal": tanggal,
                "hari": waktu.NAMA_HARI[tanggal.weekday()],
                "is_weekend": waktu.is_weekend(tanggal),
                "is_tutup": jam is None,
                "total_slot": total,
                "slot_tersedia": tersedia,
            }
        )
    return hasil
