import threading
from datetime import datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app import waktu
from app.config import ZONA_WAKTU
from app.main import app
from app.models import Booking, BookingSlot, CourtClosure, StatusBooking
from app.services.harga import hitung_deposit
from tests.conftest import PASSWORD, booking_json, buat_user, buat_venue, tanggal_depan

SENIN, SABTU = 0, 5

def test_booking_berhasil_menahan_slot(login, customer, venue_court):
    _, court = venue_court
    client = login(customer.email)
    res = client.post("/api/v1/bookings", json=booking_json(court, tanggal_depan(SENIN), 19, 2))
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "menunggu_pembayaran"
    assert (data["jam_mulai"], data["jam_selesai"], data["durasi"]) == (19, 21, 2)
    assert data["total_harga"] == 200_000
    assert data["nominal_deposit"] == 100_000
    assert data["kode"].startswith("LPG-")
    batas = datetime.fromisoformat(data["batas_bayar"])
    assert timedelta(minutes=29) < batas - waktu.sekarang() <= timedelta(minutes=30)

def test_tarif_weekday_dan_weekend(login, customer, venue_court):
    _, court = venue_court
    client = login(customer.email)
    senin = client.post("/api/v1/bookings", json=booking_json(court, tanggal_depan(SENIN)))
    sabtu = client.post("/api/v1/bookings", json=booking_json(court, tanggal_depan(SABTU)))
    assert senin.json()["total_harga"] == 100_000
    assert sabtu.json()["total_harga"] == 150_000

@pytest.mark.parametrize(
    ("jam_mulai", "durasi", "kode_status"),
    [
        (19, 1, 409),  # persis sama
        (18, 2, 409),  # beririsan di jam 19
        (20, 2, 409),  # beririsan di jam 20
        (17, 2, 201),  # bersebelahan sebelum
        (21, 1, 201),  # bersebelahan sesudah
    ],
)
def test_validasi_bentrok(login, customer, customer_lain, venue_court, jam_mulai, durasi, kode_status):
    _, court = venue_court
    tanggal = tanggal_depan(SENIN)
    pertama = login(customer.email).post(
        "/api/v1/bookings", json=booking_json(court, tanggal, 19, 2)
    )
    assert pertama.status_code == 201
    res = login(customer_lain.email).post(
        "/api/v1/bookings", json=booking_json(court, tanggal, jam_mulai, durasi)
    )
    assert res.status_code == kode_status, res.text
    if kode_status == 409:
        assert "sudah dipesan" in res.json()["detail"]

@pytest.mark.parametrize(
    ("ubah", "pesan"),
    [
        ({"jam_mulai": 7}, "Di luar jam operasional"),
        ({"jam_mulai": 21, "durasi": 2}, "Di luar jam operasional"),
        ({"tanggal": "2020-01-01"}, "sudah lewat"),
        ({"tanggal": "far"}, "paling jauh 30 hari"),
    ],
)
def test_aturan_tanggal_dan_jam(login, customer, venue_court, ubah, pesan):
    _, court = venue_court
    data = booking_json(court, tanggal_depan(SENIN))
    if ubah.get("tanggal") == "far":
        ubah = {"tanggal": (waktu.hari_ini() + timedelta(days=31)).isoformat()}
    data.update(ubah)
    res = login(customer.email).post("/api/v1/bookings", json=data)
    assert res.status_code == 400
    assert pesan in res.json()["detail"]

def test_durasi_maksimal_4_jam(login, customer, venue_court):
    _, court = venue_court
    res = login(customer.email).post(
        "/api/v1/bookings", json=booking_json(court, tanggal_depan(SENIN), 10, 5)
    )
    assert res.status_code == 422

def test_venue_tutup_di_hari_tertentu(db, login, customer, manager):
    _, court = buat_venue(db, manager, nama="Tutup Senin", hari_tutup=(SENIN,))
    res = login(customer.email).post("/api/v1/bookings", json=booking_json(court, tanggal_depan(SENIN)))
    assert res.status_code == 400
    assert "tutup" in res.json()["detail"]

