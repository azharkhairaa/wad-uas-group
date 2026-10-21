<script setup>
import { berisi } from '@/utils/slot'
import { STATUS_SLOT } from '@/utils/status'
import { jam, rupiahRingkas } from '@/utils/format'

defineProps({
  slots: { type: Array, required: true },
  pilihan: { type: Object, default: null },
  bisaPilih: { type: Boolean, default: true },
})
const emit = defineEmits(['klik'])
</script>

<template>
  <ul class="grid" role="list">
    <li v-for="s in slots" :key="s.jam">
      <button
        type="button"
        class="slot"
        :class="[s.status, { dipilih: berisi(pilihan, s.jam) }]"
        :disabled="!bisaPilih || s.status !== 'tersedia'"
        :aria-pressed="berisi(pilihan, s.jam)"
        :aria-label="`${jam(s.jam)}, ${STATUS_SLOT[s.status]}`"
        @click="emit('klik', s.jam)"
      >
        <span class="pukul">{{ jam(s.jam) }}</span>
        <span class="ket">
          {{ s.status === 'tersedia' ? rupiahRingkas(s.harga) : STATUS_SLOT[s.status] }}
        </span>
      </button>
    </li>
  </ul>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(78px, 1fr));
  gap: 8px;
}

.slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 8px 4px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface-2);
  color: var(--muted);
  line-height: 1.2;
  cursor: default;
}

.pukul {
  font-weight: 700;
  font-size: 0.92rem;
}

.ket {
  font-size: 0.72rem;
  margin-top: 2px;
}

.slot.tersedia {
  background: var(--surface);
  border-color: color-mix(in srgb, var(--brand) 45%, var(--border));
  color: var(--text);
  cursor: pointer;
}

.slot.tersedia .ket {
  color: var(--brand-ink);
  font-weight: 600;
}

/* :not(.dipilih) supaya hover tidak menimpa warna slot yang sedang dipilih */
.slot.tersedia:not(.dipilih):hover:not(:disabled) {
  background: var(--brand-soft);
}

.slot.dipilih {
  background: var(--brand);
  border-color: var(--brand);
  color: var(--on-brand);
}

.slot.dipilih .ket {
  color: var(--on-brand);
}

.slot.menunggu {
  background: var(--warning-soft);
  color: var(--warning);
  border-color: transparent;
}

.slot.dipesan {
  text-decoration: line-through;
  text-decoration-thickness: 1px;
}

.slot.milik_saya {
  background: var(--info-soft);
  color: var(--info);
  border-color: color-mix(in srgb, var(--info) 40%, transparent);
}

.slot.ditutup {
  background: repeating-linear-gradient(
    135deg,
    var(--surface-2) 0 6px,
    var(--surface-3) 6px 12px
  );
}

.slot.lewat {
  opacity: 0.45;
}

.slot:disabled {
  cursor: not-allowed;
}
</style>
