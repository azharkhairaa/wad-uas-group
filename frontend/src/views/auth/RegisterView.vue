<script setup>
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import BrandLogo from '@/components/BrandLogo.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const route = useRoute()
const router = useRouter()

const form = reactive({ nama: '', email: '', no_hp: '', password: '', ulang: '' })
const sudahKirim = ref(false)
const error = ref('')
const loading = ref(false)

// validasi di browser hanya untuk kenyamanan, backend tetap memvalidasi ulang
const masalah = computed(() => {
  const m = {}
  if (form.nama.trim().length < 2) m.nama = 'Nama minimal 2 huruf'
  if (!/^\S+@\S+\.\S+$/.test(form.email)) m.email = 'Format email belum benar'
  if (form.no_hp && !/^\+?[0-9]{9,15}$/.test(form.no_hp)) m.no_hp = 'Nomor HP 9–15 digit angka'
  if (form.password.length < 8) m.password = 'Minimal 8 karakter'
  else if (!/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
    m.password = 'Harus berisi huruf dan angka'
  }
  if (form.ulang !== form.password) m.ulang = 'Password belum sama'
  return m
})

async function daftar() {
  sudahKirim.value = true
  error.value = ''
  if (Object.keys(masalah.value).length) return
  loading.value = true
  try {
    const user = await auth.register({
      nama: form.nama.trim(),
      email: form.email.trim(),
      no_hp: form.no_hp || null,
      password: form.password,
    })
    toast.sukses(`Akun dibuat. Selamat datang, ${user.nama}!`)
    const redirect = String(route.query.redirect || '')
    router.replace(redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container auth">
    <form class="card kartu" novalidate @submit.prevent="daftar">
      <BrandLogo />
      <div>
        <h1>Daftar akun customer</h1>
        <p class="muted">Akun venue manager dibuat oleh pengelola sistem.</p>
      </div>

      <div v-if="error" class="alert danger" role="alert">{{ error }}</div>

      <label class="field">
        <span>Nama lengkap</span>
        <input v-model="form.nama" class="input" autocomplete="name" maxlength="100" :aria-invalid="sudahKirim && !!masalah.nama" />
        <span v-if="sudahKirim && masalah.nama" class="field-error">{{ masalah.nama }}</span>
      </label>
      <label class="field">
        <span>Email</span>
        <input v-model="form.email" class="input" type="email" autocomplete="email" :aria-invalid="sudahKirim && !!masalah.email" />
        <span v-if="sudahKirim && masalah.email" class="field-error">{{ masalah.email }}</span>
      </label>
      <label class="field">
        <span>Nomor HP (opsional)</span>
        <input v-model="form.no_hp" class="input" inputmode="tel" autocomplete="tel" placeholder="081234567890" :aria-invalid="sudahKirim && !!masalah.no_hp" />
        <span v-if="sudahKirim && masalah.no_hp" class="field-error">{{ masalah.no_hp }}</span>
      </label>
      <div class="form-grid">
        <label class="field">
          <span>Password</span>
          <input v-model="form.password" class="input" type="password" autocomplete="new-password" maxlength="72" :aria-invalid="sudahKirim && !!masalah.password" />
          <span v-if="sudahKirim && masalah.password" class="field-error">{{ masalah.password }}</span>
        </label>
        <label class="field">
          <span>Ulangi password</span>
          <input v-model="form.ulang" class="input" type="password" autocomplete="new-password" maxlength="72" :aria-invalid="sudahKirim && !!masalah.ulang" />
          <span v-if="sudahKirim && masalah.ulang" class="field-error">{{ masalah.ulang }}</span>
        </label>
      </div>
      <p class="small muted">Minimal 8 karakter, campuran huruf dan angka.</p>

      <button class="btn btn-primary btn-lg btn-block" :disabled="loading">
        <span v-if="loading" class="spinner" aria-hidden="true" />
        Buat akun
      </button>
      <p class="small muted tengah">
        Sudah punya akun? <RouterLink :to="{ name: 'login', query: route.query }">Login</RouterLink>
      </p>
    </form>
  </div>
</template>

<style scoped>
.auth {
  display: grid;
  place-items: center;
  padding-top: 40px;
  padding-bottom: 64px;
}

.kartu {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: min(480px, 100%);
  padding: 28px;
}

h1 {
  font-size: 1.45rem;
}

.tengah {
  text-align: center;
}
</style>
