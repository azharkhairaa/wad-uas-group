# Lapangin

Aplikasi web booking lapang olahraga untuk Group Project mata kuliah Web Application Development,
topik **3.2 Sports Venue Booking**. Customer bisa melihat slot kosong per jam di setiap lapang lalu
booking dengan deposit. Venue manager mengelola lapang, tarif, jam buka dan booking yang masuk.

Cabang olahraga yang didukung ada tujuh, yaitu lapang tennis, lapang padel, lapang futsal, golf
driving, lapang badminton, lapang voli dan lapang basket.

| Lapisan | Teknologi |
|---|---|
| Frontend | Vue 3 (Composition API), Vite, Pinia, Vue Router |
| Backend | FastAPI, Pydantic, PyJWT, bcrypt, slowapi |
| Database | PostgreSQL, SQLAlchemy 2.x, Alembic |
| Pengujian | pytest (60 test), ruff |

## Tampilan

Palet warna yang dipakai adalah `#004e89` (navy), `#1a659e` (biru), `#ff6b35` (oranye), `#f7c59f`
(peach) dan `#efefd0` (krem). Tema bawaan terang. Tema gelap bisa dipilih lewat tombol di header dan
pilihannya diingat browser. Ikon olahraga dan ikon menu memakai SVG buatan sendiri di
`frontend/src/components/AppIcon.js`, tanpa emoji. Warna grafik dashboard sudah dicek aman untuk
pembaca buta warna (biru untuk hari yang sudah lewat, oranye untuk hari mendatang).

## Fitur sesuai ketentuan soal

| Ketentuan | Implementasi |
|---|---|
| Daftar venue dan lapang dengan tarif per jam, beda weekday dan weekend | Beranda dengan pencarian dan filter olahraga. Halaman venue menampilkan tabel tarif weekday (Senin–Jumat) dan weekend (Sabtu–Minggu) |
| Kalender ketersediaan slot per lapang per hari | Strip kalender 14 hari berisi jumlah slot kosong per tanggal, lalu grid slot per jam untuk setiap lapang |
| Booking slot dengan validasi bentrok | Dicek dua lapis, di aplikasi (pesan jelas, HTTP 409) dan di database lewat indeks unik parsial |
| Konfirmasi booking otomatis setelah DP atau lewat persetujuan manager | Setiap venue memilih mode `otomatis` atau `manual`. Manager juga bisa menyetujui booking yang dibayar di lokasi |
| Riwayat booking customer | Halaman Booking saya dengan filter status, detail, hitung mundur batas bayar, simulasi bayar DP atau lunas dan pembatalan |
| Dashboard manager | CRUD lapang dan tarif, jam buka mingguan, penutupan sementara, booking masuk (setujui, tolak, selesai, batalkan), agenda harian dan grafik okupansi |

Hal yang sengaja tidak dibuat karena di luar lingkup soal adalah payment gateway sungguhan,
notifikasi WhatsApp atau SMS, sistem multi-kota, membership, review lapang dan harga dinamis.
Pembayaran di aplikasi ini hanya simulasi.

## Materi kuliah yang diterapkan

| Pertemuan | Diterapkan di |
|---|---|
| 3–4 Safe rendering, fetch async, empat keadaan request | Tidak ada `v-html` di seluruh frontend. `api/client.js` selalu cek `response.ok`. `useRequest.js` dan `RequestState.vue` menangani loading, error, kosong dan berhasil |
| 5 Vue dashboard | Komponen, props, computed dan watch di semua halaman |
| 6 FastAPI | Path dan query parameter, validasi Pydantic (422), `HTTPException` 404, CORS |
| 7 Kontrak REST API | Metadata OpenAPI, tag, `summary` dan `description` di setiap endpoint, skema request dan response dipisah (`UserOut` tanpa password), Enum, nested model, rate limit slowapi |
| 9 PostgreSQL, SQLAlchemy, Alembic | Model gaya `Mapped`, migrasi `0001`, transaksi commit/rollback, eager loading `selectinload` untuk mencegah N+1, query lewat ORM tanpa SQL mentah dari input |
| 10 JWT dan OWASP | bcrypt dengan `HASH_DUMMY`, JWT wajib `exp` dan `sub`, cookie httpOnly + SameSite + CSRF double submit, Bearer untuk Swagger, BOLA dijawab 404, RBAC customer dan manager, `SECRET_KEY` gagal cepat kalau kurang dari 32 karakter |

