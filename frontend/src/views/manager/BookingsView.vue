<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { managerApi } from '@/api'
import AppIcon from '@/components/AppIcon'
import ModalDialog from '@/components/ModalDialog.vue'
import RequestState from '@/components/RequestState.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useRequest } from '@/composables/useRequest'
import { useManagerStore } from '@/stores/manager'
import { useToastStore } from '@/stores/toast'
import { rentangJam, rupiah, tanggalPanjang, tanggalSingkat, waktuLengkap } from '@/utils/format'
import { JENIS_BAYAR, METODE_BAYAR, STATUS_BOOKING } from '@/utils/status'

const route = useRoute()
const router = useRouter()
const manager = useManagerStore()
const toast = useToastStore()

const filter = ref({
  status: route.query.status || '',
  tanggal: route.query.tanggal || '',
  court_id: route.query.court_id || '',
  q: route.query.q || '',
  page: 1,
})
const { data, loading, error, kosong, jalankan } = useRequest(managerApi.bookings)
const PER_HALAMAN = 15

function muat() {
  jalankan({ venue_id: manager.venue.id, per_page: PER_HALAMAN, ...filter.value })
  const query = Object.fromEntries(Object.entries(filter.value).filter(([k, v]) => v && k !== 'page'))
  router.replace({ query })
}

let jeda
watch(
  () => [filter.value.status, filter.value.tanggal, filter.value.court_id],
  () => {
    filter.value.page = 1
    muat()
  },
)
watch(
  () => filter.value.q,
  () => {
    clearTimeout(jeda)
    jeda = setTimeout(() => {
      filter.value.page = 1
      muat()
    }, 300)
  },
)
onBeforeUnmount(() => clearTimeout(jeda))
muat()

const jumlahHalaman = computed(() => Math.max(1, Math.ceil((data.value?.total || 0) / PER_HALAMAN)))

function halaman(arah) {
  filter.value.page = Math.min(jumlahHalaman.value, Math.max(1, filter.value.page + arah))
  muat()
}

// detail & aksi
const detail = ref(null)
const memproses = ref(false)
const modalAlasan = ref(null) // 'tolak' | 'batal'
const alasan = ref('')
const modalBayar = ref(false)
const metodeBayar = ref('qris')

async function buka(kode) {
  try {
    detail.value = await managerApi.booking(kode)
  } catch (e) {
    toast.gagal(e.message)
  }
}

function isLewatBelumLunas(b) {
  if (b.status !== 'terkonfirmasi' || (b.sisa_tagihan || 0) <= 0) return false
  const mulai = new Date(`${b.tanggal}T${String(b.jam_mulai).padStart(2, '0')}:00:00`)
  return mulai <= new Date()
}

const bisa = computed(() => {
  const b = detail.value
  if (!b) return {}
  const mulai = new Date(`${b.tanggal}T${String(b.jam_mulai).padStart(2, '0')}:00:00`)
  const lewat = mulai <= new Date()
  const menunggu = ['menunggu_pembayaran', 'menunggu_persetujuan'].includes(b.status)
  const lunas = (b.sisa_tagihan || 0) <= 0
  return {
    setujui: menunggu && !lewat,
    tolak: menunggu,
    selesai: b.status === 'terkonfirmasi' && lewat && lunas,
    lewatBelumLunas: b.status === 'terkonfirmasi' && lewat && !lunas,
    batal: b.status === 'terkonfirmasi' && !lewat,
    catatPelunasan: (b.status === 'terkonfirmasi' || menunggu) && !lunas,
  }
})

async function konfirmasiPelunasan() {
  memproses.value = true
  try {
    detail.value = await managerApi.bayar(detail.value.kode, {
      jenis: 'pelunasan',
      metode: metodeBayar.value,
    })
    toast.sukses(`Pelunasan booking ${detail.value.kode} berhasil dicatat.`)
    modalBayar.value = false
    muat()
  } catch (e) {
    toast.gagal(e.message)
  } finally {
    memproses.value = false
  }
}

