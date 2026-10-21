"""isi database dengan data contoh: python -m app.seed

semua data lama dihapus dulu, jangan dijalankan di database produksi
"""

import random
from datetime import date, datetime, timedelta

from sqlalchemy import text

from app import waktu
from app.database import SessionLocal
from app.models import (
    Booking,
    BookingSlot,
    Court,
    CourtClosure,
    JenisPembayaran,
    MetodePembayaran,
    ModeKonfirmasi,
    Olahraga,
    Payment,
    Role,
    StatusBooking,
    User,
    Venue,
    VenueSchedule,
)
from app.security import hash_password
from app.services.booking import buat_kode_booking, buat_kode_referensi
from app.services.harga import hitung_deposit, tarif_per_jam

PASSWORD_DEMO = "Lapangin2026"
S = StatusBooking
OL = Olahraga

MANAGER = [
    ("Pengelola Dago Sport Hub", "manager.dago@lapangin.id", "081200000001"),
    ("Pengelola Arcamanik", "manager.arcamanik@lapangin.id", "081200000002"),
]
CUSTOMER = [
    ("Budi Santoso", "budi@example.com", "081311110001"),
    ("Sinta Maharani", "sinta@example.com", "081311110002"),
    ("Raka Pratama", "raka@example.com", "081311110003"),
    ("Intan Permata", "intan@example.com", "081311110004"),
    ("Fajar Nugraha", "fajar@example.com", "081311110005"),
    ("Nadia Putri", "nadia@example.com", "081311110006"),
    ("Yoga Saputra", "yoga@example.com", "081311110007"),
    ("Dewi Anggraini", "dewi@example.com", "081311110008"),
]

