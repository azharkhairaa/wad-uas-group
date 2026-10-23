<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { bookingApi, venueApi } from '@/api'
import AppIcon from '@/components/AppIcon'
import DateStrip from '@/components/DateStrip.vue'
import RequestState from '@/components/RequestState.vue'
import SlotGrid from '@/components/SlotGrid.vue'
import VenueGallery from '@/components/VenueGallery.vue'
import { useRequest } from '@/composables/useRequest'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { HARI_SENIN, hariIniIso, jam, rentangJam, rupiah, tanggalPanjang } from '@/utils/format'
import { infoOlahraga } from '@/utils/olahraga'
import { klikSlot } from '@/utils/slot'
import { MODE_KONFIRMASI, STATUS_SLOT } from '@/utils/status'

const MAKS_DURASI = 4
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const slug = computed(() => route.params.slug)
const tanggal = ref(route.query.tanggal || hariIniIso())
const olahraga = ref(route.query.olahraga || '')
const pilihan = ref(null)
const catatan = ref('')
const mengirim = ref(false)
const memuatJadwal = ref(false)

const venue = useRequest(venueApi.detail)
const kalender = useRequest(venueApi.kalender)
const slot = useRequest(venueApi.ketersediaan)

const olahragaVenue = computed(() => [...new Set((venue.data.value?.courts || []).map((c) => c.olahraga))])
const jadwalPerHari = computed(() => venue.data.value?.jadwal || [])
const courtsSlot = computed(() => slot.data.value?.courts || [])
const courtDipilih = computed(() => courtsSlot.value.find((c) => c.court.id === pilihan.value?.courtId))

const ringkasan = computed(() => {
  if (!pilihan.value || !courtDipilih.value || !venue.data.value) return null
  const tarif = courtDipilih.value.tarif_per_jam
  const total = tarif * pilihan.value.durasi
  const persen = venue.data.value.persen_deposit
  const deposit = Math.min(total, Math.ceil((total * persen) / 100 / 1000) * 1000)
  return { tarif, total, deposit, persen }
})

async function muatSlot(silent = false) {
  if (!silent) memuatJadwal.value = true
  const params = { tanggal: tanggal.value, olahraga: olahraga.value }
  try {
    const pRequest = slot.jalankan(slug.value, params)
    if (!silent && slot.data.value) {
      // beri jeda visual minimal ~180ms agar loader terlihat jelas bagi pengguna saat ganti tanggal
      const [hasil] = await Promise.all([
        pRequest,
        new Promise((resolve) => setTimeout(resolve, 180)),
      ])
      return hasil
    }
    return await pRequest
  } finally {
    if (!silent) memuatJadwal.value = false
  }
}

function muatKalender() {
  return kalender.jalankan(slug.value, { hari: 14, olahraga: olahraga.value })
}

function sinkronQuery() {
  const query = { tanggal: tanggal.value }
  if (olahraga.value) query.olahraga = olahraga.value
  router.replace({ query })
}

watch(tanggal, () => {
  pilihan.value = null
  sinkronQuery()
  muatSlot()
})

watch(olahraga, () => {
  pilihan.value = null
  sinkronQuery()
  muatSlot()
  muatKalender()
})

function klik(courtId, j) {
  const court = courtsSlot.value.find((c) => c.court.id === courtId)
  const sebelum = pilihan.value?.courtId === courtId ? pilihan.value : null
  const hasil = klikSlot(sebelum, j, court.slots, MAKS_DURASI)
  pilihan.value = hasil ? { courtId, ...hasil } : null
}

// pilihan dari query (setelah kembali dari halaman login) dipulihkan kalau slot masih kosong
function pulihkanPilihan() {
  const { court, mulai, durasi } = route.query
  if (!court) return
  const c = courtsSlot.value.find((x) => x.court.id === Number(court))
  const m = Number(mulai)
  const d = Number(durasi)
  const masihKosong = c && Array.from({ length: d }, (_, i) => m + i).every(
    (j) => c.slots.find((s) => s.jam === j)?.status === 'tersedia',
  )
  if (masihKosong) pilihan.value = { courtId: c.court.id, mulai: m, durasi: d }
  sinkronQuery()
}