async function jalankanAksi(jenis) {
  memproses.value = true
  const kode = detail.value.kode
  try {
    if (jenis === 'setujui') detail.value = await managerApi.setujui(kode)
    if (jenis === 'selesai') detail.value = await managerApi.selesai(kode)
    if (jenis === 'tolak') detail.value = await managerApi.tolak(kode, alasan.value.trim())
    if (jenis === 'batal') detail.value = await managerApi.batalkan(kode, alasan.value.trim())
    const pesan = {
      setujui: 'Booking disetujui dan terkonfirmasi.',
      selesai: 'Booking ditandai selesai.',
      tolak: 'Booking ditolak, slot dilepas dan DP dikembalikan.',
      batal: 'Booking dibatalkan, pembayaran dikembalikan penuh.',
    }
    toast.sukses(pesan[jenis])
    modalAlasan.value = null
    alasan.value = ''
    muat()
  } catch (e) {
    toast.gagal(e.message)
  } finally {
    memproses.value = false
  }
}

if (route.query.q) buka(route.query.q)
</script>

<template>
  <div class="stack">
    <div class="page-head">
      <div>
        <h1>Booking masuk</h1>
        <p>{{ manager.venue.nama }} · urut dari yang terbaru dibuat</p>
      </div>
    </div>

    <div class="card filter">
      <label class="field">
        <span>Status</span>
        <select v-model="filter.status" class="select">
          <option value="">Semua status</option>
          <option v-for="(s, kode) in STATUS_BOOKING" :key="kode" :value="kode">{{ s.label }}</option>
        </select>
      </label>
      <label class="field">
        <span>Tanggal main</span>
        <input v-model="filter.tanggal" class="input" type="date" />
      </label>
      <label class="field">
        <span>Lapang</span>
        <select v-model="filter.court_id" class="select">
          <option value="">Semua lapang</option>
          <option v-for="c in manager.venue.courts" :key="c.id" :value="String(c.id)">{{ c.nama }}</option>
        </select>
      </label>
      <label class="field cari">
        <span>Cari</span>
        <input v-model="filter.q" class="input" type="search" placeholder="Kode booking atau nama customer" maxlength="60" />
      </label>
    </div>

    <RequestState
      :loading="loading && !data"
      :error="error"
      :kosong="kosong"
      judul-kosong="Tidak ada booking"
      pesan-kosong="Coba ubah filter di atas."
      :tinggi="360"
      @ulang="muat"
    >
      <div class="card">
        <div class="table-wrap">
          <table class="table" :class="{ redup: loading }">
            <thead>
              <tr>
                <th>Booking</th>
                <th>Jadwal</th>
                <th>Dibayar</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in data?.items" :key="b.id" class="baris" @click="buka(b.kode)">
                <td>
                  <button type="button" class="nama-btn" @click.stop="buka(b.kode)">{{ b.customer.nama }}</button>
                  <div class="muted small num nowrap">{{ b.kode }}</div>
                </td>
                <td class="nowrap">
                  <span class="sel-ikon"><AppIcon :name="b.court.olahraga" :size="16" />{{ b.court.nama }}</span>
                  <div class="muted small num">{{ tanggalSingkat(b.tanggal) }} · {{ rentangJam(b.jam_mulai, b.jam_selesai) }}</div>
                </td>
                <td class="num nowrap">
                  {{ rupiah(b.jumlah_dibayar) }}
                  <div class="muted small">dari {{ rupiah(b.total_harga) }}</div>
                  <div v-if="isLewatBelumLunas(b)">
                    <span class="badge danger plain mini" style="display: inline-block; margin-top: 4px;" title="Jadwal main sudah lewat namun belum lunas">
                      Belum lunas (Sisa {{ rupiah(b.sisa_tagihan) }})
                    </span>
                  </div>
                </td>
                <td><StatusBadge :status="b.status" /></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="halaman">
          <span class="muted small">{{ data?.total || 0 }} booking · halaman {{ filter.page }} dari {{ jumlahHalaman }}</span>
          <div class="row">
            <button class="btn btn-outline btn-sm" :disabled="filter.page <= 1" @click="halaman(-1)">‹ Sebelumnya</button>
            <button class="btn btn-outline btn-sm" :disabled="filter.page >= jumlahHalaman" @click="halaman(1)">Berikutnya ›</button>
          </div>
        </div>
      </div>
    </RequestState>

    <ModalDialog :buka="!!detail" :judul="detail ? `Booking ${detail.kode}` : ''" :lebar="620" @tutup="detail = null">
      <div v-if="detail" class="stack">
        <div class="row">
          <StatusBadge :status="detail.status" />
          <span class="muted small">dibuat {{ waktuLengkap(detail.created_at) }}</span>
        </div>
        <dl class="rincian">
          <div><dt>Customer</dt><dd>{{ detail.customer.nama }} · {{ detail.customer.email }}</dd></div>
          <div v-if="detail.customer.no_hp"><dt>No. HP</dt><dd>{{ detail.customer.no_hp }}</dd></div>
          <div><dt>Lapang</dt><dd>{{ detail.court.nama }}</dd></div>
          <div><dt>Jadwal</dt><dd>{{ tanggalPanjang(detail.tanggal) }}, {{ rentangJam(detail.jam_mulai, detail.jam_selesai) }}</dd></div>
          <div><dt>Total</dt><dd class="num">{{ rupiah(detail.total_harga) }}</dd></div>
          <div><dt>Sudah dibayar</dt><dd class="num">{{ rupiah(detail.jumlah_dibayar) }}</dd></div>
          <div v-if="detail.sisa_tagihan > 0">
            <dt>Sisa tagihan</dt>
            <dd class="num" style="color: var(--danger, #dc2626); font-weight: 700;">
              {{ rupiah(detail.sisa_tagihan) }} (Belum lunas)
            </dd>
          </div>
          <div v-else-if="detail.jumlah_dibayar > 0">
            <dt>Status bayar</dt>
            <dd><span class="badge success plain mini">Lunas</span></dd>
          </div>
          <div v-if="detail.catatan"><dt>Catatan</dt><dd>{{ detail.catatan }}</dd></div>
          <div v-if="detail.alasan_batal"><dt>Alasan</dt><dd>{{ detail.alasan_batal }}</dd></div>
        </dl>
        <div v-if="detail.payments.length" class="table-wrap">
          <table class="table">
            <thead><tr><th>Jenis</th><th>Metode</th><th>Waktu</th><th>Nominal</th></tr></thead>
            <tbody>
              <tr v-for="p in detail.payments" :key="p.id">
                <td>{{ JENIS_BAYAR[p.jenis] }}</td>
                <td>{{ METODE_BAYAR[p.metode] }}</td>
                <td class="small">{{ waktuLengkap(p.created_at) }}</td>
                <td class="num">{{ p.jenis === 'refund' ? '−' : '' }}{{ rupiah(p.nominal) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="detail.status === 'menunggu_pembayaran'" class="alert warning small">
          Customer belum membayar DP. Setujui hanya kalau pembayaran diterima langsung di lokasi.
        </p>
        <div v-if="bisa.lewatBelumLunas" class="alert danger small">
          <strong>⚠️ Jadwal Main Sudah Lewat Namun Belum Lunas</strong>
          <p style="margin: 4px 0 0;">
            Customer memiliki tunggakan sisa tagihan sebesar <strong>{{ rupiah(detail.sisa_tagihan) }}</strong>. Sesuai ketentuan, booking <strong>tidak dapat ditandai selesai</strong> sebelum pelunasan dicatat. Silakan gunakan tombol "Catat Pelunasan" jika customer membayar di lokasi kasir venue.
          </p>
        </div>
      </div>
      <template v-if="detail && (bisa.setujui || bisa.tolak || bisa.selesai || bisa.batal || bisa.lewatBelumLunas || bisa.catatPelunasan)" #aksi>
        <button v-if="bisa.tolak" class="btn btn-danger" :disabled="memproses" @click="modalAlasan = 'tolak'">Tolak</button>
        <button v-if="bisa.batal" class="btn btn-danger" :disabled="memproses" @click="modalAlasan = 'batal'">Batalkan</button>
        <button v-if="bisa.catatPelunasan" class="btn btn-outline" :disabled="memproses" @click="modalBayar = true">
          Catat Pelunasan
        </button>
        <button v-if="bisa.selesai" class="btn btn-primary" :disabled="memproses" @click="jalankanAksi('selesai')">
          <span v-if="memproses" class="spinner" aria-hidden="true" />
          {{ memproses ? 'Memproses...' : 'Tandai selesai' }}
        </button>
        <button
          v-else-if="bisa.lewatBelumLunas"
          class="btn btn-outline"
          disabled
          title="Booking belum lunas. Catat pelunasan terlebih dahulu."
        >
          Tandai selesai (Terkunci)
        </button>
        <button v-if="bisa.setujui" class="btn btn-primary" :disabled="memproses" @click="jalankanAksi('setujui')">
          <span v-if="memproses" class="spinner" aria-hidden="true" />
          {{ memproses ? 'Menyetujui...' : 'Setujui' }}
        </button>
      </template>
    </ModalDialog>

    <ModalDialog
      :buka="!!modalAlasan"
      :judul="modalAlasan === 'tolak' ? 'Tolak booking' : 'Batalkan booking'"
      @tutup="modalAlasan = null"
    >
      <div class="stack">
        <p class="muted">Slot akan dilepas dan semua pembayaran dikembalikan ke customer. Alasan ini terlihat oleh customer.</p>
        <label class="field">
          <span>Alasan (minimal 5 karakter)</span>
          <input v-model="alasan" class="input" maxlength="200" placeholder="Mis. lapang sedang diperbaiki" />
        </label>
      </div>
      <template #aksi>
        <button class="btn btn-ghost" :disabled="memproses" @click="modalAlasan = null">Kembali</button>
        <button class="btn btn-danger" :disabled="memproses || alasan.trim().length < 5" @click="jalankanAksi(modalAlasan)">
          <span v-if="memproses" class="spinner" aria-hidden="true" />
          {{ memproses ? 'Memproses...' : (modalAlasan === 'tolak' ? 'Tolak booking' : 'Batalkan booking') }}
        </button>
      </template>
    </ModalDialog>

    <ModalDialog
      :buka="modalBayar"
      :judul="`Catat Pelunasan · ${detail?.kode || ''}`"
      @tutup="modalBayar = false"
    >
      <div class="stack">
        <p>
          Catat pelunasan sisa tagihan untuk customer <strong>{{ detail?.customer.nama }}</strong> sebesar <strong>{{ rupiah(detail?.sisa_tagihan || 0) }}</strong>.
        </p>
        <label class="field">
          <span>Metode Pembayaran</span>
          <select v-model="metodeBayar" class="select">
            <option value="qris">QRIS</option>
            <option value="transfer">Transfer Bank</option>
            <option value="ewallet">E-Wallet / Kasir Tunai</option>
          </select>
        </label>
      </div>
      <template #aksi>
        <button class="btn btn-ghost" :disabled="memproses" @click="modalBayar = false">Batal</button>
        <button class="btn btn-primary" :disabled="memproses" @click="konfirmasiPelunasan">
          <span v-if="memproses" class="spinner" aria-hidden="true" />
          {{ memproses ? 'Menyimpan...' : 'Simpan Pelunasan' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: 0;
}

.filter {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) minmax(0, 1.5fr);
  gap: 12px;
  padding: 16px;
}

.redup {
  opacity: 0.6;
}

.nowrap {
  white-space: nowrap;
}

.baris {
  cursor: pointer;
}

.sel-ikon {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.nama-btn {
  padding: 0;
  border: 0;
  background: none;
  font-weight: 700;
  color: var(--brand-ink);
  cursor: pointer;
  text-align: left;
}

.nama-btn:hover {
  text-decoration: underline;
}

.halaman {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid var(--border);
}

.rincian {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
}

.rincian div {
  display: grid;
  grid-template-columns: 130px minmax(0, 1fr);
  gap: 12px;
}

.rincian dt {
  color: var(--muted);
}

.rincian dd {
  margin: 0;
  font-weight: 600;
}

@media (max-width: 900px) {
  .filter {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
