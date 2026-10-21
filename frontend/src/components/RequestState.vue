<script setup>
import AppIcon from '@/components/AppIcon'
// satu tempat untuk tiga keadaan selain berhasil: loading, error dan kosong
defineProps({
  loading: { type: Boolean, default: false },
  error: { type: [Object, Error], default: null },
  kosong: { type: Boolean, default: false },
  judulKosong: { type: String, default: 'Belum ada data' },
  pesanKosong: { type: String, default: '' },
  tinggi: { type: Number, default: 160 },
  baris: { type: Number, default: 3 },
})
defineEmits(['ulang'])
</script>

<template>
  <div v-if="loading" class="memuat" aria-busy="true" aria-label="Memuat data">
    <div v-for="i in baris" :key="i" class="skeleton" :style="{ height: `${tinggi / baris}px` }" />
  </div>
  <div v-else-if="error" class="kotak error" role="alert">
    <span class="ikon"><AppIcon name="alert" :size="22" /></span>
    <div>
      <p class="judul">Data gagal dimuat</p>
      <p class="muted">{{ error.message }}</p>
    </div>
    <button class="btn btn-outline btn-sm" @click="$emit('ulang')">Coba lagi</button>
  </div>
  <div v-else-if="kosong" class="kotak kosong">
    <span class="ikon"><AppIcon name="court" :size="22" /></span>
    <div>
      <p class="judul">{{ judulKosong }}</p>
      <p v-if="pesanKosong" class="muted">{{ pesanKosong }}</p>
    </div>
    <slot name="aksi-kosong" />
  </div>
  <slot v-else />
</template>

<style scoped>
.memuat {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kotak {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  padding: 22px;
  border-radius: var(--radius);
  border: 1px dashed var(--border-strong);
  background: var(--surface);
}

.kotak > div {
  flex: 1;
  min-width: 200px;
}

.error {
  border-style: solid;
  border-color: color-mix(in srgb, var(--danger) 40%, transparent);
  background: var(--danger-soft);
}

.judul {
  font-weight: 700;
}

.ikon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--surface-2);
  color: var(--muted);
}

.error .ikon {
  background: var(--danger);
  color: #fff;
}
</style>
