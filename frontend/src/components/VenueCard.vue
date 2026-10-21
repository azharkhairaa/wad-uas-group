<script setup>
import { RouterLink } from 'vue-router'

import AppIcon from '@/components/AppIcon'
import { rupiah } from '@/utils/format'
import { infoOlahraga } from '@/utils/olahraga'

defineProps({ venue: { type: Object, required: true } })
</script>

<template>
  <RouterLink :to="{ name: 'venue', params: { slug: venue.slug } }" class="venue card">
    <div class="sampul" aria-hidden="true">
      <span v-for="o in venue.olahraga" :key="o" class="ikon"><AppIcon :name="o" :size="24" /></span>
    </div>
    <div class="isi">
      <div class="atas">
        <h3>{{ venue.nama }}</h3>
        <p class="muted small">{{ venue.alamat }}</p>
      </div>
      <ul class="olahraga">
        <li v-for="o in venue.olahraga" :key="o" class="badge plain">{{ infoOlahraga(o).label }}</li>
      </ul>
      <div class="bawah">
        <div>
          <span class="muted small">Mulai dari</span>
          <p class="harga">
            {{ venue.tarif_mulai ? rupiah(venue.tarif_mulai) : '-' }}<span class="muted small">/jam</span>
          </p>
        </div>
        <span class="small muted">{{ venue.jumlah_court }} lapang · DP {{ venue.persen_deposit }}%</span>
      </div>
    </div>
  </RouterLink>
</template>

<style scoped>
.venue {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: inherit;
  transition:
    transform 0.15s,
    box-shadow 0.15s,
    border-color 0.15s;
}

.venue:hover {
  text-decoration: none;
  transform: translateY(-2px);
  border-color: var(--brand);
  box-shadow: var(--shadow);
}

.sampul {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 112px;
  /* garis tengah dan garis tepi lapang sebagai hiasan */
  background:
    linear-gradient(90deg, transparent calc(50% - 1px), rgb(255 255 255 / 14%) calc(50% - 1px) calc(50% + 1px), transparent calc(50% + 1px)),
    linear-gradient(135deg, var(--hero), var(--hero-2));
  box-shadow: inset 0 0 0 10px var(--hero), inset 0 0 0 12px rgb(255 255 255 / 14%);
}

.ikon {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: rgb(255 255 255 / 12%);
  color: var(--cream);
}

.isi {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 18px 18px;
  flex: 1;
}

h3 {
  font-size: 1.08rem;
}

.olahraga {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.bawah {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.harga {
  font-weight: 800;
  font-size: 1.1rem;
  color: var(--brand-ink);
}
</style>
