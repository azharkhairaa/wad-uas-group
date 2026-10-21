<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { bookingApi } from '@/api'
import AppIcon from '@/components/AppIcon'
import ModalDialog from '@/components/ModalDialog.vue'
import RequestState from '@/components/RequestState.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useRequest } from '@/composables/useRequest'
import { useToastStore } from '@/stores/toast'
import { pukul, rentangJam, rupiah, tanggalPanjang, waktuLengkap } from '@/utils/format'
import { infoOlahraga } from '@/utils/olahraga'
import { JENIS_BAYAR, METODE_BAYAR } from '@/utils/status'

const route = useRoute()
const toast = useToastStore()
const { data: b, loading, error, jalankan } = useRequest(bookingApi.detail)
const muat = () => jalankan(route.params.kode)

const metode = ref('qris')
const memproses = ref('')
const modalBatal = ref(false)
const alasan = ref('')
const sekarang = ref(Date.now())

const sisaDetik = computed(() => {
  if (!b.value?.batas_bayar || b.value.status !== 'menunggu_pembayaran') return null
  return Math.max(0, Math.floor((new Date(b.value.batas_bayar).getTime() - sekarang.value) / 1000))
})

const hitungMundur = computed(() => {
  if (sisaDetik.value === null) return ''
  const m = String(Math.floor(sisaDetik.value / 60)).padStart(2, '0')
  const s = String(sisaDetik.value % 60).padStart(2, '0')
  return `${m}:${s}`
})

const bisaBayarDp = computed(() => b.value?.status === 'menunggu_pembayaran' && sisaDetik.value > 0)
const bisaLunasi = computed(
  () =>
    ['menunggu_pembayaran', 'menunggu_persetujuan', 'terkonfirmasi'].includes(b.value?.status) &&
    b.value.sisa_tagihan > 0 &&
    (b.value.status !== 'menunggu_pembayaran' || sisaDetik.value > 0),
)

const langkah = computed(() => {
  if (!b.value) return []
  const s = b.value.status
  const sudahBayar = b.value.jumlah_dibayar > 0
  const terkonfirmasi = ['terkonfirmasi', 'selesai'].includes(s)
  const daftar = [
    { label: 'Booking dibuat', waktu: b.value.created_at, selesai: true },
    { label: 'DP dibayar', waktu: b.value.payments.find((p) => p.jenis !== 'refund')?.created_at, selesai: sudahBayar },
    {
      label: b.value.venue.mode_konfirmasi === 'manual' ? 'Disetujui manager' : 'Terkonfirmasi otomatis',
      waktu: b.value.dikonfirmasi_pada,
      selesai: terkonfirmasi,
    },
    { label: 'Selesai main', selesai: s === 'selesai' },
  ]
  if (['dibatalkan', 'ditolak', 'kedaluwarsa'].includes(s)) {
    const tutup = { dibatalkan: 'Dibatalkan', ditolak: 'Ditolak manager', kedaluwarsa: 'Kedaluwarsa' }[s]
    return [...daftar.filter((l) => l.selesai), { label: tutup, waktu: b.value.dibatalkan_pada, selesai: true, gagal: true }]
  }
  return daftar
})

async function bayar(jenis) {
  memproses.value = jenis
  try {
    b.value = await bookingApi.bayar(b.value.kode, { jenis, metode: metode.value })
    const pesan = {
      terkonfirmasi: 'Pembayaran diterima. Booking kamu terkonfirmasi!',
      menunggu_persetujuan: 'Pembayaran diterima. Tinggal menunggu persetujuan manager venue.',
    }
    toast.sukses(pesan[b.value.status] || 'Pembayaran diterima.')
  } catch (e) {
    toast.gagal(e.message)
    muat()
  } finally {
    memproses.value = ''
  }
}

async function batalkan() {
  memproses.value = 'batal'
  try {
    b.value = await bookingApi.batal(b.value.kode, alasan.value.trim() || null)
    modalBatal.value = false
    toast.info('Booking dibatalkan dan slot sudah dilepas.')
  } catch (e) {
    toast.gagal(e.message)
  } finally {
    memproses.value = ''
  }
}

