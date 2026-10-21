from datetime import timedelta

from app import waktu
from tests.conftest import booking_json, tanggal_depan

SENIN = 0
DEPOSIT = {"jenis": "deposit", "metode": "qris"}
COURT_BARU = {
    "nama": "Padel 1",
    "olahraga": "padel",
    "permukaan": "Turf + dinding kaca",
    "is_indoor": True,
    "kapasitas": 4,
    "tarif_weekday": 300_000,
    "tarif_weekend": 400_000,
}

def _jadwal(buka=8, tutup=22, tutup_hari=()):
    return [
        {"hari": h, "jam_buka": buka, "jam_tutup": tutup, "is_tutup": h in tutup_hari}
        for h in range(7)
    ]

def test_tambah_venue_dengan_jadwal_default(login, manager):
    client = login(manager.email)
    res = client.post(
        "/api/v1/manager/venues",
        json={
            "nama": "Arena Padel Baru",
            "kota": "Bandung",
            "alamat": "Jl. Contoh No. 2",
            "fasilitas": ["Parkir", "Kafe, minuman"],
            "mode_konfirmasi": "manual",
            "persen_deposit": 30,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["slug"] == "arena-padel-baru"
    assert len(data["jadwal"]) == 7
    assert data["fasilitas"] == ["Parkir", "Kafe minuman"]
    assert client.get("/api/v1/venues/arena-padel-baru").status_code == 200

def test_persen_deposit_divalidasi(login, manager, venue_court):
    venue, _ = venue_court
    client = login(manager.email)
    res = client.patch(f"/api/v1/manager/venues/{venue.id}", json={"persen_deposit": 5})
    assert res.status_code == 422
    res = client.patch(f"/api/v1/manager/venues/{venue.id}", json={"persen_deposit": 30})
    assert res.json()["persen_deposit"] == 30

def test_crud_court_dan_tarif(login, manager, venue_court):
    venue, _ = venue_court
    client = login(manager.email)
    res = client.post(f"/api/v1/manager/venues/{venue.id}/courts", json=COURT_BARU)
    assert res.status_code == 201
    court_id = res.json()["id"]

    dobel = client.post(f"/api/v1/manager/venues/{venue.id}/courts", json=COURT_BARU)
    assert dobel.status_code == 409
    tarif_aneh = client.post(
        f"/api/v1/manager/venues/{venue.id}/courts", json={**COURT_BARU, "nama": "X", "tarif_weekday": 0}
    )
    assert tarif_aneh.status_code == 422

    res = client.patch(f"/api/v1/manager/courts/{court_id}", json={"tarif_weekend": 450_000})
    assert res.json()["tarif_weekend"] == 450_000
    assert client.delete(f"/api/v1/manager/courts/{court_id}").status_code == 204
    assert len(client.get(f"/api/v1/manager/venues/{venue.id}/courts").json()) == 1

def test_court_dengan_riwayat_tidak_bisa_dihapus(login, manager, customer, venue_court):
    _, court = venue_court
    login(customer.email).post("/api/v1/bookings", json=booking_json(court, tanggal_depan(SENIN)))
    client = login(manager.email)
    assert client.delete(f"/api/v1/manager/courts/{court.id}").status_code == 409
    res = client.patch(f"/api/v1/manager/courts/{court.id}", json={"is_active": False})
    assert res.json()["is_active"] is False

def test_ubah_jam_operasional(login, manager, customer, venue_court):
    venue, court = venue_court
    client = login(manager.email)
    url = f"/api/v1/manager/venues/{venue.id}/schedule"
    assert client.put(url, json=_jadwal(buka=22, tutup=8)).status_code == 422
    assert client.put(url, json=_jadwal()[:6]).status_code == 422

    login(customer.email).post("/api/v1/bookings", json=booking_json(court, tanggal_depan(SENIN), 20))
    # booking jam 20 di hari Senin akan berada di luar jam baru
    assert client.put(url, json=_jadwal(tutup=20)).status_code == 409
    assert client.put(url, json=_jadwal(tutup_hari=(SENIN,))).status_code == 409

    res = client.put(url, json=_jadwal(buka=6, tutup=23, tutup_hari=(SENIN + 2,)))
    assert res.status_code == 200
    assert res.json()[2]["is_tutup"] is True
    assert res.json()[0]["jam_buka"] == 6

def test_penutupan_bentrok_dengan_booking_ditolak(login, manager, customer, venue_court):
    venue, court = venue_court
    tanggal = tanggal_depan(SENIN)
    login(customer.email).post("/api/v1/bookings", json=booking_json(court, tanggal, 19))
    client = login(manager.email)
    url = f"/api/v1/manager/venues/{venue.id}/closures"
    dasar = {"court_id": court.id, "tanggal": tanggal.isoformat(), "alasan": "Ganti lampu"}
    assert client.post(url, json=dasar).status_code == 409
    assert client.post(url, json={**dasar, "jam_mulai": 18, "jam_selesai": 20}).status_code == 409
    assert client.post(url, json={**dasar, "jam_mulai": 8}).status_code == 422
    res = client.post(url, json={**dasar, "jam_mulai": 8, "jam_selesai": 12})
    assert res.status_code == 201
    assert len(client.get(url).json()) == 1

def test_dashboard_menghitung_okupansi(login, manager, customer, venue_court):
    venue, court = venue_court
    tanggal = tanggal_depan(SENIN)
    pelanggan = login(customer.email)
    kode = pelanggan.post(
        "/api/v1/bookings", json=booking_json(court, tanggal, 19, 2)
    ).json()["kode"]
    pelanggan.post(f"/api/v1/bookings/{kode}/payments", json=DEPOSIT)
    # booking yang belum dibayar tidak dihitung terisi
    pelanggan.post("/api/v1/bookings", json=booking_json(court, tanggal, 10, 1))

    res = login(manager.email).get(
        f"/api/v1/manager/venues/{venue.id}/dashboard",
        params={"dari": waktu.hari_ini().isoformat(), "sampai": tanggal.isoformat()},
    )
    assert res.status_code == 200
    data = res.json()
    hari = {h["tanggal"]: h for h in data["harian"]}[tanggal.isoformat()]
    assert (hari["jam_terisi"], hari["jam_tersedia"]) == (2, 14)
    assert hari["okupansi_persen"] == 14.3
    assert data["ringkasan"]["pendapatan"] == 100_000
    assert data["ringkasan"]["booking_terkonfirmasi"] == 1
    assert data["per_court"][0]["jam_terisi"] == 2
    assert {j["jam"]: j["jumlah"] for j in data["jam_sibuk"]}[19] == 1

def test_agenda_harian(login, manager, customer, venue_court):
    venue, court = venue_court
    tanggal = tanggal_depan(SENIN)
    login(customer.email).post("/api/v1/bookings", json=booking_json(court, tanggal, 19, 2))
    res = login(manager.email).get(
        f"/api/v1/manager/venues/{venue.id}/agenda", params={"tanggal": tanggal.isoformat()}
    )
    item = res.json()["courts"][0]["items"][0]
    assert (item["jam_mulai"], item["jam_selesai"], item["nama_customer"]) == (19, 21, "Customer")

def test_daftar_booking_masuk_berhalaman(login, manager, customer, venue_court):
    _, court = venue_court
    client = login(customer.email)
    tanggal = tanggal_depan(SENIN)
    for jam in (9, 11, 13):
        client.post("/api/v1/bookings", json=booking_json(court, tanggal, jam))
    pengelola = login(manager.email)
    res = pengelola.get("/api/v1/manager/bookings", params={"per_page": 2, "page": 2}).json()
    assert res["total"] == 3
    assert len(res["items"]) == 1
    assert res["items"][0]["customer"]["email"] == customer.email
    cari = pengelola.get("/api/v1/manager/bookings", params={"q": "customer"}).json()
    assert cari["total"] == 3
    besok = waktu.hari_ini() + timedelta(days=1)
    kosong = pengelola.get("/api/v1/manager/bookings", params={"tanggal": besok.isoformat()})
    assert kosong.json()["total"] == (3 if besok == tanggal else 0)
