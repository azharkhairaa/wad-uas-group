import re
from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.config import MAKS_DURASI_JAM
from app.models import (
    JenisPembayaran,
    MetodePembayaran,
    ModeKonfirmasi,
    Olahraga,
    Role,
    StatusBooking,
)

class InputModel(BaseModel):
    # field di luar skema ditolak, mencegah mass assignment (mis. kirim role=manager)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class OutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# ---------- auth

class RegisterIn(InputModel):
    nama: str = Field(min_length=2, max_length=100)
    email: EmailStr
    no_hp: str | None = Field(default=None, pattern=r"^\+?[0-9]{9,15}$")
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def email_huruf_kecil(cls, nilai: str) -> str:
        return nilai.lower()

    @field_validator("password")
    @classmethod
    def password_kuat(cls, nilai: str) -> str:
        # bcrypt hanya membaca 72 byte pertama
        if len(nilai.encode()) > 72:
            raise ValueError("password maksimal 72 byte")
        if not re.search(r"[A-Za-z]", nilai) or not re.search(r"\d", nilai):
            raise ValueError("password harus berisi huruf dan angka")
        return nilai

class LoginIn(InputModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def email_huruf_kecil(cls, nilai: str) -> str:
        return nilai.lower()

class UserOut(OutputModel):
    id: int
    nama: str
    email: str
    no_hp: str | None
    role: Role

class LoginOut(BaseModel):
    user: UserOut
    csrf_token: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---------- venue, court, jadwal

class JadwalOut(OutputModel):
    hari: int
    jam_buka: int
    jam_tutup: int
    is_tutup: bool

class JadwalIn(InputModel):
    hari: int = Field(ge=0, le=6)
    jam_buka: int = Field(ge=0, le=23)
    jam_tutup: int = Field(ge=1, le=24)
    is_tutup: bool = False

    @model_validator(mode="after")
    def jam_masuk_akal(self):
        if self.jam_buka >= self.jam_tutup:
            raise ValueError("jam tutup harus setelah jam buka")
        return self

class CourtOut(OutputModel):
    id: int
    venue_id: int
    nama: str
    olahraga: Olahraga
    permukaan: str
    is_indoor: bool
    kapasitas: int | None
    tarif_weekday: int
    tarif_weekend: int
    deskripsi: str | None
    is_active: bool

class CourtIn(InputModel):
    nama: str = Field(min_length=2, max_length=60)
    olahraga: Olahraga
    permukaan: str = Field(min_length=2, max_length=60)
    is_indoor: bool = True
    kapasitas: int | None = Field(default=None, ge=1, le=50)
    tarif_weekday: int = Field(ge=10_000, le=10_000_000)
    tarif_weekend: int = Field(ge=10_000, le=10_000_000)
    deskripsi: str | None = Field(default=None, max_length=255)

class CourtUpdate(InputModel):
    nama: str | None = Field(default=None, min_length=2, max_length=60)
    olahraga: Olahraga | None = None
    permukaan: str | None = Field(default=None, min_length=2, max_length=60)
    is_indoor: bool | None = None
    kapasitas: int | None = Field(default=None, ge=1, le=50)
    tarif_weekday: int | None = Field(default=None, ge=10_000, le=10_000_000)
    tarif_weekend: int | None = Field(default=None, ge=10_000, le=10_000_000)
    deskripsi: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None

class VenueRingkas(OutputModel):
    id: int
    slug: str
    nama: str
    kota: str
    alamat: str
    mode_konfirmasi: ModeKonfirmasi
    persen_deposit: int
    fasilitas: list[str]
    olahraga: list[Olahraga]
    jumlah_court: int
    tarif_mulai: int | None

class VenueDetail(OutputModel):
    id: int
    slug: str
    nama: str
    kota: str
    alamat: str
    deskripsi: str | None
    telepon: str | None
    fasilitas: list[str]
    mode_konfirmasi: ModeKonfirmasi
    persen_deposit: int
    batas_bayar_menit: int
    jadwal: list[JadwalOut]
    courts: list[CourtOut]

class VenueManagerOut(VenueDetail):
    is_active: bool

class VenueIn(InputModel):
    nama: str = Field(min_length=3, max_length=120)
    kota: str = Field(min_length=3, max_length=60)
    alamat: str = Field(min_length=5, max_length=255)
    deskripsi: str | None = Field(default=None, max_length=2000)
    telepon: str | None = Field(default=None, pattern=r"^\+?[0-9]{9,15}$")
    fasilitas: list[str] = Field(default_factory=list, max_length=15)
    mode_konfirmasi: ModeKonfirmasi = ModeKonfirmasi.OTOMATIS
    persen_deposit: int = Field(default=50, ge=10, le=100)
    batas_bayar_menit: int = Field(default=30, ge=10, le=1440)

class VenueUpdate(InputModel):
    nama: str | None = Field(default=None, min_length=3, max_length=120)
    kota: str | None = Field(default=None, min_length=3, max_length=60)
    alamat: str | None = Field(default=None, min_length=5, max_length=255)
    deskripsi: str | None = Field(default=None, max_length=2000)
    telepon: str | None = Field(default=None, pattern=r"^\+?[0-9]{9,15}$")
    fasilitas: list[str] | None = Field(default=None, max_length=15)
    mode_konfirmasi: ModeKonfirmasi | None = None
    persen_deposit: int | None = Field(default=None, ge=10, le=100)
    batas_bayar_menit: int | None = Field(default=None, ge=10, le=1440)
    is_active: bool | None = None

# ---------- ketersediaan slot

StatusSlot = Literal["tersedia", "menunggu", "dipesan", "milik_saya", "ditutup", "lewat"]

class SlotOut(BaseModel):
    jam: int
    label: str
    status: StatusSlot
    harga: int

class KetersediaanCourt(BaseModel):
    court: CourtOut
    tarif_per_jam: int
    slot_tersedia: int
    slots: list[SlotOut]

class KetersediaanVenue(BaseModel):
    tanggal: date
    hari: str
    is_weekend: bool
    is_tutup: bool
    jam_buka: int | None
    jam_tutup: int | None
    courts: list[KetersediaanCourt]

class KalenderHari(BaseModel):
    tanggal: date
    hari: str
    is_weekend: bool
    is_tutup: bool
    total_slot: int
    slot_tersedia: int

# ---------- booking & pembayaran

class BookingIn(InputModel):
    court_id: int = Field(gt=0)
    tanggal: date
    jam_mulai: int = Field(ge=0, le=23)
    durasi: int = Field(ge=1, le=MAKS_DURASI_JAM)
    catatan: str | None = Field(default=None, max_length=300)

class PaymentIn(InputModel):
    jenis: Literal["deposit", "pelunasan"]
    metode: MetodePembayaran

class AlasanIn(InputModel):
    alasan: str | None = Field(default=None, max_length=200)

class AlasanWajibIn(InputModel):
    alasan: str = Field(min_length=5, max_length=200)

class PaymentOut(OutputModel):
    id: int
    jenis: JenisPembayaran
    metode: MetodePembayaran
    nominal: int
    kode_referensi: str
    created_at: datetime

class CourtMini(OutputModel):
    id: int
    nama: str
    olahraga: Olahraga

class VenueMini(OutputModel):
    id: int
    slug: str
    nama: str
    kota: str
    mode_konfirmasi: ModeKonfirmasi
    persen_deposit: int

class CustomerMini(OutputModel):
    id: int
    nama: str
    email: str
    no_hp: str | None

class BookingOut(OutputModel):
    id: int
    kode: str
    status: StatusBooking
    tanggal: date
    jam_mulai: int
    jam_selesai: int
    durasi: int
    total_harga: int
    nominal_deposit: int
    jumlah_dibayar: int
    sisa_tagihan: int
    catatan: str | None
    alasan_batal: str | None
    batas_bayar: datetime | None
    dikonfirmasi_pada: datetime | None
    dibatalkan_pada: datetime | None
    created_at: datetime
    court: CourtMini
    venue: VenueMini

class BookingDetailOut(BookingOut):
    payments: list[PaymentOut]
    bisa_dibatalkan: bool
    perkiraan_refund: int

class BookingManagerOut(BookingOut):
    customer: CustomerMini

class BookingManagerDetailOut(BookingDetailOut):
    customer: CustomerMini

class HalamanBooking(BaseModel):
    items: list[BookingManagerOut]
    total: int
    page: int
    per_page: int

# ---------- manager: penutupan, agenda, dashboard

class ClosureIn(InputModel):
    court_id: int = Field(gt=0)
    tanggal: date
    jam_mulai: int | None = Field(default=None, ge=0, le=23)
    jam_selesai: int | None = Field(default=None, ge=1, le=24)
    alasan: str = Field(min_length=3, max_length=160)

    @model_validator(mode="after")
    def jam_lengkap(self):
        if (self.jam_mulai is None) != (self.jam_selesai is None):
            raise ValueError("isi jam mulai dan jam selesai atau kosongkan keduanya")
        if self.jam_mulai is not None and self.jam_mulai >= self.jam_selesai:
            raise ValueError("jam selesai harus setelah jam mulai")
        return self

class ClosureOut(OutputModel):
    id: int
    court_id: int
    tanggal: date
    jam_mulai: int | None
    jam_selesai: int | None
    alasan: str
    court: CourtMini

class AgendaItem(BaseModel):
    jenis: Literal["booking", "penutupan"]
    jam_mulai: int
    jam_selesai: int
    kode: str | None = None
    status: StatusBooking | None = None
    nama_customer: str | None = None
    alasan: str | None = None

class AgendaCourt(BaseModel):
    court: CourtMini
    items: list[AgendaItem]

class AgendaOut(BaseModel):
    tanggal: date
    hari: str
    is_tutup: bool
    jam_buka: int | None
    jam_tutup: int | None
    courts: list[AgendaCourt]

class Okupansi(BaseModel):
    jam_terisi: int
    jam_tersedia: int
    okupansi_persen: float

class OkupansiHarian(Okupansi):
    tanggal: date
    is_mendatang: bool

class OkupansiCourt(Okupansi):
    court_id: int
    nama: str
    olahraga: Olahraga

class OkupansiOlahraga(Okupansi):
    olahraga: Olahraga

class JamSibuk(BaseModel):
    jam: int
    jumlah: int

class JumlahStatus(BaseModel):
    status: StatusBooking
    jumlah: int

class RingkasanDashboard(Okupansi):
    pendapatan: int
    booking_terkonfirmasi: int
    menunggu_tindakan: int
    booking_hari_ini: int

class DashboardOut(BaseModel):
    dari: date
    sampai: date
    ringkasan: RingkasanDashboard
    harian: list[OkupansiHarian]
    per_court: list[OkupansiCourt]
    per_olahraga: list[OkupansiOlahraga]
    jam_sibuk: list[JamSibuk]
    status: list[JumlahStatus]

class UserAdminOut(OutputModel):
    id: int
    nama: str
    email: str
    no_hp: str | None
    role: Role
    is_active: bool
    created_at: datetime
    venues: list[str] = []

class UserAdminCreateIn(InputModel):
    nama: str = Field(min_length=2, max_length=100)
    email: EmailStr
    no_hp: str | None = Field(default=None, max_length=20)
    role: Role = Role.MANAGER
    password: str = Field(min_length=6, max_length=100)

class UserAdminUpdateIn(InputModel):
    nama: str | None = Field(default=None, min_length=2, max_length=100)
    no_hp: str | None = Field(default=None, max_length=20)
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=100)

