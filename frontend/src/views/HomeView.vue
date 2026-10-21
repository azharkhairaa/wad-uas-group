<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { venueApi } from '@/api'
import AppIcon from '@/components/AppIcon'
import RequestState from '@/components/RequestState.vue'
import VenueCard from '@/components/VenueCard.vue'
import { useRequest } from '@/composables/useRequest'
import { DAFTAR_OLAHRAGA } from '@/utils/olahraga'

const route = useRoute()
const router = useRouter()

const q = ref(route.query.q || '')
const olahraga = ref(route.query.olahraga || '')
const { data: venues, loading, error, kosong, jalankan } = useRequest(venueApi.daftar)

function muat() {
  jalankan({ q: q.value.trim(), olahraga: olahraga.value })
  router.replace({ query: { ...(q.value ? { q: q.value } : {}), ...(olahraga.value ? { olahraga: olahraga.value } : {}) } })
}

// tunggu jeda mengetik sebelum memanggil API
let jeda
watch(q, () => {
  clearTimeout(jeda)
  jeda = setTimeout(muat, 300)
})
watch(olahraga, muat)
onBeforeUnmount(() => clearTimeout(jeda))
muat()

function pilihOlahraga(kode) {
  olahraga.value = olahraga.value === kode ? '' : kode
}
</script>

<template>
  <div>
    <section class="hero">
      <svg class="lapang" viewBox="0 0 460 260" aria-hidden="true">
        <g fill="none" stroke="rgb(255 255 255 / 22%)" stroke-width="3">
          <rect x="10" y="10" width="440" height="240" rx="4" />
          <line x1="230" y1="10" x2="230" y2="250" />
          <line x1="10" y1="40" x2="450" y2="40" />
          <line x1="10" y1="220" x2="450" y2="220" />
          <line x1="110" y1="40" x2="110" y2="220" />
          <line x1="350" y1="40" x2="350" y2="220" />
          <line x1="110" y1="130" x2="350" y2="130" />
        </g>
        <circle cx="300" cy="86" r="16" fill="var(--accent)" />
        <path d="M288 76 q12 10 0 22 M312 76 q-12 10 0 22" stroke="var(--hero)" stroke-width="2" fill="none" opacity="0.5" />
      </svg>
      <div class="container hero-inner">
        <p class="eyebrow">Tennis · Padel · Futsal · Golf Driving · Badminton · Voli · Basket</p>
        <h1>Cari lapang, pilih jam kosong, langsung main.</h1>
        <p class="lead">
          Lihat slot yang masih tersedia per jam di setiap lapang, cek tarif weekday dan weekend,
          lalu booking dengan deposit. Satu slot tidak mungkin dipesan dua orang.
        </p>
        <label class="cari">
          <span class="sr-only">Cari venue</span>
          <span class="cari-ikon"><AppIcon name="search" :size="20" /></span>
          <input
            v-model="q"
            class="input"
            type="search"
            maxlength="60"
            placeholder="Cari nama venue atau daerah, mis. Dago"
          />
        </label>
      </div>
    </section>

    <div class="container page">
      <div class="filter" role="group" aria-label="Filter jenis olahraga">
        <button class="chip" :aria-pressed="olahraga === ''" @click="olahraga = ''">Semua</button>
        <button
          v-for="o in DAFTAR_OLAHRAGA"
          :key="o.kode"
          class="chip"
          :aria-pressed="olahraga === o.kode"
          @click="pilihOlahraga(o.kode)"
        >
          <AppIcon :name="o.kode" :size="16" /> {{ o.label }}
        </button>
      </div>

      <div class="judul-daftar">
        <h2>Venue</h2>
        <span v-if="venues && !loading" class="muted small">{{ venues.length }} venue ditemukan</span>
      </div>

      <RequestState
        :loading="loading"
        :error="error"
        :kosong="kosong"
        :tinggi="300"
        :baris="2"
        judul-kosong="Venue tidak ditemukan"
        pesan-kosong="Coba kata kunci lain atau pilih semua olahraga."
        @ulang="muat"
      >
        <div class="venues">
          <VenueCard v-for="v in venues" :key="v.id" :venue="v" />
        </div>
      </RequestState>

      <section class="langkah" aria-labelledby="judul-langkah">
        <h2 id="judul-langkah">Cara booking</h2>
        <ol>
          <li>
            <span class="no">1</span>
            <div>
              <strong>Pilih venue dan tanggal</strong>
              <p class="muted small">Strip kalender menunjukkan sisa slot setiap hari.</p>
            </div>
          </li>
          <li>
            <span class="no">2</span>
            <div>
              <strong>Pilih jam yang kosong</strong>
              <p class="muted small">Klik beberapa jam berurutan, maksimal 4 jam per booking.</p>
            </div>
          </li>
          <li>
            <span class="no">3</span>
            <div>
              <strong>Bayar DP sebelum batas waktu</strong>
              <p class="muted small">Slot ditahan 30 menit. Setelah DP masuk, booking terkonfirmasi.</p>
            </div>
          </li>
        </ol>
      </section>
    </div>
  </div>
</template>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(140deg, var(--hero) 0%, var(--hero-2) 100%);
  color: var(--on-hero);
}

.lapang {
  position: absolute;
  right: -40px;
  top: 50%;
  width: 460px;
  transform: translateY(-50%) rotate(-8deg);
  opacity: 0.9;
  pointer-events: none;
}

@media (max-width: 960px) {
  .lapang {
    display: none;
  }
}

/* lebar maksimum dipasang di isi, bukan di container, supaya tidak melebihi layar HP */
.hero-inner {
  position: relative;
  padding-top: 52px;
  padding-bottom: 56px;
}

.hero-inner > * {
  max-width: 760px;
}

.eyebrow {
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--peach);
}

h1 {
  font-size: clamp(1.8rem, 4.2vw, 2.8rem);
  font-weight: 800;
  margin-top: 10px;
  letter-spacing: -0.025em;
}

.lead {
  margin-top: 12px;
  max-width: 640px;
  opacity: 0.85;
  font-size: 1.02rem;
}

.cari {
  position: relative;
  display: block;
  max-width: 560px;
  margin-top: 26px;
}

.cari .input {
  min-height: 52px;
  padding-left: 46px;
  border: 0;
  border-radius: 14px;
  font-size: 1rem;
  box-shadow: 0 10px 30px rgb(0 0 0 / 20%);
}

.cari-ikon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  color: var(--muted);
  z-index: 1;
}

.filter {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 6px;
}

.judul-daftar {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 22px 0 14px;
}

.judul-daftar h2 {
  font-size: 1.25rem;
}

.venues {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.langkah {
  margin-top: 44px;
}

.langkah h2 {
  font-size: 1.25rem;
  margin-bottom: 14px;
}

.langkah ol {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.langkah li {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: var(--radius);
  background: var(--surface);
  border: 1px solid var(--border);
}

.no {
  display: grid;
  place-items: center;
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--on-accent);
  font-weight: 800;
}
</style>
