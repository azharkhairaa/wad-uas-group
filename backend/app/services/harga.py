from datetime import date

from app.models import Court
from app.waktu import is_weekend

def tarif_per_jam(court: Court, tanggal: date) -> int:
    return court.tarif_weekend if is_weekend(tanggal) else court.tarif_weekday

def hitung_total(court: Court, tanggal: date, durasi: int) -> int:
    return tarif_per_jam(court, tanggal) * durasi

def hitung_deposit(total: int, persen: int) -> int:
    # dibulatkan ke atas per seribu rupiah, tidak pernah melebihi total
    per_seribu = -(-total * persen // 100_000)
    return min(total, per_seribu * 1000)
