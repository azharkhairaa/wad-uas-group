import enum
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import waktu
from app.config import BATAS_REFUND_JAM
from app.database import Base

class Role(enum.StrEnum):
    CUSTOMER = "customer"
    MANAGER = "manager"
    SUPERADMIN = "superadmin"

class Olahraga(enum.StrEnum):
    TENNIS = "tennis"
    PADEL = "padel"
    FUTSAL = "futsal"
    GOLF_DRIVING = "golf_driving"
    BADMINTON = "badminton"
    VOLI = "voli"
    BASKET = "basket"

class ModeKonfirmasi(enum.StrEnum):
    OTOMATIS = "otomatis"  # terkonfirmasi begitu DP dibayar
    MANUAL = "manual"  # DP dibayar, lalu menunggu persetujuan manager

class StatusBooking(enum.StrEnum):
    MENUNGGU_PEMBAYARAN = "menunggu_pembayaran"
    MENUNGGU_PERSETUJUAN = "menunggu_persetujuan"
    TERKONFIRMASI = "terkonfirmasi"
    SELESAI = "selesai"
    DIBATALKAN = "dibatalkan"
    DITOLAK = "ditolak"
    KEDALUWARSA = "kedaluwarsa"

class JenisPembayaran(enum.StrEnum):
    DEPOSIT = "deposit"
    PELUNASAN = "pelunasan"
    REFUND = "refund"

class MetodePembayaran(enum.StrEnum):
    TRANSFER = "transfer"
    QRIS = "qris"
    EWALLET = "ewallet"

# status yang masih memegang slot di jadwal
STATUS_AKTIF = (
    StatusBooking.MENUNGGU_PEMBAYARAN,
    StatusBooking.MENUNGGU_PERSETUJUAN,
    StatusBooking.TERKONFIRMASI,
    StatusBooking.SELESAI,
)
# status yang dihitung sebagai jam terisi di dashboard okupansi
STATUS_OKUPANSI = (StatusBooking.TERKONFIRMASI, StatusBooking.SELESAI)
STATUS_BISA_BATAL = (
    StatusBooking.MENUNGGU_PEMBAYARAN,
    StatusBooking.MENUNGGU_PERSETUJUAN,
    StatusBooking.TERKONFIRMASI,
)

def kolom_enum(jenis: type[enum.Enum], nama: str) -> Enum:
    # disimpan sebagai varchar + check constraint, isinya nilai huruf kecil
    return Enum(
        jenis,
        name=nama,
        native_enum=False,
        create_constraint=True,
        length=30,
        values_callable=lambda e: [x.value for x in e],
    )

def kolom_dibuat() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    no_hp: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[Role] = mapped_column(kolom_enum(Role, "ck_users_role"), default=Role.CUSTOMER)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = kolom_dibuat()

    venues: Mapped[list["Venue"]] = relationship(back_populates="manager")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="customer")

