<script setup>
import { RouterLink } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="container page kosong">
    <p class="kode">403</p>
    <h1>Kamu tidak punya akses ke halaman ini</h1>
    <p class="muted">
      Halaman ini khusus {{ auth.isManager ? 'customer' : 'venue manager' }}. Login dengan akun yang
      sesuai untuk membukanya.
    </p>
    <RouterLink :to="auth.isManager ? '/manager' : '/'" class="btn btn-primary">Kembali</RouterLink>
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
  color: var(--danger);
  line-height: 1;
}
</style>
