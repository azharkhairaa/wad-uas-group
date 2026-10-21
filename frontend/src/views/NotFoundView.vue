<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="container page kosong">
    <p class="kode">404</p>
    <h1>Halaman tidak ditemukan</h1>
    <p class="muted">Alamat yang kamu buka tidak ada atau sudah dipindah.</p>
    <RouterLink to="/" class="btn btn-primary">Kembali ke beranda</RouterLink>
  </div>
</template>

<style scoped>
.kosong {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  padding-top: 80px;
}

.kode {
  font-size: 4rem;
  font-weight: 800;
  color: var(--brand);
  line-height: 1;
}
</style>
