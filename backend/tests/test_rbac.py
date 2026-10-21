"""otorisasi: peran (RBAC) dan kepemilikan data (BOLA/IDOR)"""

from tests.conftest import booking_json, buat_venue, tanggal_depan

def test_customer_tidak_bisa_masuk_area_manager(login, customer):
    client = login(customer.email)
    assert client.get("/api/v1/manager/venues").status_code == 403
    assert client.get("/api/v1/manager/bookings").status_code == 403

def test_manager_tidak_bisa_booking(login, manager, venue_court):
    _, court = venue_court
    client = login(manager.email)
    res = client.post("/api/v1/bookings", json=booking_json(court, tanggal_depan(1)))
    assert res.status_code == 403

def test_tamu_harus_login_untuk_booking(anon, venue_court):
    _, court = venue_court
    res = anon.post("/api/v1/bookings", json=booking_json(court, tanggal_depan(1)))
    assert res.status_code == 401

def test_customer_tidak_bisa_menyentuh_booking_orang_lain(
    login, customer, customer_lain, venue_court
):
    _, court = venue_court
    pemilik = login(customer.email)
    kode = pemilik.post("/api/v1/bookings", json=booking_json(court, tanggal_depan(1))).json()[
        "kode"
    ]
    penyusup = login(customer_lain.email)
    assert penyusup.get(f"/api/v1/bookings/{kode}").status_code == 404
    bayar = {"jenis": "deposit", "metode": "qris"}
    assert penyusup.post(f"/api/v1/bookings/{kode}/payments", json=bayar).status_code == 404
    assert penyusup.post(f"/api/v1/bookings/{kode}/cancel", json={}).status_code == 404
    assert penyusup.get("/api/v1/bookings").json() == []
    # booking pemilik tetap utuh
    assert pemilik.get(f"/api/v1/bookings/{kode}").json()["status"] == "menunggu_pembayaran"

def test_manager_hanya_mengelola_venue_miliknya(
    db, login, manager, manager_lain, customer, venue_court
):
    venue, court = venue_court
    kode = login(customer.email).post(
        "/api/v1/bookings", json=booking_json(court, tanggal_depan(1))
    ).json()["kode"]
    lain = login(manager_lain.email)

    assert lain.get(f"/api/v1/manager/venues/{venue.id}").status_code == 404
    assert lain.patch(f"/api/v1/manager/venues/{venue.id}", json={"nama": "Diambil"}).status_code == 404
    assert lain.patch(f"/api/v1/manager/courts/{court.id}", json={"tarif_weekday": 10_000}).status_code == 404
    assert lain.delete(f"/api/v1/manager/courts/{court.id}").status_code == 404
    assert lain.get(f"/api/v1/manager/venues/{venue.id}/dashboard").status_code == 404
    assert lain.post(f"/api/v1/manager/bookings/{kode}/approve").status_code == 404
    assert lain.get("/api/v1/manager/bookings").json()["total"] == 0

    # manager lain punya venue sendiri dan hanya melihat booking di sana
    buat_venue(db, manager_lain, nama="Venue Lain")
    assert len(lain.get("/api/v1/manager/venues").json()) == 1
    assert login(manager.email).get("/api/v1/manager/bookings").json()["total"] == 1

def test_penutupan_milik_manager_lain_tidak_bisa_dihapus(login, manager, manager_lain, venue_court):
    venue, court = venue_court
    pemilik = login(manager.email)
    res = pemilik.post(
        f"/api/v1/manager/venues/{venue.id}/closures",
        json={"court_id": court.id, "tanggal": tanggal_depan(2).isoformat(), "alasan": "Servis"},
    )
    assert res.status_code == 201
    lain = login(manager_lain.email)
    assert lain.delete(f"/api/v1/manager/closures/{res.json()['id']}").status_code == 404