# (nama, olahraga, permukaan, indoor, kapasitas, weekday, weekend)
VENUE = [
    {
        "manager": 0,
        "nama": "Dago Sport Hub",
        "slug": "dago-sport-hub",
        "kota": "Bandung",
        "alamat": "Jl. Ir. H. Juanda No. 210, Dago, Bandung",
        "deskripsi": "Gedung olahraga indoor di kawasan Dago. Lapang futsal, badminton, "
        "basket dan voli dalam satu atap, cocok untuk main rutin bareng kantor atau komunitas.",
        "telepon": "0222500210",
        "fasilitas": "Parkir luas, Musala, Kantin, Ruang ganti, Shower, Tribun penonton",
        "mode": ModeKonfirmasi.OTOMATIS,
        "deposit": 50,
        "jadwal": {h: (8, 23) if h < 5 else (7, 23) for h in range(7)},
        "courts": [
            ("Futsal A", OL.FUTSAL, "Vinyl interlock", True, 10, 180_000, 250_000),
            ("Futsal B", OL.FUTSAL, "Rumput sintetis", True, 10, 150_000, 220_000),
            ("Badminton 1", OL.BADMINTON, "Karpet standar BWF", True, 4, 60_000, 80_000),
            ("Badminton 2", OL.BADMINTON, "Karpet standar BWF", True, 4, 60_000, 80_000),
            ("Badminton 3", OL.BADMINTON, "Karpet vinyl", True, 4, 50_000, 70_000),
            ("Badminton 4", OL.BADMINTON, "Karpet vinyl", True, 4, 50_000, 70_000),
            ("Basket Full Court", OL.BASKET, "Lantai kayu maple", True, 10, 300_000, 400_000),
            ("Voli Indoor", OL.VOLI, "Karpet sintetis", True, 12, 200_000, 260_000),
        ],
    },
    {
        "manager": 0,
        "nama": "Setiabudi Padel & Tennis",
        "slug": "setiabudi-padel-tennis",
        "kota": "Bandung",
        "alamat": "Jl. Dr. Setiabudi No. 155, Bandung",
        "deskripsi": "Klub raket di Bandung utara dengan tiga lapang padel berdinding kaca dan "
        "dua lapang tennis. Booking dikonfirmasi manager setelah deposit masuk.",
        "telepon": "0222010155",
        "fasilitas": "Parkir, Kafe, Sewa raket, Ruang ganti, Shower",
        "mode": ModeKonfirmasi.MANUAL,
        "deposit": 50,
        "jadwal": dict.fromkeys(range(7), (6, 22)),
        "courts": [
            ("Padel 1 Panoramic", OL.PADEL, "Turf + dinding kaca", True, 4, 350_000, 450_000),
            ("Padel 2", OL.PADEL, "Turf + dinding kaca", False, 4, 300_000, 400_000),
            ("Padel 3", OL.PADEL, "Turf + dinding kaca", False, 4, 300_000, 400_000),
            ("Tennis Hard Court", OL.TENNIS, "Hard court akrilik", False, 4, 150_000, 200_000),
            ("Tennis Clay Court", OL.TENNIS, "Clay (tanah liat)", False, 4, 175_000, 225_000),
        ],
    },
    {
        "manager": 1,
        "nama": "Arcamanik Golf Range",
        "slug": "arcamanik-golf-range",
        "kota": "Bandung",
        "alamat": "Jl. Pacuan Kuda No. 40, Arcamanik, Bandung",
        "deskripsi": "Driving range beratap dengan bay bermatras rumput sintetis dan dua bay "
        "simulator. Sewa bay per jam sudah termasuk satu keranjang bola. Tutup setiap Senin.",
        "telepon": "0227200040",
        "fasilitas": "Parkir, Sewa stik, Pelatih, Kafe",
        "mode": ModeKonfirmasi.OTOMATIS,
        "deposit": 100,
        "jadwal": dict.fromkeys(range(7), (7, 22)),
        "tutup": [0],
        "courts": [
            ("Bay 1", OL.GOLF_DRIVING, "Matras rumput sintetis", False, 2, 120_000, 160_000),
            ("Bay 2", OL.GOLF_DRIVING, "Matras rumput sintetis", False, 2, 120_000, 160_000),
            ("Bay 3", OL.GOLF_DRIVING, "Matras rumput sintetis", False, 2, 120_000, 160_000),
            ("Bay 4", OL.GOLF_DRIVING, "Matras rumput sintetis", False, 2, 120_000, 160_000),
            ("Bay Simulator 5", OL.GOLF_DRIVING, "Simulator layar", True, 4, 200_000, 250_000),
            ("Bay Simulator 6", OL.GOLF_DRIVING, "Simulator layar", True, 4, 200_000, 250_000),
        ],
    },
    {
        "manager": 1,
        "nama": "GOR Antapani Sport Center",
        "slug": "gor-antapani-sport-center",
        "kota": "Bandung",
        "alamat": "Jl. Terusan Jakarta No. 88, Antapani, Bandung",
        "deskripsi": "GOR serbaguna dengan harga bersahabat untuk latihan klub dan sekolah. "
        "Booking dikonfirmasi manager, deposit cukup 30%.",
        "telepon": "0227270088",
        "fasilitas": "Parkir motor, Musala, Warung, Ruang ganti",
        "mode": ModeKonfirmasi.MANUAL,
        "deposit": 30,
        "jadwal": {h: (9, 22) if h < 5 else (8, 22) for h in range(7)},
        "courts": [
            ("Badminton A", OL.BADMINTON, "Karpet vinyl", True, 4, 45_000, 60_000),
            ("Badminton B", OL.BADMINTON, "Karpet vinyl", True, 4, 45_000, 60_000),
            ("Badminton C", OL.BADMINTON, "Lantai kayu", True, 4, 40_000, 55_000),
            ("Lapang Voli", OL.VOLI, "Lantai kayu", True, 12, 150_000, 200_000),
            ("Basket 3x3", OL.BASKET, "Lantai kayu", True, 6, 120_000, 160_000),
            ("Futsal Antapani", OL.FUTSAL, "Vinyl", True, 10, 130_000, 180_000),
        ],
    },
]

