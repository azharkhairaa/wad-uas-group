<script setup>
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { bookingApi } from '@/api'
import AppIcon from '@/components/AppIcon'
import RequestState from '@/components/RequestState.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useRequest } from '@/composables/useRequest'
import { pukul, rentangJam, rupiah, tanggalPanjang } from '@/utils/format'

const TAB = [
  { kode: 'semua', label: 'Semua', status: null },
  { kode: 'aktif', label: 'Aktif', status: ['menunggu_pembayaran', 'menunggu_persetujuan', 'terkonfirmasi'] },
  { kode: 'selesai', label: 'Selesai', status: ['selesai'] },
  { kode: 'batal', label: 'Batal', status: ['dibatalkan', 'ditolak', 'kedaluwarsa'] },
]

const tab = ref('semua')
const { data, loading, error, jalankan } = useRequest(bookingApi.daftar)
jalankan()

const terpilih = computed(() => {
  const status = TAB.find((t) => t.kode === tab.value).status
  return (data.value || []).filter((b) => !status || status.includes(b.status))
})

function jumlah(kode) {
  const status = TAB.find((t) => t.kode === kode).status
  return (data.value || []).filter((b) => !status || status.includes(b.status)).length
}
</script>

<template>
  <div class="container page">
    <div class="page-head">
      <div>
        <h1>Booking saya</h1>
        <p>Riwayat dan status semua booking lapang kamu.</p>
      </div>
      <RouterLink to="/" class="btn btn-primary">Booking lapang lagi</RouterLink>
    </div>

    <div class="tabs" role="tablist" aria-label="Filter status booking">
      <button
        v-for="t in TAB"
        :key="t.kode"
        role="tab"
        :aria-selected="tab === t.kode"
        @click="tab = t.kode"
      >
        {{ t.label }} <span class="muted">({{ jumlah(t.kode) }})</span>
      </button>
    </div>

    <div class="isi">
      <RequestState
        :loading="loading"
        :error="error"
        :kosong="!loading && !error && data !== null && terpilih.length === 0"
        judul-kosong="Belum ada booking di sini"
        pesan-kosong="Booking yang kamu buat akan muncul di halaman ini."
        @ulang="jalankan()"
      >
        <template #aksi-kosong>
          <RouterLink to="/" class="btn btn-outline btn-sm">Cari lapang</RouterLink>
        </template>
        <TransitionGroup name="fade-list" tag="ul" class="daftar">
          <li v-for="b in terpilih" :key="b.id">
            <RouterLink :to="{ name: 'booking-detail', params: { kode: b.kode } }" class="item card">
              <span class="ikon"><AppIcon :name="b.court.olahraga" :size="22" /></span>
              <div class="utama">
                <div class="row">
                  <strong>{{ b.venue.nama }}</strong>
                  <StatusBadge :status="b.status" />
                </div>
                <p class="muted small">
                  {{ b.court.nama }} · {{ tanggalPanjang(b.tanggal) }} ·
                  <span class="num">{{ rentangJam(b.jam_mulai, b.jam_selesai) }}</span>
                </p>
                <p v-if="b.status === 'menunggu_pembayaran' && b.batas_bayar" class="peringatan small">
                  Bayar DP sebelum pukul {{ pukul(b.batas_bayar) }} supaya slot tidak lepas
                </p>
              </div>
              <div class="harga">
                <strong class="num">{{ rupiah(b.total_harga) }}</strong>
                <span class="muted small">{{ b.kode }}</span>
              </div>
            </RouterLink>
          </li>
        </TransitionGroup>
      </RequestState>
    </div>
  </div>
</template>

<style scoped>
.isi {
  margin-top: 18px;
}

.daftar {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  color: inherit;
}

.item:hover {
  text-decoration: none;
  border-color: var(--brand);
}

.ikon {
  display: grid;
  place-items: center;
  flex: none;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: var(--brand-soft);
  color: var(--brand-ink);
}

.utama {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.peringatan {
  color: var(--warning);
  font-weight: 600;
}

.harga {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  text-align: right;
}

@media (max-width: 560px) {
  .item {
    flex-wrap: wrap;
  }

  .harga {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>
