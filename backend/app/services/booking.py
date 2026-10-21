import secrets
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app import waktu
from app.config import BATAS_HARI_BOOKING, MAKS_BOOKING_MENUNGGU
from app.errors import AppError, Conflict, NotFound
from app.models import (
    Booking,
    BookingSlot,
    Court,
    JenisPembayaran,
    ModeKonfirmasi,
    Payment,
    StatusBooking,
    User,
    Venue,
)
from app.schemas import BookingIn, PaymentIn
from app.services import harga, ketersediaan

S = StatusBooking
STATUS_MENUNGGU = (S.MENUNGGU_PEMBAYARAN, S.MENUNGGU_PERSETUJUAN)

def buat_kode_booking(tanggal) -> str:
    return f"LPG-{tanggal:%y%m%d}-{secrets.token_hex(3).upper()}"

def buat_kode_referensi(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6).upper()}"

def opsi_muat_booking():
    # eager loading supaya daftar booking tidak kena N+1 query
    return (
        selectinload(Booking.court).selectinload(Court.venue),
        selectinload(Booking.customer),
        selectinload(Booking.payments),
    )

def ambil_booking(db: Session, kode: str) -> Booking | None:
    return db.scalars(
        select(Booking).options(*opsi_muat_booking()).where(Booking.kode == kode)
    ).first()

def buat_booking(db: Session, customer: User, data: BookingIn) -> Booking:
    ketersediaan.kedaluwarsakan_booking(db)
    court = db.scalars(
        select(Court)
        .options(selectinload(Court.venue).selectinload(Venue.jadwal))
        .where(Court.id == data.court_id)
    ).first()
    if court is None or not court.is_active or not court.venue.is_active:
        raise NotFound("Court tidak ditemukan")
    venue = court.venue

    hari_ini = waktu.hari_ini()
    if data.tanggal < hari_ini:
        raise AppError("Tanggal booking sudah lewat")
    if data.tanggal > hari_ini + timedelta(days=BATAS_HARI_BOOKING):
        raise AppError(f"Booking paling jauh {BATAS_HARI_BOOKING} hari ke depan")

    jam = ketersediaan.jam_operasional(venue, data.tanggal)
    if jam is None:
        raise AppError("Venue tutup pada tanggal tersebut")
    jam_selesai = data.jam_mulai + data.durasi
    if data.jam_mulai < jam[0] or jam_selesai > jam[1]:
        raise AppError(f"Di luar jam operasional venue ({jam[0]:02d}:00 sampai {jam[1]:02d}:00)")
    if waktu.mulai_slot(data.tanggal, data.jam_mulai) <= waktu.sekarang():
        raise AppError("Jam mulai sudah lewat, pilih jam berikutnya")

    rentang = range(data.jam_mulai, jam_selesai)
    penutupan = ketersediaan.peta_penutupan(db, [court.id], data.tanggal, data.tanggal)
    if any(p.menutup(j) for p in penutupan.get((court.id, data.tanggal), []) for j in rentang):
        raise Conflict("Court sedang ditutup pada jam tersebut")

    menunggu = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(Booking.customer_id == customer.id, Booking.status == S.MENUNGGU_PEMBAYARAN)
    )
    if menunggu >= MAKS_BOOKING_MENUNGGU:
        raise AppError(
            f"Masih ada {menunggu} booking yang belum dibayar. Selesaikan atau batalkan dulu."
        )

    # lapis pertama: cek di aplikasi supaya pesan error jelas
    bentrok = db.scalars(
        select(BookingSlot.jam).where(
            BookingSlot.court_id == court.id,
            BookingSlot.tanggal == data.tanggal,
            BookingSlot.jam.in_(list(rentang)),
            BookingSlot.aktif.is_(True),
        )
    ).all()
    if bentrok:
        daftar = ", ".join(f"{j:02d}:00" for j in sorted(bentrok))
        raise Conflict(f"Slot {daftar} sudah dipesan, pilih jam lain")

    tarif = harga.tarif_per_jam(court, data.tanggal)
    total = tarif * data.durasi
    booking = Booking(
        kode=buat_kode_booking(data.tanggal),
        customer_id=customer.id,
        court_id=court.id,
        tanggal=data.tanggal,
        jam_mulai=data.jam_mulai,
        jam_selesai=jam_selesai,
        total_harga=total,
        nominal_deposit=harga.hitung_deposit(total, venue.persen_deposit),
        jumlah_dibayar=0,
        status=S.MENUNGGU_PEMBAYARAN,
        catatan=data.catatan or None,
        batas_bayar=waktu.sekarang() + timedelta(minutes=venue.batas_bayar_menit),
    )
    booking.slots = [
        BookingSlot(court_id=court.id, tanggal=data.tanggal, jam=j, harga=tarif) for j in rentang
    ]
    db.add(booking)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # lapis kedua: indeks unik parsial menolak slot ganda saat dua request balapan
        if "uq_booking_slots_aktif" in str(e.orig):
            raise Conflict("Slot baru saja dipesan orang lain, pilih jam lain") from None
        raise
    return ambil_booking(db, booking.kode)