# peluang slot terisi per jam, sore-malam paling ramai
def peluang(jam: int, weekend: bool, olahraga: Olahraga) -> float:
    if 17 <= jam <= 21:
        dasar = 0.55
    elif jam >= 22 or jam < 9:
        dasar = 0.18
    else:
        dasar = 0.14
    if olahraga in (OL.PADEL, OL.GOLF_DRIVING, OL.TENNIS) and jam < 9:
        dasar += 0.2  # pemain raket dan golf suka pagi
    if weekend:
        dasar = min(0.85, dasar * 1.4 + 0.1)
    return dasar

def reset(db) -> None:
    db.execute(
        text(
            "TRUNCATE payments, booking_slots, bookings, court_closures, courts, "
            "venue_schedules, venues, users RESTART IDENTITY CASCADE"
        )
    )
    db.commit()

def tambah_booking(
    db,
    rng: random.Random,
    *,
    court: Court,
    venue: Venue,
    customer: User,
    tanggal: date,
    jam_mulai: int,
    durasi: int,
    status: StatusBooking,
    now: datetime,
) -> Booking:
    tarif = tarif_per_jam(court, tanggal)
    total = tarif * durasi
    deposit = hitung_deposit(total, venue.persen_deposit)
    mulai = waktu.mulai_slot(tanggal, jam_mulai)
    dibuat = min(now - timedelta(minutes=5), mulai - timedelta(hours=rng.randint(3, 120)))
    metode = rng.choice(list(MetodePembayaran))
    aktif = status not in (S.DIBATALKAN, S.KEDALUWARSA, S.DITOLAK)

    booking = Booking(
        kode=buat_kode_booking(tanggal),
        customer_id=customer.id,
        court_id=court.id,
        tanggal=tanggal,
        jam_mulai=jam_mulai,
        jam_selesai=jam_mulai + durasi,
        total_harga=total,
        nominal_deposit=deposit,
        jumlah_dibayar=0,
        status=status,
        created_at=dibuat,
    )
    booking.slots = [
        BookingSlot(court_id=court.id, tanggal=tanggal, jam=j, harga=tarif, aktif=aktif)
        for j in range(jam_mulai, jam_mulai + durasi)
    ]

    def bayar(jenis: JenisPembayaran, nominal: int, pada: datetime) -> None:
        booking.payments.append(
            Payment(
                jenis=jenis,
                metode=metode,
                nominal=nominal,
                kode_referensi=buat_kode_referensi(
                    "RFD" if jenis == JenisPembayaran.REFUND else "PAY"
                ),
                created_at=pada,
            )
        )
        if jenis != JenisPembayaran.REFUND:
            booking.jumlah_dibayar += nominal

    dp_pada = min(now, dibuat + timedelta(minutes=rng.randint(2, 25)))
    if status == S.MENUNGGU_PEMBAYARAN:
        booking.batas_bayar = now + timedelta(minutes=venue.batas_bayar_menit - 5)
        booking.created_at = now - timedelta(minutes=5)
    elif status == S.KEDALUWARSA:
        booking.alasan_batal = "Batas waktu pembayaran terlewati"
        booking.dibatalkan_pada = dibuat + timedelta(minutes=venue.batas_bayar_menit)
    else:
        bayar(JenisPembayaran.DEPOSIT, deposit, dp_pada)
        if status == S.MENUNGGU_PERSETUJUAN:
            pass
        elif status == S.DIBATALKAN:
            booking.alasan_batal = rng.choice(
                ["Ada acara mendadak", "Tim kurang orang", "Hujan, pindah jadwal"]
            )
            batal_pada = min(now, dp_pada + timedelta(hours=rng.randint(1, 30)))
            booking.dibatalkan_pada = batal_pada
            if (mulai - batal_pada).total_seconds() >= 24 * 3600:
                bayar(JenisPembayaran.REFUND, deposit, batal_pada)
        else:
            jeda = 0 if venue.mode_konfirmasi == ModeKonfirmasi.OTOMATIS else rng.randint(10, 180)
            booking.dikonfirmasi_pada = min(now, dp_pada + timedelta(minutes=jeda))
            sisa = total - deposit
            lunas = status == S.SELESAI or rng.random() < 0.35
            if lunas and sisa > 0:
                bayar(JenisPembayaran.PELUNASAN, sisa, min(now, max(dp_pada, mulai)))
    db.add(booking)
    return booking

