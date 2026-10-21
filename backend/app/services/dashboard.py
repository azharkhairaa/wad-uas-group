from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app import waktu
from app.config import ZONA_WAKTU
from app.models import (
    STATUS_AKTIF,
    STATUS_OKUPANSI,
    Booking,
    BookingSlot,
    Court,
    JenisPembayaran,
    Payment,
    StatusBooking,
    Venue,
)
from app.services import ketersediaan

def _persen(terisi: int, tersedia: int) -> float:
    return round(terisi / tersedia * 100, 1) if tersedia else 0.0

def _okupansi(terisi: int, tersedia: int) -> dict:
    return {
        "jam_terisi": terisi,
        "jam_tersedia": tersedia,
        "okupansi_persen": _persen(terisi, tersedia),
    }

def _jam_buka_court(venue: Venue, court: Court, tanggal: date, penutupan: dict) -> int:
    jam = ketersediaan.jam_operasional(venue, tanggal)
    if jam is None:
        return 0
    tutup = penutupan.get((court.id, tanggal), [])
    return sum(1 for j in range(jam[0], jam[1]) if not any(p.menutup(j) for p in tutup))

def ringkasan(db: Session, venue: Venue, dari: date, sampai: date) -> dict:
    courts = [c for c in venue.courts if c.is_active]
    court_ids = [c.id for c in courts]
    hari_ini = waktu.hari_ini()
    jumlah_hari = (sampai - dari).days + 1
    tanggal_list = [dari + timedelta(days=i) for i in range(jumlah_hari)]

    penutupan = ketersediaan.peta_penutupan(db, court_ids, dari, sampai)
    terisi = db.execute(
        select(BookingSlot.court_id, BookingSlot.tanggal, BookingSlot.jam)
        .join(Booking, Booking.id == BookingSlot.booking_id)
        .where(
            BookingSlot.court_id.in_(court_ids),
            BookingSlot.tanggal.between(dari, sampai),
            BookingSlot.aktif.is_(True),
            Booking.status.in_(STATUS_OKUPANSI),
        )
    ).all()

    terisi_tanggal = Counter(r.tanggal for r in terisi)
    terisi_court = Counter(r.court_id for r in terisi)
    jam_sibuk = Counter(r.jam for r in terisi)
    tersedia_tanggal: Counter = Counter()
    tersedia_court: Counter = Counter()
    for tanggal in tanggal_list:
        for court in courts:
            jam = _jam_buka_court(venue, court, tanggal, penutupan)
            tersedia_tanggal[tanggal] += jam
            tersedia_court[court.id] += jam

    harian = [
        {
            "tanggal": t,
            "is_mendatang": t > hari_ini,
            **_okupansi(terisi_tanggal[t], tersedia_tanggal[t]),
        }
        for t in tanggal_list
    ]
    per_court = [
        {
            "court_id": c.id,
            "nama": c.nama,
            "olahraga": c.olahraga,
            **_okupansi(terisi_court[c.id], tersedia_court[c.id]),
        }
        for c in courts
    ]
    per_olahraga_raw: dict = defaultdict(lambda: [0, 0])
    for c in courts:
        per_olahraga_raw[c.olahraga][0] += terisi_court[c.id]
        per_olahraga_raw[c.olahraga][1] += tersedia_court[c.id]
    per_olahraga = [
        {"olahraga": o, **_okupansi(isi, sedia)} for o, (isi, sedia) in per_olahraga_raw.items()
    ]
    per_olahraga.sort(key=lambda x: x["okupansi_persen"], reverse=True)

    jam_list = [j.jam_buka for j in venue.jadwal if not j.is_tutup]
    jam_akhir = [j.jam_tutup for j in venue.jadwal if not j.is_tutup]
    rentang_jam = range(min(jam_list, default=8), max(jam_akhir, default=22))
    sibuk = [{"jam": j, "jumlah": jam_sibuk[j]} for j in rentang_jam]

    di_venue = Court.venue_id == venue.id
    status_rows = db.execute(
        select(Booking.status, func.count())
        .join(Court, Court.id == Booking.court_id)
        .where(di_venue, Booking.tanggal.between(dari, sampai))
        .group_by(Booking.status)
    ).all()
    jumlah_status = dict(status_rows)

    awal = datetime.combine(dari, time(0), tzinfo=ZONA_WAKTU)
    akhir = datetime.combine(sampai + timedelta(days=1), time(0), tzinfo=ZONA_WAKTU)
    nilai = case((Payment.jenis == JenisPembayaran.REFUND, -Payment.nominal), else_=Payment.nominal)
    pendapatan = db.scalar(
        select(func.coalesce(func.sum(nilai), 0))
        .join(Booking, Booking.id == Payment.booking_id)
        .join(Court, Court.id == Booking.court_id)
        .where(di_venue, Payment.created_at >= awal, Payment.created_at < akhir)
    )
    menunggu_tindakan = db.scalar(
        select(func.count())
        .select_from(Booking)
        .join(Court, Court.id == Booking.court_id)
        .where(
            di_venue,
            Booking.status == StatusBooking.MENUNGGU_PERSETUJUAN,
            Booking.tanggal >= hari_ini,
        )
    )
    booking_hari_ini = db.scalar(
        select(func.count())
        .select_from(Booking)
        .join(Court, Court.id == Booking.court_id)
        .where(di_venue, Booking.tanggal == hari_ini, Booking.status.in_(STATUS_AKTIF))
    )

    total_terisi = sum(terisi_tanggal.values())
    total_tersedia = sum(tersedia_tanggal.values())
    return {
        "dari": dari,
        "sampai": sampai,
        "ringkasan": {
            **_okupansi(total_terisi, total_tersedia),
            "pendapatan": int(pendapatan or 0),
            "booking_terkonfirmasi": sum(jumlah_status.get(s, 0) for s in STATUS_OKUPANSI),
            "menunggu_tindakan": menunggu_tindakan or 0,
            "booking_hari_ini": booking_hari_ini or 0,
        },
        "harian": harian,
        "per_court": per_court,
        "per_olahraga": per_olahraga,
        "jam_sibuk": sibuk,
        "status": [
            {"status": s, "jumlah": jumlah_status[s]} for s in StatusBooking if s in jumlah_status
        ],
    }

