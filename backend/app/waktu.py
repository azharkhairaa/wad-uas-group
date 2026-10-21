from datetime import date, datetime, time, timedelta

from app.config import ZONA_WAKTU

NAMA_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

def sekarang() -> datetime:
    return datetime.now(ZONA_WAKTU)

def hari_ini() -> date:
    return sekarang().date()

def mulai_slot(tanggal: date, jam: int) -> datetime:
    # jam 24 dipakai sebagai batas tutup tengah malam
    return datetime.combine(tanggal, time(0), tzinfo=ZONA_WAKTU) + timedelta(hours=jam)

def is_weekend(tanggal: date) -> bool:
    return tanggal.weekday() >= 5