CI/CD GitHub Actions dan deployment (Docker) menyusul setelah materinya dibahas di sesi berikutnya.

## Menjalankan di komputer sendiri

Prasyarat: PostgreSQL 14 ke atas, Python 3.12, Node.js 22.

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # isi DATABASE_URL dan SECRET_KEY
createdb lapangin
alembic upgrade head
python -m app.seed            # data contoh, menghapus data lama
uvicorn app.main:app --reload --port 8000
```

Dokumentasi API interaktif ada di <http://localhost:8000/docs>. Untuk mencoba endpoint yang butuh
login di Swagger, tekan **Authorize** lalu isi email di kolom username.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Buka <http://localhost:5173>. Request ke `/api` diteruskan Vite ke port 8000, jadi cookie sesi tetap
satu origin.

### Akun demo

Semua akun memakai password `Lapangin2026`. Di halaman login ada tombol untuk mengisi akun demo.

| Peran | Email | Venue |
|---|---|---|
| Customer | `budi@example.com` | punya riwayat booking dari selesai sampai menunggu persetujuan |
| Venue manager | `manager.dago@lapangin.id` | Dago Sport Hub (otomatis, DP 50%), Setiabudi Padel & Tennis (manual, DP 50%) |
| Venue manager | `manager.arcamanik@lapangin.id` | Arcamanik Golf Range (otomatis, bayar penuh, tutup Senin), GOR Antapani (manual, DP 30%) |

Customer lain untuk mencoba bentrok jadwal: `sinta@example.com`, `raka@example.com` dan
seterusnya (lihat `backend/app/seed.py`).

## Aturan booking

- Slot per jam, satu booking 1 sampai 4 jam berurutan di satu lapang, paling jauh 30 hari ke depan.
- Setelah booking dibuat, slot ditahan sesuai batas bayar venue (bawaan 30 menit). Kalau DP tidak
  dibayar, booking menjadi kedaluwarsa dan slot dilepas.
- Satu customer maksimal punya 3 booking yang belum dibayar, supaya slot tidak ditimbun.
- Harga dibekukan saat booking dibuat. Perubahan tarif tidak mengubah tagihan lama.
- Batal paling lambat 24 jam sebelum main, uang kembali penuh. Kurang dari itu, DP hangus.
  Booking yang ditolak atau dibatalkan manager selalu dikembalikan penuh.

## Keputusan desain yang penting

**Anti-bentrok dua lapis.** Setiap jam yang dipesan disimpan sebagai baris `booking_slots`. Lapis
pertama mengecek slot di aplikasi supaya pesan error jelas. Lapis kedua adalah indeks unik parsial
`uq_booking_slots_aktif (court_id, tanggal, jam) WHERE aktif` di PostgreSQL. Dua request yang datang
bersamaan tetap hanya satu yang berhasil. Test `test_dua_request_bersamaan_hanya_satu_yang_menang`
membuktikannya dengan dua thread.

**Pembatalan tidak menghapus data.** Booking yang batal, ditolak atau kedaluwarsa cukup menandai
slotnya `aktif = false`. Slot langsung bebas lagi tetapi riwayat booking dan pembayaran tetap utuh.

**Kedaluwarsa tanpa scheduler.** Booking yang lewat batas bayar dilepas setiap kali jadwal dibaca atau
booking dibuat. Tidak perlu cron atau worker tambahan.

**Kunci baris saat membayar.** Bayar, batal, setujui dan tolak memakai `SELECT ... FOR UPDATE`
supaya dua klik bersamaan tidak memproses pembayaran dua kali.

## Pengujian

```bash
cd backend
createdb lapangin_test        # sekali saja
pytest -q                     # 60 test
ruff check .
```

Test memakai database `lapangin_test` (bisa diganti lewat `TEST_DATABASE_URL`). Cakupannya meliputi
register dan login, token palsu atau kedaluwarsa, CSRF, rate limit login, RBAC dan BOLA, tarif weekday
dan weekend, semua pola bentrok jadwal, race condition, alur pembayaran otomatis dan manual,
pembatalan dan refund, kedaluwarsa, penutupan lapang, perubahan jam buka dan hitungan okupansi
dashboard.

## Deploy gratis (Vercel + Neon)

Frontend dan API berjalan di satu project Vercel dengan dua service di domain yang sama, jadi cookie
sesi dan CSRF tetap satu origin. Service `web` menyajikan hasil build Vue, service `api` menjalankan
FastAPI sebagai Vercel Function untuk `/api`, `/docs` dan `/openapi.json`. Database memakai
PostgreSQL di Neon. Paket Hobby Vercel dan paket Free Neon tidak meminta kartu kredit.

| Berkas | Isi |
|---|---|
| `vercel.json` | Service `web` (folder `frontend/`, rute Vue diarahkan ke `index.html`) dan `api` (folder `backend/`, `app.main:app`) |
| `.github/workflows/ci.yml` | ruff, migrasi dari nol dan `alembic check`, pytest dengan PostgreSQL 16, build frontend, build image Docker, lalu migrasi ke Neon setelah push ke `main` |
| `Dockerfile` | Image produksi (build Vue + FastAPI) untuk menjalankan aplikasi di host lain yang mendukung container |

Langkah pertama kali:

1. **Neon.** Daftar di <https://neon.com> (bisa memakai akun GitHub) lalu buat project dengan region
   Singapura. Di menu **Connect**, matikan *Connection pooling* lalu salin connection string yang
   diawali `postgresql://`.
