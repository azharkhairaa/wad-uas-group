<script setup>
import { computed, ref } from 'vue'

// grafik kolom satu sumbu, warna dari token --viz-1/--viz-2 yang sudah divalidasi
const props = defineProps({
  items: { type: Array, required: true }, // [{ key, label, judul, nilai, kategori, detail }]
  maks: { type: Number, default: null },
  format: { type: Function, default: (v) => String(v) },
  tinggi: { type: Number, default: 220 },
  penanda: { type: String, default: '' }, // key kolom yang diberi garis "hari ini"
  legenda: { type: Array, default: () => [] }, // [{ kategori, label }]
  judulTabel: { type: String, default: 'Data grafik' },
  labelSetiap: { type: Number, default: 0 },
})

const aktif = ref(null)
const tabel = ref(false)

const batas = computed(() => {
  if (props.maks) return props.maks
  const tertinggi = Math.max(1, ...props.items.map((i) => i.nilai))
  // dibulatkan ke angka rapi supaya garis bantu enak dibaca
  const pangkat = 10 ** Math.floor(Math.log10(tertinggi))
  return Math.ceil(tertinggi / pangkat) * pangkat
})

const garis = computed(() => [0, 0.25, 0.5, 0.75, 1].map((f) => ({ f, nilai: Math.round(batas.value * f) })))

const loncat = computed(() => props.labelSetiap || Math.max(1, Math.ceil(props.items.length / 12)))

function tinggiBatang(nilai) {
  return `${Math.min(100, (nilai / batas.value) * 100)}%`
}
</script>

<template>
  <figure class="kolom">
    <div v-if="legenda.length" class="legenda small">
      <span v-for="l in legenda" :key="l.kategori" class="item">
        <span class="swatch" :class="l.kategori" aria-hidden="true" />{{ l.label }}
      </span>
    </div>

    <div v-if="!tabel" class="plot" :style="{ height: `${tinggi}px` }">
      <div class="sumbu" aria-hidden="true">
        <span v-for="g in garis" :key="g.f" :style="{ bottom: `${g.f * 100}%` }">{{ format(g.nilai) }}</span>
      </div>
      <div class="area">
        <div v-for="g in garis" :key="g.f" class="grid-line" :style="{ bottom: `${g.f * 100}%` }" aria-hidden="true" />
        <div class="batang-list">
          <div
            v-for="(item, i) in items"
            :key="item.key"
            class="kolom-item"
            tabindex="0"
            :aria-label="`${item.judul || item.label}: ${format(item.nilai)}${item.detail ? ', ' + item.detail : ''}`"
            @mouseenter="aktif = i"
            @mouseleave="aktif = null"
            @focus="aktif = i"
            @blur="aktif = null"
          >
            <div v-if="item.key === penanda" class="penanda" aria-hidden="true"><span>Hari ini</span></div>
            <div class="batang" :class="[item.kategori || 'utama', { redup: aktif !== null && aktif !== i }]" :style="{ height: tinggiBatang(item.nilai) }" />
            <div v-if="aktif === i" class="tooltip" role="tooltip">
              <strong>{{ item.judul || item.label }}</strong>
              <span class="num">{{ format(item.nilai) }}</span>
              <span v-if="item.detail" class="muted">{{ item.detail }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="!tabel" class="label-x" aria-hidden="true">
      <span v-for="(item, i) in items" :key="item.key">{{ i % loncat === 0 ? item.label : '' }}</span>
    </div>

    <div v-else class="table-wrap">
      <table class="table">
        <caption class="sr-only">{{ judulTabel }}</caption>
        <thead>
          <tr><th>Label</th><th>Nilai</th><th>Keterangan</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.key">
            <td>{{ item.judul || item.label }}</td>
            <td class="num">{{ format(item.nilai) }}</td>
            <td class="muted">{{ item.detail }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <button class="btn btn-ghost btn-sm ganti" type="button" @click="tabel = !tabel">
      {{ tabel ? 'Lihat grafik' : 'Lihat sebagai tabel' }}
    </button>
  </figure>
</template>

<style scoped>
.kolom {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.legenda {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  color: var(--text-2);
}

.legenda .item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  background: var(--viz-1);
}

.swatch.mendatang {
  background: var(--viz-2);
}

.plot {
  display: flex;
  gap: 8px;
}

.sumbu {
  position: relative;
  width: 40px;
  flex: none;
  font-size: 0.72rem;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

.sumbu span {
  position: absolute;
  right: 0;
  transform: translateY(50%);
}

.area {
  position: relative;
  flex: 1;
  min-width: 0;
}

.grid-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--viz-grid);
}

.batang-list {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: stretch;
  gap: 2px;
}

.kolom-item {
  position: relative;
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  min-width: 0;
  outline-offset: -2px;
  cursor: default;
}

.batang {
  width: 100%;
  max-width: 24px;
  min-height: 2px;
  border-radius: 4px 4px 0 0;
  background: var(--viz-1);
  transition: opacity 0.15s;
}

.batang.mendatang {
  background: var(--viz-2);
}

.batang.redup {
  opacity: 0.45;
}

.penanda {
  position: absolute;
  top: -4px;
  bottom: 0;
  left: 50%;
  border-left: 1px solid var(--text-2);
  pointer-events: none;
}

.penanda span {
  position: absolute;
  top: -16px;
  left: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-2);
  white-space: nowrap;
}

.tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  z-index: 5;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  min-width: 150px;
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: 0 8px 24px rgb(0 0 0 / 16%);
  font-size: 0.8rem;
  pointer-events: none;
  white-space: nowrap;
}

.kolom-item:first-child .tooltip,
.kolom-item:nth-child(2) .tooltip {
  left: 0;
  transform: none;
}

.kolom-item:last-child .tooltip,
.kolom-item:nth-last-child(2) .tooltip {
  left: auto;
  right: 0;
  transform: none;
}

.label-x {
  display: flex;
  gap: 2px;
  margin-left: 48px;
  font-size: 0.7rem;
  color: var(--muted);
}

.label-x span {
  flex: 1;
  min-width: 0;
  text-align: center;
  white-space: nowrap;
  overflow: visible;
}

.ganti {
  align-self: flex-end;
}
</style>
