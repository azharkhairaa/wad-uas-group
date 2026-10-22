<script setup>
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { managerApi } from '@/api'
import BarList from '@/components/charts/BarList.vue'
import ColumnChart from '@/components/charts/ColumnChart.vue'
import KpiTile from '@/components/KpiTile.vue'
import RequestState from '@/components/RequestState.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useRequest } from '@/composables/useRequest'
import { useManagerStore } from '@/stores/manager'
import { useToastStore } from '@/stores/toast'
import { geserHari, hariIniIso, keTanggal, persen, rentangJam, rupiah, rupiahRingkas, tanggalPanjang, tanggalPendek } from '@/utils/format'
import { infoOlahraga } from '@/utils/olahraga'

const manager = useManagerStore()
const toast = useToastStore()
const venueId = computed(() => manager.venue.id)

const PERIODE = [
  { kode: 'default', label: '14 hari lalu + 7 hari ke depan', dari: -13, sampai: 7 },
  { kode: '30', label: '30 hari terakhir', dari: -29, sampai: 0 },
  { kode: '7', label: '7 hari ke depan', dari: 0, sampai: 6 },
]
const periode = ref('default')
const dash = useRequest(managerApi.dashboard)
const antrean = useRequest(managerApi.bookings)
const memproses = ref('')

function muat() {
  const p = PERIODE.find((x) => x.kode === periode.value)
  const hariIni = hariIniIso()
  dash.jalankan(venueId.value, { dari: geserHari(hariIni, p.dari), sampai: geserHari(hariIni, p.sampai) })
  antrean.jalankan({ venue_id: venueId.value, status: 'menunggu_persetujuan', per_page: 5 })
}
watch(periode, muat)
muat()

const d = computed(() => dash.data.value)
const hariIni = hariIniIso()

const harian = computed(() =>
  (d.value?.harian || []).map((h) => {
    const t = keTanggal(h.tanggal)
    return {
      key: h.tanggal,
      label: `${t.getDate()}`,
      judul: tanggalPanjang(h.tanggal),
      nilai: h.okupansi_persen,
      kategori: h.is_mendatang ? 'mendatang' : 'lewat',
      detail: `${h.jam_terisi} dari ${h.jam_tersedia} jam terisi`,
    }
  }),
)

const legendaHarian = computed(() => {
  const ada = new Set(harian.value.map((h) => h.kategori))
  return [
    { kategori: 'lewat', label: 'Sudah berjalan' },
    { kategori: 'mendatang', label: 'Sudah dipesan untuk hari mendatang' },
  ].filter((l) => ada.has(l.kategori))
})

const perCourt = computed(() =>
  [...(d.value?.per_court || [])]
    .sort((a, b) => b.okupansi_persen - a.okupansi_persen)
    .map((c) => ({
      key: c.court_id,
      label: c.nama,
      sub: infoOlahraga(c.olahraga).label,
      nilai: c.okupansi_persen,
      detail: `${c.jam_terisi} dari ${c.jam_tersedia} jam`,
    })),
)

const perOlahraga = computed(() =>
  (d.value?.per_olahraga || []).map((o) => ({
    key: o.olahraga,
    label: infoOlahraga(o.olahraga).label,
    ikon: o.olahraga,
    nilai: o.okupansi_persen,
    detail: `${o.jam_terisi} dari ${o.jam_tersedia} jam`,
  })),
)

const jamSibuk = computed(() =>
  (d.value?.jam_sibuk || []).map((j) => ({
    key: String(j.jam),
    label: String(j.jam).padStart(2, '0'),
    judul: rentangJam(j.jam, j.jam + 1),
    nilai: j.jumlah,
    detail: 'jam terisi selama periode',
  })),
)

const totalStatus = computed(() => (d.value?.status || []).reduce((n, s) => n + s.jumlah, 0))

async function setujui(kode) {
  memproses.value = kode
  try {
    await managerApi.setujui(kode)
    toast.sukses(`Booking ${kode} disetujui.`)
    muat()
  } catch (e) {
    toast.gagal(e.message)
  } finally {
    memproses.value = ''
  }
}
</script>