async function booking() {
  if (!pilihan.value) return
  if (!auth.sudahLogin) {
    // pilihan dibawa lewat query supaya bisa dipulihkan setelah login
    const query = {
      tanggal: tanggal.value,
      ...(olahraga.value ? { olahraga: olahraga.value } : {}),
      court: pilihan.value.courtId,
      mulai: pilihan.value.mulai,
      durasi: pilihan.value.durasi,
    }
    const tujuan = router.resolve({ name: 'venue', params: { slug: slug.value }, query })
    router.push({ name: 'login', query: { redirect: tujuan.fullPath } })
    return
  }
  mengirim.value = true
  try {
    const hasil = await bookingApi.buat({
      court_id: pilihan.value.courtId,
      tanggal: tanggal.value,
      jam_mulai: pilihan.value.mulai,
      durasi: pilihan.value.durasi,
      catatan: catatan.value.trim() || null,
    })
    toast.sukses(`Booking ${hasil.kode} dibuat. Bayar DP sebelum batas waktu supaya slot tidak lepas.`)
    router.push({ name: 'booking-detail', params: { kode: hasil.kode } })
  } catch (e) {
    toast.gagal(e.message)
    if (e.status === 409) {
      pilihan.value = null
      muatSlot()
      muatKalender()
    }
  } finally {
    mengirim.value = false
  }
}