let timer
let sudahDimuatUlang = false
onMounted(() => {
  muat()
  timer = setInterval(() => {
    sekarang.value = Date.now()
    // batas bayar habis: muat ulang sekali supaya status kedaluwarsa dari server tampil
    if (sisaDetik.value === 0 && !loading.value && !sudahDimuatUlang) {
      sudahDimuatUlang = true
      setTimeout(muat, 1500)
    }
  }, 1000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="container page">
    <nav class="small crumb" aria-label="Breadcrumb">
      <RouterLink to="/bookings">Booking saya</RouterLink>
      <span class="muted"> / {{ route.params.kode }}</span>
    </nav>

    <RequestState :loading="loading && !b" :error="error" :tinggi="320" @ulang="muat">
      <template v-if="b">
        <div class="page-head">
          <div>
            <p class="muted small num">{{ b.kode }}</p>
            <h1>{{ b.venue.nama }}</h1>
          </div>
          <StatusBadge :status="b.status" class="besar" />
        </div>

        <div v-if="b.status === 'menunggu_pembayaran' && sisaDetik > 0" class="alert warning tenggat">
          <span class="waktu num" aria-hidden="true">{{ hitungMundur }}</span>
          <span>
            Slot ditahan sampai pukul {{ pukul(b.batas_bayar) }}. Bayar DP sebelum waktu habis, kalau
            tidak booking otomatis kedaluwarsa dan slot dilepas untuk orang lain.
          </span>
        </div>
        <div v-if="b.alasan_batal" class="alert danger">Alasan: {{ b.alasan_batal }}</div>

        <div class="tata">
          <div class="stack">
            <section class="card card-body">
              <h2 class="card-title">Detail jadwal</h2>
              <dl class="rincian">
                <div>
                  <dt>Lapang</dt>
                  <dd>{{ b.court.nama }}</dd>
                </div>
                <div><dt>Olahraga</dt><dd>{{ infoOlahraga(b.court.olahraga).panjang }}</dd></div>
                <div><dt>Tanggal</dt><dd>{{ tanggalPanjang(b.tanggal) }}</dd></div>
                <div>
                  <dt>Jam</dt>
                  <dd class="num">{{ rentangJam(b.jam_mulai, b.jam_selesai) }} ({{ b.durasi }} jam)</dd>
                </div>
                <div v-if="b.catatan"><dt>Catatan</dt><dd>{{ b.catatan }}</dd></div>
              </dl>
              <RouterLink :to="{ name: 'venue', params: { slug: b.venue.slug } }" class="small">
                Lihat venue
              </RouterLink>
            </section>

            <section class="card card-body">
              <h2 class="card-title">Status</h2>
              <ol class="timeline">
                <li v-for="l in langkah" :key="l.label" :class="{ selesai: l.selesai, gagal: l.gagal }">
                  <span class="titik"><AppIcon v-if="l.selesai" :name="l.gagal ? 'close' : 'check'" :size="14" :stroke="3" /></span>
                  <div>
                    <strong>{{ l.label }}</strong>
                    <p v-if="l.waktu" class="muted small">{{ waktuLengkap(l.waktu) }}</p>
                  </div>
                </li>
              </ol>
            </section>

            <section v-if="b.payments.length" class="card card-body">
              <h2 class="card-title">Riwayat pembayaran</h2>
              <div class="table-wrap">
                <table class="table">
                  <thead>
                    <tr><th>Waktu</th><th>Jenis</th><th>Metode</th><th>Referensi</th><th>Nominal</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in b.payments" :key="p.id">
                      <td>{{ waktuLengkap(p.created_at) }}</td>
                      <td>{{ JENIS_BAYAR[p.jenis] }}</td>
                      <td>{{ METODE_BAYAR[p.metode] }}</td>
                      <td class="num small">{{ p.kode_referensi }}</td>
                      <td class="num" :class="{ refund: p.jenis === 'refund' }">
                        {{ p.jenis === 'refund' ? '−' : '' }}{{ rupiah(p.nominal) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <aside class="stack">
            <section class="card card-body bayar">
              <h2 class="card-title">Pembayaran</h2>
              <dl class="rincian">
                <div><dt>Total</dt><dd class="num">{{ rupiah(b.total_harga) }}</dd></div>
                <div><dt>DP ({{ b.venue.persen_deposit }}%)</dt><dd class="num">{{ rupiah(b.nominal_deposit) }}</dd></div>
                <div><dt>Sudah dibayar</dt><dd class="num">{{ rupiah(b.jumlah_dibayar) }}</dd></div>
                <div class="sisa"><dt>Sisa tagihan</dt><dd class="num">{{ rupiah(b.sisa_tagihan) }}</dd></div>
              </dl>

              <template v-if="bisaBayarDp || bisaLunasi">
                <fieldset class="metode">
                  <legend class="field-label">Metode (simulasi)</legend>
                  <label v-for="(label, kode) in METODE_BAYAR" :key="kode" class="opsi">
                    <input v-model="metode" type="radio" name="metode" :value="kode" />
                    {{ label }}
                  </label>
                </fieldset>
                <button v-if="bisaBayarDp" class="btn btn-accent btn-block" :disabled="!!memproses" @click="bayar('deposit')">
                  <span v-if="memproses === 'deposit'" class="spinner" aria-hidden="true" />
                  Bayar DP {{ rupiah(b.nominal_deposit) }}
                </button>
                <button
                  v-if="bisaLunasi"
                  class="btn btn-block"
                  :class="bisaBayarDp ? 'btn-outline' : 'btn-primary'"
                  :disabled="!!memproses"
                  @click="bayar('pelunasan')"
                >
                  <span v-if="memproses === 'pelunasan'" class="spinner" aria-hidden="true" />
                  {{ bisaBayarDp ? 'Bayar lunas' : 'Lunasi sisa' }} {{ rupiah(b.sisa_tagihan) }}
                </button>
                <p class="muted small">Tidak ada uang sungguhan yang ditarik, pembayaran hanya simulasi.</p>
              </template>
              <p v-else-if="b.sisa_tagihan === 0 && b.jumlah_dibayar > 0" class="badge success plain lunas">Lunas</p>
            </section>

            <section v-if="b.bisa_dibatalkan" class="card card-body">
              <h2 class="card-title">Batalkan booking</h2>
              <p class="muted small">
                Batal paling lambat 24 jam sebelum main, uang kembali penuh. Kurang dari itu, DP tidak
                dikembalikan.
              </p>
              <button class="btn btn-danger btn-block" @click="modalBatal = true">Batalkan booking</button>
            </section>
          </aside>
        </div>

        <ModalDialog :buka="modalBatal" judul="Batalkan booking?" @tutup="modalBatal = false">
          <div class="stack">
            <p>
              Slot {{ rentangJam(b.jam_mulai, b.jam_selesai) }} di {{ b.court.nama }} akan dilepas dan
              bisa dipesan orang lain.
            </p>
            <div class="alert" :class="b.perkiraan_refund < b.jumlah_dibayar ? 'warning' : 'success'">
              Perkiraan dana kembali: <strong>{{ rupiah(b.perkiraan_refund) }}</strong>
              dari {{ rupiah(b.jumlah_dibayar) }} yang sudah dibayar.
            </div>
            <label class="field">
              <span>Alasan (opsional)</span>
              <input v-model="alasan" class="input" maxlength="200" placeholder="Mis. tim kurang orang" />
            </label>
          </div>
          <template #aksi>
            <button class="btn btn-ghost" @click="modalBatal = false">Tidak jadi</button>
            <button class="btn btn-danger" :disabled="memproses === 'batal'" @click="batalkan">
              Ya, batalkan
            </button>
          </template>
        </ModalDialog>
      </template>
    </RequestState>
  </div>
</template>

<style scoped>
.crumb {
  margin-bottom: 12px;
}

.tenggat {
  align-items: center;
  margin-bottom: 16px;
}

.waktu {
  flex: none;
  padding: 6px 12px;
  border-radius: 10px;
  background: var(--warning);
  color: var(--surface);
  font-weight: 800;
  font-size: 1.15rem;
}

.alert.danger {
  margin-bottom: 16px;
}

.tata {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 20px;
  align-items: start;
}

.rincian {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 14px 0;
}

.rincian div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.rincian dt {
  color: var(--muted);
}

.rincian dd {
  margin: 0;
  font-weight: 600;
  text-align: right;
}

.rincian .sisa {
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.rincian .sisa dd {
  font-weight: 800;
  font-size: 1.05rem;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 14px;
}

.timeline li {
  display: flex;
  gap: 12px;
  position: relative;
  padding-bottom: 14px;
  color: var(--muted);
}

.timeline li:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 13px;
  top: 30px;
  bottom: 0;
  width: 2px;
  background: var(--border);
}

.titik {
  display: grid;
  place-items: center;
  flex: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--border-strong);
  background: var(--surface);
}

.timeline li.selesai {
  color: var(--text);
}

.timeline li.selesai .titik {
  background: var(--brand);
  border-color: var(--brand);
  color: var(--on-brand);
}

.timeline li.gagal .titik {
  background: var(--danger);
  border-color: var(--danger);
  color: #fff;
}

.bayar {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metode {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 0;
  border: 0;
}

.opsi {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
}

.opsi:has(input:checked) {
  border-color: var(--brand);
  background: var(--brand-soft);
}

.opsi input {
  accent-color: var(--brand);
}

.refund {
  color: var(--success);
}

.lunas {
  align-self: flex-start;
}

@media (max-width: 900px) {
  .tata {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
