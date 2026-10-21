from datetime import UTC, datetime, timedelta

import jwt

from app.config import ALGORITHM, SECRET_KEY
from tests.conftest import PASSWORD, booking_json, tanggal_depan

DAFTAR = {
    "nama": "Budi Santoso",
    "email": "Budi@Example.com",
    "no_hp": "081234567890",
    "password": "Rahasia123",
}

def test_register_selalu_jadi_customer(anon):
    res = anon.post("/api/v1/auth/register", json=DAFTAR)
    assert res.status_code == 201
    data = res.json()
    assert data["role"] == "customer"
    assert data["email"] == "budi@example.com"
    assert "password" not in data and "password_hash" not in data

def test_register_menolak_field_role(anon):
    # mass assignment: field di luar skema ditolak
    res = anon.post("/api/v1/auth/register", json={**DAFTAR, "role": "manager"})
    assert res.status_code == 422

def test_register_email_dobel_ditolak(anon):
    assert anon.post("/api/v1/auth/register", json=DAFTAR).status_code == 201
    res = anon.post("/api/v1/auth/register", json={**DAFTAR, "email": "BUDI@example.com"})
    assert res.status_code == 409

def test_register_password_lemah_ditolak(anon):
    res = anon.post("/api/v1/auth/register", json={**DAFTAR, "password": "hanyahuruf"})
    assert res.status_code == 422

def test_login_menyimpan_jwt_di_cookie_httponly(anon, customer):
    res = anon.post("/api/v1/auth/login", json={"email": customer.email, "password": PASSWORD})
    assert res.status_code == 200
    cookie = res.headers.get_list("set-cookie")
    akses = next(c for c in cookie if c.startswith("access_token="))
    assert "HttpOnly" in akses and "SameSite=lax" in akses
    assert res.json()["csrf_token"]
    assert anon.get("/api/v1/auth/me").json()["email"] == customer.email

def test_login_salah_pesannya_sama(anon, customer):
    salah_password = anon.post(
        "/api/v1/auth/login", json={"email": customer.email, "password": "Salah12345"}
    )
    tidak_terdaftar = anon.post(
        "/api/v1/auth/login", json={"email": "hantu@example.com", "password": "Salah12345"}
    )
    assert salah_password.status_code == tidak_terdaftar.status_code == 401
    # pesan identik supaya penyerang tidak bisa menebak email mana yang terdaftar
    assert salah_password.json() == tidak_terdaftar.json()

def test_me_tanpa_login_401(anon):
    assert anon.get("/api/v1/auth/me").status_code == 401

def test_token_palsu_dan_kedaluwarsa_ditolak(anon, customer):
    sekarang = datetime.now(UTC)
    palsu = jwt.encode(
        {"sub": str(customer.id), "exp": sekarang + timedelta(hours=1)},
        "kunci-penyerang-yang-berbeda-0123456789abcdef",
        algorithm=ALGORITHM,
    )
    basi = jwt.encode(
        {"sub": str(customer.id), "exp": sekarang - timedelta(minutes=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    for token in (palsu, basi, "bukan.jwt.sama-sekali"):
        res = anon.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401

def test_cookie_tanpa_csrf_token_ditolak(login, customer, venue_court):
    _, court = venue_court
    client = login(customer.email)
    data = booking_json(court, tanggal_depan(1))
    tanpa = client.post("/api/v1/bookings", json=data, headers={"X-CSRF-Token": ""})
    salah = client.post("/api/v1/bookings", json=data, headers={"X-CSRF-Token": "tebakan"})
    assert tanpa.status_code == 403
    assert salah.status_code == 403
    assert client.post("/api/v1/bookings", json=data).status_code == 201

def test_bearer_token_tidak_butuh_csrf(anon, customer, venue_court):
    _, court = venue_court
    res = anon.post(
        "/api/v1/auth/token", data={"username": customer.email, "password": PASSWORD}
    )
    assert res.status_code == 200
    header = {"Authorization": f"Bearer {res.json()['access_token']}"}
    anon.cookies.clear()
    res = anon.post("/api/v1/bookings", json=booking_json(court, tanggal_depan(1)), headers=header)
    assert res.status_code == 201

def test_login_dibatasi_10_per_menit(anon, customer):
    for _ in range(10):
        anon.post("/api/v1/auth/login", json={"email": customer.email, "password": "Salah12345"})
    res = anon.post("/api/v1/auth/login", json={"email": customer.email, "password": PASSWORD})
    assert res.status_code == 429
    assert res.headers["Retry-After"] == "60"

def test_logout_menghapus_sesi(login, customer):
    client = login(customer.email)
    assert client.get("/api/v1/auth/me").status_code == 200
    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401

def test_header_keamanan_terpasang(anon):
    res = anon.get("/api/v1/venues")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in res.headers["Content-Security-Policy"]
