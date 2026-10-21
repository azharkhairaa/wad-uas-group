<script setup>
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { managerApi } from '@/api'
import AppIcon from '@/components/AppIcon'
import RequestState from '@/components/RequestState.vue'
import { useRequest } from '@/composables/useRequest'
import { useManagerStore } from '@/stores/manager'
import { geserHari, hariIniIso, jam, rentangJam, tanggalPanjang } from '@/utils/format'
import { STATUS_BOOKING } from '@/utils/status'

const manager = useManagerStore()
const tanggal = ref(hariIniIso())
const { data, loading, error, jalankan } = useRequest(managerApi.agenda)

const muat = () => jalankan(manager.venue.id, { tanggal: tanggal.value })
watch(tanggal, muat)
muat()

const jamList = computed(() => {
  if (!data.value || data.value.is_tutup) return []
  return Array.from({ length: data.value.jam_tutup - data.value.jam_buka }, (_, i) => data.value.jam_buka + i)
})

function posisi(item) {
  const buka = data.value.jam_buka
  return { gridColumn: `${item.jam_mulai - buka + 1} / ${item.jam_selesai - buka + 1}` }
}

const totalBooking = computed(() =>
  (data.value?.courts || []).reduce((n, c) => n + c.items.filter((i) => i.jenis === 'booking').length, 0),
)
</script>

<template>
  <div class="stack">
    <div class="page-head">
      <div>
        <h1>Agenda harian</h1>
        <p>{{ manager.venue.nama }} · semua lapang dalam satu tampilan</p>
      </div>
      <div class="row">
        <button class="btn btn-outline btn-sm" aria-label="Hari sebelumnya" @click="tanggal = geserHari(tanggal, -1)"><AppIcon name="chevron-left" :size="16" /></button>
        <input v-model="tanggal" class="input tgl" type="date" aria-label="Tanggal" />
        <button class="btn btn-outline btn-sm" aria-label="Hari berikutnya" @click="tanggal = geserHari(tanggal, 1)"><AppIcon name="chevron-right" :size="16" /></button>
        <button class="btn btn-ghost btn-sm" @click="tanggal = hariIniIso()">Hari ini</button>
      </div>
    </div>

    <RequestState :loading="loading && !data" :error="error" :tinggi="320" @ulang="muat">
      <template v-if="data">
        <div class="ringkas">
          <strong>{{ tanggalPanjang(data.tanggal) }}</strong>
          <span v-if="data.is_tutup" class="badge muted">Venue tutup</span>
          <span v-else class="muted small">
            Buka {{ rentangJam(data.jam_buka, data.jam_tutup) }} · {{ totalBooking }} booking aktif
          </span>
        </div>

        <div v-if="data.is_tutup" class="alert warning">Venue tutup pada {{ data.hari }} sesuai jam operasional.</div>

        <div v-else class="card table-wrap">
          <div class="agenda" :style="{ '--kolom': jamList.length }">
            <div class="baris kepala">
              <div class="nama">Lapang</div>
              <div class="jalur jam">
                <span v-for="j in jamList" :key="j">{{ jam(j) }}</span>
              </div>
            </div>
            <div v-for="c in data.courts" :key="c.court.id" class="baris">
              <div class="nama">
                <AppIcon :name="c.court.olahraga" :size="16" />
                {{ c.court.nama }}
              </div>
              <div class="jalur">
                <template v-for="(item, i) in c.items" :key="i">
                  <RouterLink
                    v-if="item.jenis === 'booking'"
                    :to="{ name: 'manager-bookings', query: { q: item.kode } }"
                    class="blok"
                    :class="item.status"
                    :style="posisi(item)"
                    :title="`${item.nama_customer} · ${STATUS_BOOKING[item.status].label}`"
                  >
                    <strong>{{ item.nama_customer }}</strong>
                    <span>{{ rentangJam(item.jam_mulai, item.jam_selesai) }} · {{ STATUS_BOOKING[item.status].label }}</span>
                  </RouterLink>
                  <div v-else class="blok tutup" :style="posisi(item)" :title="item.alasan">
                    <strong>Tutup</strong>
                    <span>{{ item.alasan }}</span>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </template>
    </RequestState>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: 0;
}

.tgl {
  width: auto;
  min-height: 32px;
  padding: 4px 10px;
}

.ringkas {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.agenda {
  min-width: calc(160px + var(--kolom) * 64px);
}

.baris {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  border-bottom: 1px solid var(--border);
}

.baris:last-child {
  border-bottom: 0;
}

.nama {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  font-weight: 600;
  font-size: 0.88rem;
  border-right: 1px solid var(--border);
  background: var(--surface);
  position: sticky;
  left: 0;
  z-index: 1;
}

.jalur {
  display: grid;
  grid-template-columns: repeat(var(--kolom), minmax(0, 1fr));
  align-items: stretch;
  gap: 0;
  min-height: 58px;
  padding: 6px 0;
  background-image: linear-gradient(to right, var(--border) 1px, transparent 1px);
  background-size: calc(100% / var(--kolom)) 100%;
}

.kepala .nama,
.jam {
  font-size: 0.72rem;
  color: var(--muted);
  font-weight: 700;
  min-height: 0;
  padding: 8px 0;
}

.kepala .nama {
  padding-left: 12px;
}

.jam span {
  padding-left: 4px;
}

.blok {
  grid-row: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  margin: 0 2px;
  padding: 4px 8px;
  border-radius: 8px;
  border-left: 4px solid var(--neutral);
  background: var(--neutral-soft);
  color: var(--text);
  font-size: 0.76rem;
  line-height: 1.25;
  overflow: hidden;
}

.blok:hover {
  text-decoration: none;
  filter: brightness(0.97);
}

.blok strong,
.blok span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.blok span {
  color: var(--muted);
}

.blok.terkonfirmasi {
  background: var(--success-soft);
  border-left-color: var(--success);
}

.blok.menunggu_pembayaran {
  background: var(--warning-soft);
  border-left-color: var(--warning);
}

.blok.menunggu_persetujuan {
  background: var(--info-soft);
  border-left-color: var(--info);
}

.blok.tutup {
  border-left-color: var(--muted);
  background: repeating-linear-gradient(135deg, var(--surface-2) 0 6px, var(--surface-3) 6px 12px);
}
</style>