// segarkan slot tiap menit selama halaman terbuka supaya status tidak basi
let timer
onMounted(async () => {
  await venue.jalankan(slug.value)
  await Promise.all([muatKalender(), muatSlot()])
  pulihkanPilihan()
  timer = setInterval(() => {
    if (document.visibilityState === 'visible' && !mengirim.value) muatSlot(true)
  }, 60_000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="container page" :class="{ 'ada-bar': ringkasan }">
    <RequestState
      :loading="venue.loading.value"
      :error="venue.error.value"
      :tinggi="240"
      @ulang="venue.jalankan(slug)"
    >
      <template v-if="venue.data.value">
        <nav class="small crumb" aria-label="Breadcrumb">
          <RouterLink to="/">Venue</RouterLink> <span class="muted">/ {{ venue.data.value.nama }}</span>
        </nav>

        <header class="kepala card">
          <div class="kepala-utama">
            <div class="ikon-olahraga" aria-hidden="true">
              <span v-for="o in olahragaVenue" :key="o" class="ikon-bulat"><AppIcon :name="o" :size="20" /></span>
            </div>
            <h1>{{ venue.data.value.nama }}</h1>
            <p class="muted">{{ venue.data.value.alamat }}</p>
            <p v-if="venue.data.value.deskripsi" class="deskripsi">{{ venue.data.value.deskripsi }}</p>
            <ul class="fasilitas">
              <li v-for="f in venue.data.value.fasilitas" :key="f" class="badge plain">{{ f }}</li>
            </ul>
          </div>
          <dl class="info">
            <div>
              <dt>Konfirmasi booking</dt>
              <dd>{{ MODE_KONFIRMASI[venue.data.value.mode_konfirmasi] }}</dd>
            </div>
            <div>
              <dt>Deposit (DP)</dt>
              <dd>{{ venue.data.value.persen_deposit }}% dari total</dd>
            </div>
            <div>
              <dt>Batas bayar DP</dt>
              <dd>{{ venue.data.value.batas_bayar_menit }} menit setelah booking</dd>
            </div>
            <div v-if="venue.data.value.telepon">
              <dt>Telepon</dt>
              <dd>{{ venue.data.value.telepon }}</dd>
            </div>
          </dl>
        </header>

        <div class="tata">
          <section class="utama" aria-label="Ketersediaan slot">
            <!-- Galeri Foto Lapang & Fasilitas -->
            <VenueGallery :slug="venue.data.value.slug" :venue-nama="venue.data.value.nama" />

            <details class="card jadwal">
              <summary>
                <strong>Jam operasional & tarif</strong>
                <span class="muted small">Tarif weekday berlaku Senin–Jumat, weekend Sabtu–Minggu</span>
              </summary>
              <div class="jadwal-isi">
                <table class="table">
                  <thead>
                    <tr><th>Hari</th><th>Jam buka</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="j in jadwalPerHari" :key="j.hari">
                      <td>{{ HARI_SENIN[j.hari] }}</td>
                      <td class="num">{{ j.is_tutup ? 'Tutup' : rentangJam(j.jam_buka, j.jam_tutup) }}</td>
                    </tr>
                  </tbody>
                </table>
                <table class="table">
                  <thead>
                    <tr><th>Lapang</th><th>Weekday</th><th>Weekend</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="c in venue.data.value.courts" :key="c.id">
                      <td><span class="sel-ikon"><AppIcon :name="c.olahraga" :size="16" />{{ c.nama }}</span></td>
                      <td class="num">{{ rupiah(c.tarif_weekday) }}</td>
                      <td class="num">{{ rupiah(c.tarif_weekend) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>

            <div v-if="olahragaVenue.length > 1" class="filter" role="group" aria-label="Filter olahraga">
              <button class="chip" :aria-pressed="olahraga === ''" @click="olahraga = ''">Semua</button>
              <button
                v-for="o in olahragaVenue"
                :key="o"
                class="chip"
                :aria-pressed="olahraga === o"
                @click="olahraga = o"
              >
                <AppIcon :name="o" :size="16" /> {{ infoOlahraga(o).label }}
              </button>
            </div>

            <div class="blok">
              <h2 class="blok-judul">Pilih tanggal</h2>
              <RequestState :loading="kalender.loading.value && !kalender.data.value" :error="kalender.error.value" :tinggi="96" :baris="1" @ulang="muatKalender">
                <DateStrip v-model="tanggal" :hari="kalender.data.value || []" />
              </RequestState>
            </div>

            <div class="blok">
              <div class="blok-kepala">
                <div class="blok-judul-grup">
                  <h2 class="blok-judul">Slot {{ tanggalPanjang(tanggal) }}</h2>
                  <transition name="fade">
                    <span v-if="memuatJadwal" class="memuat-slot-tag" aria-live="polite">
                      <span class="spinner" aria-hidden="true" /> Memuat slot...
                    </span>
                  </transition>
                </div>
                <ul class="legenda small" aria-label="Keterangan warna slot">
                  <li v-for="(label, kode) in STATUS_SLOT" :key="kode"><span :class="['kotak', kode]" />{{ label }}</li>
                </ul>
              </div>

              <RequestState
                :loading="slot.loading.value && !slot.data.value"
                :error="slot.error.value"
                :tinggi="260"
                @ulang="muatSlot"
              >
                <div class="slot-kontainer">
                  <transition name="fade">
                    <div v-if="memuatJadwal && slot.data.value" class="slot-overlay" aria-live="polite">
                      <div class="overlay-kotak">
                        <span class="spinner" aria-hidden="true" />
                        <span>Memperbarui jadwal slot...</span>
                      </div>
                    </div>
                  </transition>

                  <div :class="{ 'sedang-memuat': memuatJadwal }">
                    <div v-if="slot.data.value?.is_tutup" class="alert warning">
                      Venue tutup pada {{ slot.data.value.hari }}. Pilih tanggal lain.
                    </div>
                    <div v-else class="courts">
                      <article
                        v-for="c in courtsSlot"
                        :key="c.court.id"
                        class="court card"
                        :class="{ aktif: pilihan?.courtId === c.court.id }"
                      >
                        <div class="court-kepala">
                          <div>
                            <h3>
                              <AppIcon :name="c.court.olahraga" :size="20" />
                              {{ c.court.nama }}
                            </h3>
                            <p class="muted small">
                              {{ infoOlahraga(c.court.olahraga).panjang }} · {{ c.court.permukaan }} ·
                              {{ c.court.is_indoor ? 'Indoor' : 'Outdoor' }}
                              <template v-if="c.court.kapasitas"> · {{ c.court.kapasitas }} pemain</template>
                            </p>
                          </div>
                          <div class="tarif">
                            <strong>{{ rupiah(c.tarif_per_jam) }}</strong><span class="muted small">/jam</span>
                            <span class="badge" :class="slot.data.value.is_weekend ? 'warning' : 'info'">
                              {{ slot.data.value.is_weekend ? 'Tarif weekend' : 'Tarif weekday' }}
                            </span>
                          </div>
                        </div>
                        <SlotGrid
                          :slots="c.slots"
                          :pilihan="pilihan?.courtId === c.court.id ? pilihan : null"
                          @klik="(j) => klik(c.court.id, j)"
                        />
                        <p v-if="c.slot_tersedia === 0" class="muted small">Tidak ada slot kosong di tanggal ini.</p>
                      </article>
                    </div>
                  </div>
                </div>
              </RequestState>
            </div>
          </section>

          <aside class="samping" aria-label="Ringkasan booking">
            <div class="card ringkas">
              <h2 class="card-title">Ringkasan booking</h2>
              <template v-if="ringkasan">
                <dl class="rincian">
                  <div><dt>Lapang</dt><dd>{{ courtDipilih.court.nama }}</dd></div>
                  <div><dt>Tanggal</dt><dd>{{ tanggalPanjang(tanggal) }}</dd></div>
                  <div>
                    <dt>Jam</dt>
                    <dd class="num">{{ rentangJam(pilihan.mulai, pilihan.mulai + pilihan.durasi) }} ({{ pilihan.durasi }} jam)</dd>
                  </div>
                  <div>
                    <dt>Tarif</dt>
                    <dd class="num">{{ rupiah(ringkasan.tarif) }} × {{ pilihan.durasi }}</dd>
                  </div>
                  <div class="total"><dt>Total</dt><dd class="num">{{ rupiah(ringkasan.total) }}</dd></div>
                  <div class="dp">
                    <dt>DP {{ ringkasan.persen }}% dibayar sekarang</dt>
                    <dd class="num">{{ rupiah(ringkasan.deposit) }}</dd>
                  </div>
                </dl>
                <label v-if="auth.isCustomer" class="field">
                  <span>Catatan untuk venue (opsional)</span>
                  <textarea v-model="catatan" class="textarea" maxlength="300" rows="2" placeholder="Mis. butuh sewa raket 2" />
                </label>
                <button
                  class="btn btn-accent btn-lg btn-block"
                  :disabled="mengirim || auth.isManager"
                  @click="booking"
                >
                  <span v-if="mengirim" class="spinner" aria-hidden="true" />
                  {{ mengirim ? 'Membuat booking...' : (auth.sudahLogin ? 'Booking sekarang' : 'Login untuk booking') }}
                </button>
                <p v-if="auth.isManager" class="muted small">Akun venue manager tidak bisa membuat booking.</p>
                <p v-else class="muted small">
                  Slot ditahan {{ venue.data.value.batas_bayar_menit }} menit sampai DP dibayar.
                  {{ venue.data.value.mode_konfirmasi === 'manual' ? 'Setelah DP, manager venue akan menyetujui booking.' : 'Booking langsung terkonfirmasi setelah DP masuk.' }}
                </p>
              </template>
              <p v-else class="muted kosong">
                Klik jam yang masih tersedia. Untuk main lebih dari satu jam, klik jam berikutnya
                (maksimal {{ MAKS_DURASI }} jam berurutan).
              </p>
            </div>
          </aside>
        </div>

        <div v-if="ringkasan" class="bar-hp">
          <div>
            <strong class="num">{{ rupiah(ringkasan.total) }}</strong>
            <span class="muted small">{{ courtDipilih.court.nama }} · {{ jam(pilihan.mulai) }}, {{ pilihan.durasi }} jam</span>
          </div>
          <button class="btn btn-accent" :disabled="mengirim || auth.isManager" @click="booking">
            <span v-if="mengirim" class="spinner" aria-hidden="true" />
            {{ mengirim ? 'Memproses...' : (auth.sudahLogin ? 'Booking' : 'Login') }}
          </button>
        </div>
      </template>
    </RequestState>
  </div>
</template>

<style scoped>
.crumb {
  margin-bottom: 12px;
}

.kepala {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: 24px;
  padding: 24px;
}

.ikon-olahraga {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.ikon-bulat {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--brand-soft);
  color: var(--brand-ink);
}

.sel-ikon {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.kepala h1 {
  font-size: clamp(1.5rem, 3vw, 2rem);
}

.deskripsi {
  margin-top: 10px;
  color: var(--text-2);
  max-width: 640px;
}

.fasilitas {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 14px;
}

.info {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 16px;
  border-radius: var(--radius);
  background: var(--surface-2);
  align-content: start;
}

.info dt {
  font-size: 0.78rem;
  color: var(--muted);
  font-weight: 600;
}

.info dd {
  margin: 0;
  font-weight: 600;
}

.tata {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 24px;
  margin-top: 24px;
  align-items: start;
}

/* anak grid wajib min-width 0, kalau tidak strip tanggal melebarkan halaman di HP */
.utama {
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-width: 0;
}

.jadwal summary {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 12px;
  padding: 14px 18px;
  cursor: pointer;
}

.jadwal-isi {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
  gap: 16px;
  padding: 0 18px 16px;
}

.filter {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.blok {
  min-width: 0;
}

.blok-kepala {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
  margin-bottom: 12px;
}

.blok-judul-grup {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.memuat-slot-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--brand-ink);
  background: var(--brand-soft);
  padding: 3px 10px;
  border-radius: 999px;
  line-height: 1.2;
}

.memuat-slot-tag .spinner {
  width: 12px;
  height: 12px;
  border-width: 1.5px;
}

.slot-kontainer {
  position: relative;
  min-height: 200px;
}

.slot-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 50px;
  background: color-mix(in srgb, var(--surface) 55%, transparent);
  backdrop-filter: blur(1.5px);
  border-radius: var(--radius);
  pointer-events: none;
}

.overlay-kotak {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  box-shadow: var(--shadow);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text);
}

.sedang-memuat {
  opacity: 0.35;
  filter: grayscale(35%);
  pointer-events: none;
  transition: opacity 0.2s ease, filter 0.2s ease;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.blok-judul {
  font-size: 1.1rem;
  margin-bottom: 10px;
}

.blok-kepala .blok-judul {
  margin-bottom: 0;
}

.legenda {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  color: var(--muted);
}

.legenda li {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.kotak {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  border: 1px solid var(--border-strong);
  background: var(--surface-2);
}

.kotak.tersedia {
  background: var(--surface);
  border-color: var(--brand);
}

.kotak.menunggu {
  background: var(--warning-soft);
  border-color: var(--warning);
}

.kotak.milik_saya {
  background: var(--info-soft);
  border-color: var(--info);
}

.kotak.ditutup {
  background: repeating-linear-gradient(135deg, var(--surface-2) 0 3px, var(--border-strong) 3px 5px);
}

.kotak.lewat {
  opacity: 0.45;
}

.courts {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.court {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 18px 18px;
  transition: border-color 0.15s;
}

.court.aktif {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-soft);
}

.court-kepala {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px 16px;
}

.court h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.05rem;
}

.court h3 .ikon-svg {
  color: var(--brand-ink);
}

.tarif {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.samping {
  position: sticky;
  top: 84px;
}

.ringkas {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
}

.rincian {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
}

.rincian div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.92rem;
}

.rincian dt {
  color: var(--muted);
}

.rincian dd {
  margin: 0;
  font-weight: 600;
  text-align: right;
}

.rincian .total {
  padding-top: 10px;
  border-top: 1px solid var(--border);
  font-size: 1rem;
}

.rincian .total dd {
  font-weight: 800;
}

.rincian .dp {
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--brand-soft);
}

.rincian .dp dt,
.rincian .dp dd {
  color: var(--brand-ink);
  font-weight: 700;
}

.kosong {
  font-size: 0.92rem;
}

.bar-hp {
  display: none;
}

@media (max-width: 900px) {
  .kepala,
  .tata,
  .jadwal-isi {
    grid-template-columns: minmax(0, 1fr);
  }

  .samping {
    position: static;
  }

  .ada-bar {
    padding-bottom: 110px;
  }

  .bar-hp {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 30;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 16px;
    background: var(--surface);
    border-top: 1px solid var(--border);
    box-shadow: 0 -8px 24px rgb(0 0 0 / 10%);
  }

  .bar-hp > div {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
}
</style>