def test_jam_yang_sudah_lewat_ditolak(login, customer, venue_court, monkeypatch):
    _, court = venue_court
    besok = waktu.hari_ini() + timedelta(days=1)
    jam_15 = datetime.combine(besok, time(15, 30), tzinfo=ZONA_WAKTU)
    monkeypatch.setattr(waktu, "sekarang", lambda: jam_15)
    client = login(customer.email)
    assert client.post("/api/v1/bookings", json=booking_json(court, besok, 15)).status_code == 400
    assert client.post("/api/v1/bookings", json=booking_json(court, besok, 16)).status_code == 201

def test_court_nonaktif_tidak_bisa_dipesan(db, login, customer, venue_court):
    _, court = venue_court
    court.is_active = False
    db.commit()
    res = login(customer.email).post("/api/v1/bookings", json=booking_json(court, tanggal_depan(SENIN)))
    assert res.status_code == 404

def test_court_ditutup_maintenance(db, login, customer, venue_court):
    _, court = venue_court
    tanggal = tanggal_depan(SENIN)
    db.add(CourtClosure(court_id=court.id, tanggal=tanggal, jam_mulai=18, jam_selesai=20, alasan="Servis"))
    db.commit()
    client = login(customer.email)
    assert client.post("/api/v1/bookings", json=booking_json(court, tanggal, 19)).status_code == 409
    assert client.post("/api/v1/bookings", json=booking_json(court, tanggal, 20)).status_code == 201

def test_maksimal_3_booking_menunggu_pembayaran(login, customer, venue_court):
    _, court = venue_court
    client = login(customer.email)
    tanggal = tanggal_depan(SENIN)
    for jam in (10, 12, 14):
        assert client.post("/api/v1/bookings", json=booking_json(court, tanggal, jam)).status_code == 201
    res = client.post("/api/v1/bookings", json=booking_json(court, tanggal, 16))
    assert res.status_code == 400
    assert "belum dibayar" in res.json()["detail"]

def test_deposit_dibulatkan_ke_atas_per_seribu():
    assert hitung_deposit(200_000, 50) == 100_000
    assert hitung_deposit(125_000, 30) == 38_000
    assert hitung_deposit(150_000, 100) == 150_000

def _booking_langsung(db, court, customer, jam=19):
    booking = Booking(
        kode=f"LPG-UJI-{jam}-{customer.id}",
        customer_id=customer.id,
        court_id=court.id,
        tanggal=tanggal_depan(SENIN),
        jam_mulai=jam,
        jam_selesai=jam + 1,
        total_harga=100_000,
        nominal_deposit=50_000,
        status=StatusBooking.MENUNGGU_PEMBAYARAN,
    )
    booking.slots = [
        BookingSlot(court_id=court.id, tanggal=booking.tanggal, jam=jam, harga=100_000)
    ]
    db.add(booking)
    return booking

def test_indeks_unik_parsial_menolak_slot_ganda(db, customer, customer_lain, venue_court):
    # lapis kedua: walau validasi aplikasi dilewati, PostgreSQL tetap menolak
    _, court = venue_court
    _booking_langsung(db, court, customer)
    db.commit()
    _booking_langsung(db, court, customer_lain)
    with pytest.raises(IntegrityError, match="uq_booking_slots_aktif"):
        db.commit()
    db.rollback()

def test_slot_nonaktif_boleh_dipakai_lagi(db, customer, customer_lain, venue_court):
    _, court = venue_court
    lama = _booking_langsung(db, court, customer)
    db.commit()
    lama.status = StatusBooking.DIBATALKAN
    lama.slots[0].aktif = False
    db.commit()
    _booking_langsung(db, court, customer_lain)
    db.commit()

def test_dua_request_bersamaan_hanya_satu_yang_menang(db, venue_court):
    _, court = venue_court
    pemain = [buat_user(db, f"pemain{i}@example.com") for i in range(2)]
    clients = []
    for user in pemain:
        client = TestClient(app)
        res = client.post("/api/v1/auth/login", json={"email": user.email, "password": PASSWORD})
        client.headers["X-CSRF-Token"] = res.json()["csrf_token"]
        clients.append(client)

    data = booking_json(court, tanggal_depan(SENIN), 20)
    mulai = threading.Barrier(len(clients))
    hasil = []

    def pesan(client):
        mulai.wait()
        hasil.append(client.post("/api/v1/bookings", json=data).status_code)

    threads = [threading.Thread(target=pesan, args=(c,)) for c in clients]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for c in clients:
        c.close()
    assert sorted(hasil) == [201, 409]