def agenda(db: Session, venue: Venue, tanggal: date) -> dict:
    courts = [c for c in venue.courts if c.is_active]
    jam = ketersediaan.jam_operasional(venue, tanggal)
    bookings = db.scalars(
        select(Booking)
        .options(selectinload(Booking.customer))
        .join(Court, Court.id == Booking.court_id)
        .where(
            Court.venue_id == venue.id,
            Booking.tanggal == tanggal,
            Booking.status.in_(STATUS_AKTIF),
        )
        .order_by(Booking.jam_mulai)
    ).all()
    penutupan = ketersediaan.peta_penutupan(db, [c.id for c in courts], tanggal, tanggal)

    per_court = []
    for court in courts:
        items = [
            {
                "jenis": "booking",
                "jam_mulai": b.jam_mulai,
                "jam_selesai": b.jam_selesai,
                "kode": b.kode,
                "status": b.status,
                "nama_customer": b.customer.nama,
            }
            for b in bookings
            if b.court_id == court.id
        ]
        buka, tutup = jam or (0, 24)
        for p in penutupan.get((court.id, tanggal), []):
            # penutupan sehari penuh digambar selebar jam operasional
            items.append(
                {
                    "jenis": "penutupan",
                    "jam_mulai": buka if p.jam_mulai is None else p.jam_mulai,
                    "jam_selesai": tutup if p.jam_selesai is None else p.jam_selesai,
                    "alasan": p.alasan,
                }
            )
        items.sort(key=lambda x: x["jam_mulai"])
        per_court.append({"court": court, "items": items})

    return {
        "tanggal": tanggal,
        "hari": waktu.NAMA_HARI[tanggal.weekday()],
        "is_tutup": jam is None,
        "jam_buka": jam[0] if jam else None,
        "jam_tutup": jam[1] if jam else None,
        "courts": per_court,
    }
