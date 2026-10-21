<script setup>
import { computed } from 'vue'

import AppIcon from '@/components/AppIcon'

// batang horizontal satu warna, nilai ditulis di ujung batang
const props = defineProps({
  items: { type: Array, required: true }, // [{ key, label, sub, ikon, nilai, detail }]
  maks: { type: Number, default: null },
  format: { type: Function, default: (v) => String(v) },
})

const batas = computed(() => props.maks || Math.max(1, ...props.items.map((i) => i.nilai)))
</script>

<template>
  <ul class="bars">
    <li v-for="item in items" :key="item.key" class="bar" tabindex="0" :title="item.detail">
      <span class="label">
        <span class="nama" :title="item.label"><AppIcon v-if="item.ikon" :name="item.ikon" :size="16" />{{ item.label }}</span>
        <span v-if="item.sub" class="sub">{{ item.sub }}</span>
      </span>
      <span class="track">
        <span class="isi" :style="{ width: `${Math.min(100, (item.nilai / batas) * 100)}%` }" />
        <span class="nilai num">{{ format(item.nilai) }}</span>
      </span>
      <span v-if="item.detail" class="detail" role="tooltip">{{ item.detail }}</span>
    </li>
  </ul>
</template>

<style scoped>
.bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bar {
  position: relative;
  display: grid;
  grid-template-columns: minmax(110px, 38%) minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  border-radius: 8px;
  outline-offset: 2px;
}

.label {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.2;
}

.nama {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.88rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub {
  font-size: 0.74rem;
  color: var(--muted);
}

.track {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.isi {
  height: 14px;
  min-width: 2px;
  border-radius: 0 4px 4px 0;
  background: var(--viz-1);
  transition: width 0.3s;
}

.nilai {
  flex: none;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-2);
}

.detail {
  position: absolute;
  right: 0;
  bottom: calc(100% + 4px);
  z-index: 5;
  display: none;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: 0 8px 24px rgb(0 0 0 / 16%);
  font-size: 0.78rem;
  white-space: nowrap;
}

.bar:hover .detail,
.bar:focus .detail {
  display: block;
}

.bar:hover .isi,
.bar:focus .isi {
  filter: brightness(1.1);
}
</style>