class Venue(Base):
    __tablename__ = "venues"
    __table_args__ = (
        CheckConstraint("persen_deposit BETWEEN 10 AND 100", name="ck_venues_persen_deposit"),
        CheckConstraint("batas_bayar_menit BETWEEN 10 AND 1440", name="ck_venues_batas_bayar"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    nama: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    kota: Mapped[str] = mapped_column(String(60), index=True)
    alamat: Mapped[str] = mapped_column(String(255))
    deskripsi: Mapped[str | None] = mapped_column(Text)
    telepon: Mapped[str | None] = mapped_column(String(20))
    # dipisah koma, cukup untuk lingkup proyek ini
    fasilitas: Mapped[str | None] = mapped_column(String(255))
    mode_konfirmasi: Mapped[ModeKonfirmasi] = mapped_column(
        kolom_enum(ModeKonfirmasi, "ck_venues_mode_konfirmasi"), default=ModeKonfirmasi.OTOMATIS
    )
    persen_deposit: Mapped[int] = mapped_column(SmallInteger, default=50)
    batas_bayar_menit: Mapped[int] = mapped_column(SmallInteger, default=30)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = kolom_dibuat()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    manager: Mapped[User] = relationship(back_populates="venues")
    courts: Mapped[list["Court"]] = relationship(
        back_populates="venue", order_by="Court.id", cascade="all, delete-orphan"
    )
    jadwal: Mapped[list["VenueSchedule"]] = relationship(
        back_populates="venue", order_by="VenueSchedule.hari", cascade="all, delete-orphan"
    )

    @property
    def daftar_fasilitas(self) -> list[str]:
        if not self.fasilitas:
            return []
        return [f.strip() for f in self.fasilitas.split(",") if f.strip()]

class VenueSchedule(Base):
    """jam buka-tutup rutin per hari, 0 = Senin sampai 6 = Minggu"""

    __tablename__ = "venue_schedules"
    __table_args__ = (
        UniqueConstraint("venue_id", "hari", name="uq_venue_schedules_hari"),
        CheckConstraint("hari BETWEEN 0 AND 6", name="ck_venue_schedules_hari"),
        CheckConstraint(
            "jam_buka >= 0 AND jam_tutup <= 24 AND jam_buka < jam_tutup",
            name="ck_venue_schedules_jam",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    hari: Mapped[int] = mapped_column(SmallInteger)
    jam_buka: Mapped[int] = mapped_column(SmallInteger, default=8)
    jam_tutup: Mapped[int] = mapped_column(SmallInteger, default=22)
    is_tutup: Mapped[bool] = mapped_column(default=False)

    venue: Mapped[Venue] = relationship(back_populates="jadwal")

class Court(Base):
    __tablename__ = "courts"
    __table_args__ = (
        UniqueConstraint("venue_id", "nama", name="uq_courts_nama_per_venue"),
        CheckConstraint("tarif_weekday > 0 AND tarif_weekend > 0", name="ck_courts_tarif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    nama: Mapped[str] = mapped_column(String(60))
    olahraga: Mapped[Olahraga] = mapped_column(
        kolom_enum(Olahraga, "ck_courts_olahraga"), index=True
    )
    permukaan: Mapped[str] = mapped_column(String(60))
    is_indoor: Mapped[bool] = mapped_column(default=True)
    kapasitas: Mapped[int | None] = mapped_column(SmallInteger)
    # tarif per jam, weekday = Senin-Jumat, weekend = Sabtu-Minggu
    tarif_weekday: Mapped[int] = mapped_column(Integer)
    tarif_weekend: Mapped[int] = mapped_column(Integer)
    deskripsi: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = kolom_dibuat()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    venue: Mapped[Venue] = relationship(back_populates="courts")

class CourtClosure(Base):
    """penutupan insidental (maintenance, turnamen), jam kosong = tutup sehari penuh"""

    __tablename__ = "court_closures"
    __table_args__ = (
        CheckConstraint(
            "(jam_mulai IS NULL AND jam_selesai IS NULL) OR "
            "(jam_mulai >= 0 AND jam_selesai <= 24 AND jam_mulai < jam_selesai)",
            name="ck_court_closures_jam",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id", ondelete="CASCADE"), index=True)
    tanggal: Mapped[date] = mapped_column(Date, index=True)
    jam_mulai: Mapped[int | None] = mapped_column(SmallInteger)
    jam_selesai: Mapped[int | None] = mapped_column(SmallInteger)
    alasan: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = kolom_dibuat()

    court: Mapped[Court] = relationship()

    def menutup(self, jam: int) -> bool:
        if self.jam_mulai is None:
            return True
        return self.jam_mulai <= jam < self.jam_selesai

class Booking(Base):
    """satu booking = satu court, satu tanggal, beberapa jam berurutan"""

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint(
            "jam_mulai >= 0 AND jam_selesai <= 24 AND jam_mulai < jam_selesai",
            name="ck_bookings_jam",
        ),
        CheckConstraint(
            "jumlah_dibayar >= 0 AND jumlah_dibayar <= total_harga", name="ck_bookings_dibayar"
        ),
        Index("ix_bookings_court_tanggal", "court_id", "tanggal"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kode: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id", ondelete="RESTRICT"), index=True)
    tanggal: Mapped[date] = mapped_column(Date)
    jam_mulai: Mapped[int] = mapped_column(SmallInteger)
    jam_selesai: Mapped[int] = mapped_column(SmallInteger)
    # harga dibekukan saat booking dibuat, perubahan tarif tidak mengubah tagihan lama
    total_harga: Mapped[int] = mapped_column(Integer)
    nominal_deposit: Mapped[int] = mapped_column(Integer)
    jumlah_dibayar: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[StatusBooking] = mapped_column(
        kolom_enum(StatusBooking, "ck_bookings_status"),
        default=StatusBooking.MENUNGGU_PEMBAYARAN,
        index=True,
    )
    catatan: Mapped[str | None] = mapped_column(String(300))
    alasan_batal: Mapped[str | None] = mapped_column(String(200))
    batas_bayar: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dikonfirmasi_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dibatalkan_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = kolom_dibuat()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped[User] = relationship(back_populates="bookings")
    court: Mapped[Court] = relationship()
    slots: Mapped[list["BookingSlot"]] = relationship(
        back_populates="booking", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="booking", order_by="Payment.id", cascade="all, delete-orphan"
    )

    @property
    def venue(self) -> Venue:
        return self.court.venue

    @property
    def durasi(self) -> int:
        return self.jam_selesai - self.jam_mulai

    @property
    def sisa_tagihan(self) -> int:
        return self.total_harga - self.jumlah_dibayar

    @property
    def mulai_pada(self) -> datetime:
        return waktu.mulai_slot(self.tanggal, self.jam_mulai)

    @property
    def bisa_dibatalkan(self) -> bool:
        return self.status in STATUS_BISA_BATAL and self.mulai_pada > waktu.sekarang()

    @property
    def perkiraan_refund(self) -> int:
        # DP hangus kalau batal kurang dari 24 jam sebelum main
        if self.jumlah_dibayar == 0:
            return 0
        sisa_jam = (self.mulai_pada - waktu.sekarang()).total_seconds() / 3600
        if sisa_jam >= BATAS_REFUND_JAM:
            return self.jumlah_dibayar
        return max(0, self.jumlah_dibayar - self.nominal_deposit)

class BookingSlot(Base):
    """satu baris per jam yang dipesan

    indeks unik parsial uq_booking_slots_aktif adalah penjaga bentrok lapis kedua,
    PostgreSQL menolak dua slot aktif di court, tanggal dan jam yang sama walau
    dua request datang bersamaan
    """

    __tablename__ = "booking_slots"
    __table_args__ = (
        Index(
            "uq_booking_slots_aktif",
            "court_id",
            "tanggal",
            "jam",
            unique=True,
            postgresql_where=text("aktif"),
        ),
        CheckConstraint("jam BETWEEN 0 AND 23", name="ck_booking_slots_jam"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id", ondelete="RESTRICT"))
    tanggal: Mapped[date] = mapped_column(Date)
    jam: Mapped[int] = mapped_column(SmallInteger)
    harga: Mapped[int] = mapped_column(Integer)
    aktif: Mapped[bool] = mapped_column(default=True)

    booking: Mapped[Booking] = relationship(back_populates="slots")

class Payment(Base):
    """pembayaran simulasi, tidak terhubung ke payment gateway sungguhan"""

    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("nominal > 0", name="ck_payments_nominal"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )
    jenis: Mapped[JenisPembayaran] = mapped_column(kolom_enum(JenisPembayaran, "ck_payments_jenis"))
    metode: Mapped[MetodePembayaran] = mapped_column(
        kolom_enum(MetodePembayaran, "ck_payments_metode")
    )
    nominal: Mapped[int] = mapped_column(Integer)
    kode_referensi: Mapped[str] = mapped_column(String(24), unique=True)
    created_at: Mapped[datetime] = kolom_dibuat()

    booking: Mapped[Booking] = relationship(back_populates="payments")
