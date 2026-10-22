"""alur status booking: pembayaran, konfirmasi otomatis/manual, batal, tolak, kedaluwarsa"""

from datetime import datetime, time, timedelta

from sqlalchemy import update

from app import waktu
from app.config import ZONA_WAKTU
from app.models import Booking, CourtClosure, ModeKonfirmasi
from tests.conftest import booking_json, buat_venue, tanggal_depan

SENIN = 0
DEPOSIT = {"jenis": "deposit", "metode": "qris"}
LUNAS = {"jenis": "pelunasan", "metode": "transfer"}

def _pesan(client, court, tanggal=None, jam=19, durasi=2):
    res = client.post("/api/v1/bookings", json=booking_json(court, tanggal or tanggal_depan(SENIN), jam, durasi))
    assert res.status_code == 201, res.text
    return res.json()["kode"]

def test_mode_otomatis_terkonfirmasi_setelah_deposit(login, customer, venue_court):
    _, court = venue_court
    client = login(customer.email)
    kode = _pesan(client, court)
    res = client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "terkonfirmasi"
    assert data["jumlah_dibayar"] == 100_000
    assert data["sisa_tagihan"] == 100_000
    assert data["batas_bayar"] is None
    assert [p["jenis"] for p in data["payments"]] == ["deposit"]

    lunas = client.post(f"/api/v1/bookings/{kode}/payments", json=LUNAS).json()
    assert lunas["sisa_tagihan"] == 0
    assert client.post(f"/api/v1/bookings/{kode}/payments", json=LUNAS).status_code == 400

def test_deposit_tidak_bisa_dibayar_dua_kali(login, customer, venue_court):
    _, court = venue_court
    client = login(customer.email)
    kode = _pesan(client, court)
    assert client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT).status_code == 200
    res = client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT)
    assert res.status_code == 400

def test_mode_manual_menunggu_persetujuan_manager(db, login, customer, manager):
    _, court = buat_venue(db, manager, nama="Venue Manual", mode=ModeKonfirmasi.MANUAL)
    client = login(customer.email)
    kode = _pesan(client, court)
    res = client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT)
    assert res.json()["status"] == "menunggu_persetujuan"

    pengelola = login(manager.email)
    masuk = pengelola.get("/api/v1/manager/bookings", params={"status": "menunggu_persetujuan"})
    assert [b["kode"] for b in masuk.json()["items"]] == [kode]
    res = pengelola.post(f"/api/v1/manager/bookings/{kode}/approve")
    assert res.status_code == 200
    assert res.json()["status"] == "terkonfirmasi"
    assert client.get(f"/api/v1/bookings/{kode}").json()["dikonfirmasi_pada"] is not None

def test_manager_bisa_menyetujui_tanpa_deposit(login, customer, manager, venue_court):
    # misalnya customer bayar langsung di lokasi
    _, court = venue_court
    kode = _pesan(login(customer.email), court)
    res = login(manager.email).post(f"/api/v1/manager/bookings/{kode}/approve")
    assert res.json()["status"] == "terkonfirmasi"

def test_ditolak_manager_refund_penuh_dan_slot_bebas(db, login, customer, customer_lain, manager):
    _, court = buat_venue(db, manager, nama="Venue Manual", mode=ModeKonfirmasi.MANUAL)
    client = login(customer.email)
    kode = _pesan(client, court)
    client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT)

    pengelola = login(manager.email)
    assert pengelola.post(f"/api/v1/manager/bookings/{kode}/reject", json={"alasan": "x"}).status_code == 422
    res = pengelola.post(
        f"/api/v1/manager/bookings/{kode}/reject", json={"alasan": "Court dipakai turnamen"}
    )
    data = res.json()
    assert data["status"] == "ditolak"
    assert data["payments"][-1]["jenis"] == "refund"
    assert data["payments"][-1]["nominal"] == 100_000
    # slot yang sama bisa dipesan orang lain
    _pesan(login(customer_lain.email), court)

def test_batal_lebih_dari_24_jam_refund_penuh(login, customer, customer_lain, venue_court):
    _, court = venue_court
    client = login(customer.email)
    kode = _pesan(client, court)
    client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT)
    detail = client.get(f"/api/v1/bookings/{kode}").json()
    assert detail["bisa_dibatalkan"] is True
    assert detail["perkiraan_refund"] == 100_000

    res = client.post(f"/api/v1/bookings/{kode}/cancel", json={"alasan": "Tim kurang orang"})
    data = res.json()
    assert data["status"] == "dibatalkan"
    assert data["payments"][-1] == {**data["payments"][-1], "jenis": "refund", "nominal": 100_000}
    _pesan(login(customer_lain.email), court)

def test_batal_mendadak_deposit_hangus(login, customer, venue_court, monkeypatch):
    _, court = venue_court
    client = login(customer.email)
    tanggal = tanggal_depan(SENIN)
    kode = _pesan(client, court, tanggal)
    client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT)
    client.post(f"/api/v1/bookings/{kode}/payments", json=LUNAS)

    tiga_jam_sebelum = datetime.combine(tanggal, time(16), tzinfo=ZONA_WAKTU)
    monkeypatch.setattr(waktu, "sekarang", lambda: tiga_jam_sebelum)
    data = client.post(f"/api/v1/bookings/{kode}/cancel", json={}).json()
    assert data["status"] == "dibatalkan"
    # sudah bayar 200rb, deposit 100rb hangus, pelunasan 100rb kembali
    assert data["payments"][-1]["nominal"] == 100_000