def jalankan() -> None:
    rng = random.Random(2026)
    now = waktu.sekarang()
    hari_ini = now.date()
    db = SessionLocal()
    reset(db)

    hash_demo = hash_password(PASSWORD_DEMO)
    managers = [
        User(nama=n, email=e, no_hp=hp, role=Role.MANAGER, password_hash=hash_demo)
        for n, e, hp in MANAGER
    ]
    customers = [
        User(nama=n, email=e, no_hp=hp, role=Role.CUSTOMER, password_hash=hash_demo)
        for n, e, hp in CUSTOMER
    ]
    db.add_all(managers + customers)
    db.flush()

    venues: dict[str, Venue] = {}
    courts: dict[str, Court] = {}
    for data in VENUE:
        venue = Venue(
            manager_id=managers[data["manager"]].id,
            nama=data["nama"],
            slug=data["slug"],
            kota=data["kota"],
            alamat=data["alamat"],
            deskripsi=data["deskripsi"],
            telepon=data["telepon"],
            fasilitas=data["fasilitas"],
            mode_konfirmasi=data["mode"],
            persen_deposit=data["deposit"],
            batas_bayar_menit=30,
        )
        venue.jadwal = [
            VenueSchedule(
                hari=h, jam_buka=buka, jam_tutup=tutup, is_tutup=h in data.get("tutup", [])
            )
            for h, (buka, tutup) in data["jadwal"].items()
        ]
        venue.courts = [
            Court(
                nama=nama,
                olahraga=olahraga,
                permukaan=permukaan,
                is_indoor=indoor,
                kapasitas=kapasitas,
                tarif_weekday=weekday,
                tarif_weekend=weekend,
            )
            for nama, olahraga, permukaan, indoor, kapasitas, weekday, weekend in data["courts"]
        ]
        db.add(venue)
        venues[data["slug"]] = venue
        for court in venue.courts:
            courts[court.nama] = court
    db.flush()

    terpakai: set[tuple[int, date, int]] = set()

    def bisa(court: Court, tanggal: date, jam_mulai: int, durasi: int) -> bool:
        jadwal = next(j for j in court.venue.jadwal if j.hari == tanggal.weekday())
        if jadwal.is_tutup or jam_mulai < jadwal.jam_buka or jam_mulai + durasi > jadwal.jam_tutup:
            return False
        rentang = range(jam_mulai, jam_mulai + durasi)
        return all((court.id, tanggal, j) not in terpakai for j in rentang)

    def pesan(court, customer, tanggal, jam_mulai, durasi, status):
        if status not in (S.DIBATALKAN, S.KEDALUWARSA, S.DITOLAK):
            for j in range(jam_mulai, jam_mulai + durasi):
                terpakai.add((court.id, tanggal, j))
        return tambah_booking(
            db,
            rng,
            court=court,
            venue=court.venue,
            customer=customer,
            tanggal=tanggal,
            jam_mulai=jam_mulai,
            durasi=durasi,
            status=status,
            now=now,
        )

    # penutupan: ganti karpet sehari penuh dan turnamen setengah hari
    db.add_all(
        [
            CourtClosure(
                court_id=courts["Badminton 4"].id,
                tanggal=hari_ini + timedelta(days=3),
                alasan="Penggantian karpet lapang",
            ),
            CourtClosure(
                court_id=courts["Padel 3"].id,
                tanggal=hari_ini + timedelta(days=5),
                jam_mulai=8,
                jam_selesai=12,
                alasan="Turnamen internal klub",
            ),
        ]
    )
    for j in range(24):
        terpakai.add((courts["Badminton 4"].id, hari_ini + timedelta(days=3), j))
    for j in range(8, 12):
        terpakai.add((courts["Padel 3"].id, hari_ini + timedelta(days=5), j))

    # riwayat Budi untuk demo: lengkap dari selesai sampai menunggu persetujuan
    budi = customers[0]
    contoh = [
        ("Futsal A", -5, 19, 2, S.SELESAI),
        ("Badminton A", -2, 19, 1, S.DIBATALKAN),
        ("Bay 2", -1, 16, 1, S.KEDALUWARSA),
        ("Padel 1 Panoramic", 2, 19, 1, S.TERKONFIRMASI),
        ("Tennis Hard Court", 4, 7, 2, S.MENUNGGU_PERSETUJUAN),
    ]
    for nama_court, selisih, jam, durasi, status in contoh:
        tanggal = hari_ini + timedelta(days=selisih)
        court = courts[nama_court]
        while not bisa(court, tanggal, jam, durasi):
            tanggal += timedelta(days=1)
        pesan(court, budi, tanggal, jam, durasi, status)

    # booking acak 21 hari ke belakang sampai 10 hari ke depan
    lainnya = customers[1:]
    menunggu_bayar = 0
    for selisih in range(-21, 11):
        tanggal = hari_ini + timedelta(days=selisih)
        weekend = waktu.is_weekend(tanggal)
        for court in courts.values():
            jadwal = next(j for j in court.venue.jadwal if j.hari == tanggal.weekday())
            if jadwal.is_tutup:
                continue
            jam = jadwal.jam_buka
            while jam < jadwal.jam_tutup:
                p = peluang(jam, weekend, court.olahraga)
                if selisih > 0:
                    p *= max(0.15, 1 - selisih / 12)  # makin jauh makin sepi
                durasi = rng.choice([1, 1, 2] if court.olahraga != OL.GOLF_DRIVING else [1])
                if rng.random() >= p or not bisa(court, tanggal, jam, durasi):
                    jam += 1
                    continue
                lewat = waktu.mulai_slot(tanggal, jam) <= now
                manual = court.venue.mode_konfirmasi == ModeKonfirmasi.MANUAL
                r = rng.random()
                if lewat:
                    status = S.SELESAI if r < 0.88 else S.DIBATALKAN if r < 0.95 else S.KEDALUWARSA
                elif selisih >= 1 and r < 0.025 and menunggu_bayar < len(lainnya):
                    status = S.MENUNGGU_PEMBAYARAN
                    menunggu_bayar += 1
                elif manual and r < 0.3:
                    status = S.MENUNGGU_PERSETUJUAN
                elif r < 0.92:
                    status = S.TERKONFIRMASI
                else:
                    status = S.DIBATALKAN
                customer = (
                    lainnya[menunggu_bayar - 1]
                    if status == S.MENUNGGU_PEMBAYARAN
                    else rng.choice(lainnya)
                )
                pesan(court, customer, tanggal, jam, durasi, status)
                jam += durasi

    db.commit()
    jumlah = db.execute(
        text("SELECT status, count(*) FROM bookings GROUP BY status ORDER BY 2 DESC")
    ).all()
    print(f"{len(managers)} manager, {len(customers)} customer")
    print(f"{len(venues)} venue, {len(courts)} court")
    print("booking per status:", ", ".join(f"{s} {n}" for s, n in jumlah))
    print(f"password semua akun demo: {PASSWORD_DEMO}")
    db.close()

if __name__ == "__main__":
    jalankan()