2. **Isi database** sekali dari komputer sendiri. Perintah ini membuat tabel lalu mengisi data contoh
   dan menghapus data lama di database Neon.

```bash
cd backend
read -rs NEON_URL             # tempel connection string Neon lalu Enter, tidak tampil di layar
DATABASE_URL="$NEON_URL" .venv/bin/alembic upgrade head
DATABASE_URL="$NEON_URL" .venv/bin/python -m app.seed
```

3. **Vercel.** Daftar di <https://vercel.com> dengan akun GitHub (paket Hobby), pilih
   **Add New > Project** lalu import repo ini. Vercel membaca `vercel.json` dan membangun kedua
   service. Isi Environment Variables berikut sebelum deploy.

| Variabel | Nilai |
|---|---|
| `DATABASE_URL` | connection string Neon |
| `SECRET_KEY` | hasil `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `COOKIE_SECURE` | `true` |
| `TOKEN_MENIT` | `120` |

4. Opsional, tambahkan secret repo `NEON_DATABASE_URL` (Settings > Secrets and variables > Actions)
   berisi connection string yang sama. Setelah itu setiap push ke `main` menjalankan migrasi ke Neon
   lewat GitHub Actions. Tanpa secret ini job migrasi dilewati.

Setiap push ke `main` menjalankan CI di GitHub Actions dan Vercel men-deploy commit tersebut.

Catatan paket gratis:

- Function Python di Vercel butuh beberapa detik saat pertama dipanggil setelah lama tidak dipakai.
- Compute Neon tidur setelah 5 menit tidak dipakai lalu bangun sendiri saat ada query.
- Rate limit login membaca IP asli dari header `x-real-ip` yang ditulis ulang Vercel.

## Struktur folder

```
uas-2/
├── vercel.json              # service web (Vue) dan api (FastAPI) di Vercel
├── Dockerfile               # image produksi (build Vue + FastAPI)
├── .github/workflows/ci.yml # CI lint, migrasi, test dan build
├── backend/
│   ├── app/
│   │   ├── main.py          # aplikasi FastAPI, CORS, header keamanan, build Vue di produksi
│   │   ├── config.py        # baca .env, SECRET_KEY wajib
│   │   ├── database.py      # engine dan session
│   │   ├── models.py        # tabel users, venues, courts, bookings, booking_slots, payments, dst.
│   │   ├── schemas.py       # skema request dan response
│   │   ├── security.py      # bcrypt dan JWT
│   │   ├── deps.py          # get_current_user, cek CSRF, RBAC
│   │   ├── limiter.py       # rate limit slowapi
│   │   ├── routers/         # auth, venues, bookings, manager
│   │   ├── services/        # harga, ketersediaan, booking, dashboard
│   │   └── seed.py          # data contoh
│   ├── alembic/versions/    # migrasi database
│   └── tests/               # pytest
└── frontend/
    └── src/
        ├── api/             # fetch + CSRF, daftar endpoint
        ├── stores/          # Pinia: auth, manager, toast
        ├── router/          # rute dan penjaga peran
        ├── composables/     # useRequest, useTheme
        ├── components/      # SlotGrid, DateStrip, grafik, modal
        └── views/           # halaman publik, customer, manager
```
