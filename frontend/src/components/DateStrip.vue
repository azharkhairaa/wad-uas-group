<script setup>
import { BULAN, keTanggal } from '@/utils/format'

defineProps({
  hari: { type: Array, required: true },
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const SINGKAT = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab']

function label(h) {
  const d = keTanggal(h.tanggal)
  return { hari: SINGKAT[d.getDay()], tgl: d.getDate(), bulan: BULAN[d.getMonth()] }
}
</script>

<template>
  <div class="strip" role="listbox" aria-label="Pilih tanggal">
    <button
      v-for="h in hari"
      :key="h.tanggal"
      type="button"
      role="option"
      class="hari"
      :class="{ weekend: h.is_weekend, tutup: h.is_tutup, habis: !h.is_tutup && h.slot_tersedia === 0 }"
      :aria-selected="h.tanggal === modelValue"
      @click="emit('update:modelValue', h.tanggal)"
    >
      <span class="nama">{{ label(h).hari }}</span>
      <span class="tgl">{{ label(h).tgl }}</span>
      <span class="bulan">{{ label(h).bulan }}</span>
      <span class="sisa">
        <template v-if="h.is_tutup">Tutup</template>
        <template v-else-if="h.slot_tersedia === 0">Penuh</template>
        <template v-else>{{ h.slot_tersedia }} slot</template>
      </span>
    </button>
  </div>
</template>

<style scoped>
/* min-width: 0 di induk grid wajib, kalau tidak strip ini memaksa halaman melebar di HP */
.strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 2px 2px 8px;
  scroll-snap-type: x proximity;
  min-width: 0;
}

.hari {
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 74px;
  padding: 10px 6px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  cursor: pointer;
  scroll-snap-align: start;
  line-height: 1.2;
}

.hari:hover {
  border-color: var(--brand);
}

.nama {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
}

.weekend .nama {
  color: var(--accent-ink);
}

.tgl {
  font-size: 1.35rem;
  font-weight: 800;
  margin: 2px 0;
}

.bulan {
  font-size: 0.74rem;
  color: var(--muted);
}

.sisa {
  margin-top: 6px;
  padding: 2px 7px;
  white-space: nowrap;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  background: var(--brand-soft);
  color: var(--brand-ink);
}

.tutup .sisa,
.habis .sisa {
  background: var(--surface-2);
  color: var(--muted);
}

.tutup {
  opacity: 0.7;
}

.hari[aria-selected='true'] {
  background: var(--brand);
  border-color: var(--brand);
  color: var(--on-brand);
}

.hari[aria-selected='true'] .nama,
.hari[aria-selected='true'] .bulan {
  color: inherit;
  opacity: 0.85;
}

.hari[aria-selected='true'] .sisa {
  background: rgb(255 255 255 / 20%);
  color: inherit;
}
</style>
