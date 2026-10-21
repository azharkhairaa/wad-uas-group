import os

# database uji terpisah, harus di-set sebelum app diimpor
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://localhost:5432/lapangin_test"
)
os.environ["SECRET_KEY"] = "kunci-uji-yang-panjang-dan-acak-0123456789abcdef"

from datetime import date, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import waktu  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.limiter import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Court,
    ModeKonfirmasi,
    Olahraga,
    Role,
    User,
    Venue,
    VenueSchedule,
)
from app.security import hash_password  # noqa: E402

PASSWORD = "Rahasia123"
HASH = hash_password(PASSWORD)

@pytest.fixture(scope="session", autouse=True)
def skema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(autouse=True)
def bersih(skema):
    # semua tabel dikosongkan supaya urutan test tidak berpengaruh
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE payments, booking_slots, bookings, court_closures, courts, "
                "venue_schedules, venues, users RESTART IDENTITY CASCADE"
            )
        )
    limiter.reset()
    yield

@pytest.fixture
def db():
    sesi = SessionLocal()
    yield sesi
    sesi.close()

def buat_user(db, email: str, role: Role = Role.CUSTOMER) -> User:
    user = User(nama=email.split("@")[0].title(), email=email, password_hash=HASH, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def customer(db):
    return buat_user(db, "customer@example.com")

@pytest.fixture
def customer_lain(db):
    return buat_user(db, "customer2@example.com")

@pytest.fixture
def manager(db):
    return buat_user(db, "manager@example.com", Role.MANAGER)

@pytest.fixture
def manager_lain(db):
    return buat_user(db, "manager2@example.com", Role.MANAGER)

def buat_venue(
    db,
    manager: User,
    *,
    nama: str = "Venue Uji",
    mode: ModeKonfirmasi = ModeKonfirmasi.OTOMATIS,
    persen_deposit: int = 50,
    jam: tuple[int, int] = (8, 22),
    hari_tutup: tuple[int, ...] = (),
    tarif: tuple[int, int] = (100_000, 150_000),
) -> tuple[Venue, Court]:
    venue = Venue(
        manager_id=manager.id,
        nama=nama,
        slug=nama.lower().replace(" ", "-"),
        kota="Bandung",
        alamat="Jl. Uji No. 1",
        mode_konfirmasi=mode,
        persen_deposit=persen_deposit,
    )
    venue.jadwal = [
        VenueSchedule(hari=h, jam_buka=jam[0], jam_tutup=jam[1], is_tutup=h in hari_tutup)
        for h in range(7)
    ]
    venue.courts = [
        Court(
            nama="Court 1",
            olahraga=Olahraga.BADMINTON,
            permukaan="Karpet",
            tarif_weekday=tarif[0],
            tarif_weekend=tarif[1],
        )
    ]
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue, venue.courts[0]

@pytest.fixture
def venue_court(db, manager):
    return buat_venue(db, manager)

@pytest.fixture
def login():
    """pabrik client yang sudah login lewat cookie + CSRF token, seperti frontend"""
    clients = []

    def _login(email: str, password: str = PASSWORD) -> TestClient:
        client = TestClient(app)
        res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200, res.text
        client.headers["X-CSRF-Token"] = res.json()["csrf_token"]
        clients.append(client)
        return client

    yield _login
    for client in clients:
        client.close()

@pytest.fixture
def anon():
    with TestClient(app) as client:
        yield client

def tanggal_depan(hari: int, minimal: int = 2) -> date:
    """tanggal terdekat (minimal N hari lagi) dengan hari tertentu, 0 = Senin"""
    tanggal = waktu.hari_ini() + timedelta(days=minimal)
    while tanggal.weekday() != hari:
        tanggal += timedelta(days=1)
    return tanggal

def booking_json(court: Court, tanggal: date, jam_mulai: int = 19, durasi: int = 1) -> dict:
    return {
        "court_id": court.id,
        "tanggal": tanggal.isoformat(),
        "jam_mulai": jam_mulai,
        "durasi": durasi,
    }