<template>
  <div class="stack">
    <div class="page-head">
      <div>
        <h1>Dashboard</h1>
        <p>{{ manager.venue.nama }} · okupansi dan booking</p>
      </div>
      <div class="tabs" role="tablist" aria-label="Periode">
        <button v-for="p in PERIODE" :key="p.kode" role="tab" :aria-selected="periode === p.kode" @click="periode = p.kode">
          {{ p.label }}
        </button>
      </div>
    </div>

    <RequestState :loading="dash.loading.value && !d" :error="dash.error.value" :tinggi="420" @ulang="muat">
      <template v-if="d">
        <div class="kpi-grid">
          <KpiTile
            hero
            label="Okupansi periode ini"
            :nilai="persen(d.ringkasan.okupansi_persen)"
            :ket="`${d.ringkasan.jam_terisi.toLocaleString('id-ID')} dari ${d.ringkasan.jam_tersedia.toLocaleString('id-ID')} jam lapang terisi`"
          />
          <KpiTile label="Booking terkonfirmasi" :nilai="String(d.ringkasan.booking_terkonfirmasi)" ket="termasuk yang sudah selesai" />
          <KpiTile label="Booking hari ini" :nilai="String(d.ringkasan.booking_hari_ini)" :ket="tanggalPendek(hariIni)" />
          <KpiTile label="Menunggu persetujuan" :nilai="String(d.ringkasan.menunggu_tindakan)" ket="perlu tindakan kamu">
            <RouterLink v-if="d.ringkasan.menunggu_tindakan" :to="{ name: 'manager-bookings', query: { status: 'menunggu_persetujuan' } }" class="small">
              Tinjau
            </RouterLink>
          </KpiTile>
          <KpiTile
            class="kpi-pendapatan"
            label="Pendapatan bersih"
            :nilai="rupiah(d.ringkasan.pendapatan)"
            ket="DP + pelunasan − refund"
          />
        </div>

        <section class="card card-body">
          <div class="judul">
            <div>
              <h2 class="card-title">Okupansi harian</h2>
              <p class="card-sub">Jam terisi (booking terkonfirmasi atau selesai) dibagi jam buka semua lapang</p>
            </div>
          </div>
          <ColumnChart
            :items="harian"
            :maks="100"
            :format="persen"
            :legenda="legendaHarian"
            :penanda="hariIni"
            judul-tabel="Okupansi harian"
          />
        </section>

        <div class="dua">
          <section class="card card-body">
            <h2 class="card-title">Okupansi per lapang</h2>
            <p class="card-sub">Diurutkan dari yang paling ramai</p>
            <BarList class="isi-kartu" :items="perCourt" :maks="100" :format="persen" />
          </section>
          <section class="card card-body">
            <h2 class="card-title">Okupansi per olahraga</h2>
            <p class="card-sub">Gabungan semua lapang dengan jenis olahraga yang sama</p>
            <BarList class="isi-kartu" :items="perOlahraga" :maks="100" :format="persen" />
          </section>
        </div>

        <div class="dua">
          <section class="card card-body">
            <h2 class="card-title">Jam sibuk</h2>
            <p class="card-sub">Jumlah jam lapang terisi per jam mulai, seluruh periode</p>
            <ColumnChart class="isi-kartu" :items="jamSibuk" :tinggi="180" :label-setiap="2" judul-tabel="Jam sibuk" />
          </section>
          <section class="card card-body">
            <h2 class="card-title">Status booking</h2>
            <p class="card-sub">{{ totalStatus }} booking dengan tanggal main di periode ini</p>
            <ul class="status-list isi-kartu">
              <li v-for="s in d.status" :key="s.status">
                <StatusBadge :status="s.status" />
                <span class="num">{{ s.jumlah }}</span>
                <span class="muted small num">{{ persen(totalStatus ? (s.jumlah / totalStatus) * 100 : 0) }}</span>
              </li>
            </ul>
          </section>
        </div>
      </template>
    </RequestState>

    <section class="card card-body">
      <div class="judul">
        <div>
          <h2 class="card-title">Perlu persetujuan</h2>
          <p class="card-sub">DP sudah dibayar, tinggal disetujui atau ditolak</p>
        </div>
        <RouterLink :to="{ name: 'manager-bookings', query: { status: 'menunggu_persetujuan' } }" class="small">Lihat semua</RouterLink>
      </div>
      <RequestState
        :loading="antrean.loading.value && !antrean.data.value"
        :error="antrean.error.value"
        :kosong="antrean.kosong.value"
        judul-kosong="Tidak ada antrean"
        pesan-kosong="Semua booking sudah ditangani."
        :baris="2"
        :tinggi="100"
        @ulang="muat"
      >
        <ul class="antrean">
          <li v-for="b in antrean.data.value?.items" :key="b.id">
            <div class="antrean-info">
              <strong>{{ b.customer.nama }}</strong>
              <span class="muted small">
                {{ b.court.nama }} · {{ tanggalPanjang(b.tanggal) }} · {{ rentangJam(b.jam_mulai, b.jam_selesai) }}
              </span>
              <span class="small">DP {{ rupiah(b.jumlah_dibayar) }} dari {{ rupiahRingkas(b.total_harga) }}</span>
            </div>
            <div class="row">
              <!-- menolak butuh alasan, jadi diarahkan ke detail booking -->
              <RouterLink :to="{ name: 'manager-bookings', query: { q: b.kode } }" class="btn btn-outline btn-sm">Detail</RouterLink>
              <button class="btn btn-primary btn-sm" :disabled="memproses === b.kode" @click="setujui(b.kode)">Setujui</button>
            </div>
          </li>
        </ul>
      </RequestState>
    </section>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: 0;
}

.kpi-grid {
  display: grid;
  grid-template-columns: 1.4fr repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.kpi-pendapatan {
  grid-column: 1 / -1;
}

.kpi-pendapatan :deep(.nilai) {
  font-size: 1.85rem;
  white-space: nowrap;
}

.judul {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 18px;
}

.dua {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.isi-kartu {
  margin-top: 16px;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-list li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 52px;
  align-items: center;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}

.status-list li:last-child {
  border-bottom: 0;
}

/* badge boleh turun baris di layar sempit supaya halaman tidak melebar */
.status-list .badge {
  justify-self: start;
  max-width: 100%;
  white-space: normal;
}

.status-list li > :nth-child(3) {
  text-align: right;
}

.antrean {
  display: flex;
  flex-direction: column;
}

.antrean li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.antrean li:last-child {
  border-bottom: 0;
}

.antrean-info {
  display: flex;
  flex-direction: column;
}

@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .kpi-grid > :first-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .dua {
    grid-template-columns: minmax(0, 1fr);
  }

  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .kpi-grid > :nth-child(4) {
    grid-column: 1 / -1;
  }
}

@media (max-width: 520px) {
  .kpi-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