def _kunci(db: Session, booking: Booking) -> Booking:
    # lepas booking kedaluwarsa dulu, lalu kunci barisnya (SELECT ... FOR UPDATE)
    # supaya dua klik bayar/batal bersamaan tidak diproses dua kali
    ketersediaan.kedaluwarsakan_booking(db)
    db.refresh(booking, with_for_update=True)
    return booking

def _selesai_simpan(db: Session, booking: Booking) -> Booking:
    db.commit()
    return ambil_booking(db, booking.kode)

def _tutup_booking(
    db: Session, booking: Booking, status: StatusBooking, alasan: str, refund: int
) -> None:
    booking.status = status
    booking.alasan_batal = alasan
    booking.dibatalkan_pada = waktu.sekarang()
    booking.batas_bayar = None
    for slot in booking.slots:
        slot.aktif = False
    if refund > 0:
        terakhir = [p for p in booking.payments if p.jenis != JenisPembayaran.REFUND][-1]
        booking.payments.append(
            Payment(
                jenis=JenisPembayaran.REFUND,
                metode=terakhir.metode,
                nominal=refund,
                kode_referensi=buat_kode_referensi("RFD"),
            )
        )

def bayar(db: Session, booking: Booking, data: PaymentIn) -> Booking:
    _kunci(db, booking)
    if booking.status == S.KEDALUWARSA:
        raise AppError("Booking sudah kedaluwarsa karena melewati batas waktu pembayaran")
    if data.jenis == "deposit":
        if booking.status != S.MENUNGGU_PEMBAYARAN:
            raise AppError("Deposit untuk booking ini sudah dibayar")
        jenis, nominal = JenisPembayaran.DEPOSIT, booking.nominal_deposit
    else:
        if booking.status not in (*STATUS_MENUNGGU, S.TERKONFIRMASI):
            raise AppError("Booking ini tidak bisa dilunasi")
        if booking.sisa_tagihan <= 0:
            raise AppError("Booking ini sudah lunas")
        jenis, nominal = JenisPembayaran.PELUNASAN, booking.sisa_tagihan

    booking.jumlah_dibayar += nominal
    booking.payments.append(
        Payment(
            jenis=jenis,
            metode=data.metode,
            nominal=nominal,
            kode_referensi=buat_kode_referensi("PAY"),
        )
    )
    if booking.status == S.MENUNGGU_PEMBAYARAN:
        booking.batas_bayar = None
        if booking.venue.mode_konfirmasi == ModeKonfirmasi.OTOMATIS:
            booking.status = S.TERKONFIRMASI
            booking.dikonfirmasi_pada = waktu.sekarang()
        else:
            booking.status = S.MENUNGGU_PERSETUJUAN
    return _selesai_simpan(db, booking)

def batalkan_oleh_customer(db: Session, booking: Booking, alasan: str | None) -> Booking:
    _kunci(db, booking)
    if not booking.bisa_dibatalkan:
        raise AppError("Booking ini sudah tidak bisa dibatalkan")
    _tutup_booking(
        db, booking, S.DIBATALKAN, alasan or "Dibatalkan oleh customer", booking.perkiraan_refund
    )
    return _selesai_simpan(db, booking)

def setujui(db: Session, booking: Booking) -> Booking:
    _kunci(db, booking)
    if booking.status not in STATUS_MENUNGGU:
        raise AppError("Hanya booking yang masih menunggu yang bisa disetujui")
    if booking.mulai_pada <= waktu.sekarang():
        raise AppError("Jadwal booking ini sudah lewat")
    booking.status = S.TERKONFIRMASI
    booking.dikonfirmasi_pada = waktu.sekarang()
    booking.batas_bayar = None
    return _selesai_simpan(db, booking)

def tolak(db: Session, booking: Booking, alasan: str) -> Booking:
    _kunci(db, booking)
    if booking.status not in STATUS_MENUNGGU:
        raise AppError("Hanya booking yang masih menunggu yang bisa ditolak")
    # ditolak manager = uang kembali penuh
    _tutup_booking(db, booking, S.DITOLAK, alasan, booking.jumlah_dibayar)
    return _selesai_simpan(db, booking)

def batalkan_oleh_manager(db: Session, booking: Booking, alasan: str) -> Booking:
    _kunci(db, booking)
    if booking.status != S.TERKONFIRMASI:
        raise AppError("Hanya booking terkonfirmasi yang bisa dibatalkan manager")
    if booking.mulai_pada <= waktu.sekarang():
        raise AppError("Jadwal booking ini sudah lewat")
    _tutup_booking(db, booking, S.DIBATALKAN, alasan, booking.jumlah_dibayar)
    return _selesai_simpan(db, booking)

def selesaikan(db: Session, booking: Booking) -> Booking:
    _kunci(db, booking)
    if booking.status != S.TERKONFIRMASI:
        raise AppError("Hanya booking terkonfirmasi yang bisa ditandai selesai")
    if booking.mulai_pada > waktu.sekarang():
        raise AppError("Booking baru bisa ditandai selesai setelah jam main dimulai")
    booking.status = S.SELESAI
    return _selesai_simpan(db, booking)