def test_booking_kedaluwarsa_melepas_slot(db, login, customer, customer_lain, venue_court):
    venue, court = venue_court
    client = login(customer.email)
    tanggal = tanggal_depan(SENIN)
    kode = _pesan(client, court, tanggal)
    db.execute(
        update(Booking)
        .where(Booking.kode == kode)
        .values(batas_bayar=waktu.sekarang() - timedelta(minutes=1))
    )
    db.commit()

    slot = client.get(
        f"/api/v1/venues/{venue.slug}/availability", params={"tanggal": tanggal.isoformat()}
    ).json()["courts"][0]["slots"]
    assert {s["jam"]: s["status"] for s in slot}[19] == "tersedia"
    detail = client.get(f"/api/v1/bookings/{kode}").json()
    assert detail["status"] == "kedaluwarsa"
    assert client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT).status_code == 400
    _pesan(login(customer_lain.email), court, tanggal)

def test_tandai_selesai_setelah_jam_main(login, customer, manager, venue_court, monkeypatch):
    _, court = venue_court
    tanggal = tanggal_depan(SENIN)
    client = login(customer.email)
    kode = _pesan(client, court, tanggal)
    client.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT)
    pengelola = login(manager.email)
    assert pengelola.post(f"/api/v1/manager/bookings/{kode}/complete").status_code == 400

    saat_main = datetime.combine(tanggal, time(19, 30), tzinfo=ZONA_WAKTU)
    monkeypatch.setattr(waktu, "sekarang", lambda: saat_main)
    # Jam main sudah lewat tapi belum lunas -> harus ditolak (400)
    res_sebelum_lunas = pengelola.post(f"/api/v1/manager/bookings/{kode}/complete")
    assert res_sebelum_lunas.status_code == 400
    assert "belum lunas" in res_sebelum_lunas.json()["detail"].lower()

    # Manager mencatat pelunasan langsung di venue
    res_bayar = pengelola.post(
        f"/api/v1/manager/bookings/{kode}/payments",
        json={"jenis": "pelunasan", "metode": "qris"},
    )
    assert res_bayar.status_code == 200
    assert res_bayar.json()["sisa_tagihan"] == 0

    # Setelah lunas, booking baru dapat ditandai selesai
    res = pengelola.post(f"/api/v1/manager/bookings/{kode}/complete")
    assert res.json()["status"] == "selesai"
    assert client.get(f"/api/v1/bookings/{kode}").json()["bisa_dibatalkan"] is False

def test_status_slot_di_kalender_ketersediaan(db, login, anon, customer, customer_lain, venue_court):
    venue, court = venue_court
    tanggal = tanggal_depan(SENIN)
    saya = login(customer.email)
    _pesan(saya, court, tanggal, 10, 1)
    kode_lain = _pesan(login(customer_lain.email), court, tanggal, 12, 1)
    login(customer_lain.email).post(f"/api/v1/bookings/{kode_lain}/payments", json=DEPOSIT)
    _pesan(login(customer_lain.email), court, tanggal, 14, 1)
    db.add(CourtClosure(court_id=court.id, tanggal=tanggal, jam_mulai=20, jam_selesai=22, alasan="Servis"))
    db.commit()

    params = {"tanggal": tanggal.isoformat()}
    url = f"/api/v1/venues/{venue.slug}/availability"
    status = {s["jam"]: s["status"] for s in saya.get(url, params=params).json()["courts"][0]["slots"]}
    assert status[10] == "milik_saya"
    assert status[12] == "dipesan"
    assert status[14] == "menunggu"
    assert status[20] == status[21] == "ditutup"
    assert status[8] == "tersedia"
    # tamu tidak melihat "milik_saya"
    tamu = {s["jam"]: s["status"] for s in anon.get(url, params=params).json()["courts"][0]["slots"]}
    assert tamu[10] == "menunggu"

    kalender = anon.get(
        f"/api/v1/venues/{venue.slug}/calendar", params={"mulai": tanggal.isoformat(), "hari": 1}
    ).json()[0]
    assert kalender["total_slot"] == 14
    assert kalender["slot_tersedia"] == 14 - 3 - 2

def test_jam_lewat_hari_ini_tidak_tersedia(anon, venue_court, monkeypatch):
    venue, _ = venue_court
    hari_ini = waktu.hari_ini()
    jam_13 = datetime.combine(hari_ini, time(13, 5), tzinfo=ZONA_WAKTU)
    monkeypatch.setattr(waktu, "sekarang", lambda: jam_13)
    slots = anon.get(
        f"/api/v1/venues/{venue.slug}/availability", params={"tanggal": hari_ini.isoformat()}
    ).json()["courts"][0]["slots"]
    status = {s["jam"]: s["status"] for s in slots}
    assert status[13] == "lewat"
    assert status[14] == "tersedia"
