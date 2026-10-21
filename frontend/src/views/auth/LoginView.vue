<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import BrandLogo from '@/components/BrandLogo.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const AKUN_DEMO = [
  { label: 'Customer', email: 'budi@example.com' },
  { label: 'Manager Dago & Setiabudi', email: 'manager.dago@lapangin.id' },
  { label: 'Manager Arcamanik & Antapani', email: 'manager.arcamanik@lapangin.id' },
]

// redirect hanya ke path internal supaya tidak bisa dipakai untuk open redirect
function tujuan(user) {
  const redirect = String(route.query.redirect || '')
  if (redirect.startsWith('/') && !redirect.startsWith('//')) {
    const rute = router.resolve(redirect)
    const butuhManager = rute.matched.some((r) => r.meta.role === 'manager')
    const butuhCustomer = rute.matched.some((r) => r.meta.role === 'customer')
    if (!(butuhManager && user.role !== 'manager') && !(butuhCustomer && user.role !== 'customer')) {
      return redirect
    }
  }
  return user.role === 'manager' ? { name: 'manager-dashboard' } : { name: 'home' }
}

async function masuk() {
  error.value = ''
  loading.value = true
  try {
    const user = await auth.login(email.value.trim(), password.value)
    toast.sukses(`Halo, ${user.nama}!`)
    router.replace(tujuan(user))
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function isiDemo(akun) {
  email.value = akun.email
  password.value = 'Lapangin2026'
}
</script>

<template>
  <div class="container auth">
    <form class="card kartu" novalidate @submit.prevent="masuk">
      <BrandLogo />
      <div>
        <h1>Login</h1>
        <p class="muted">Masuk untuk booking lapang atau mengelola venue.</p>
      </div>

      <div v-if="error" class="alert danger" role="alert">{{ error }}</div>

      <label class="field">
        <span>Email</span>
        <input v-model="email" class="input" type="email" autocomplete="email" required />
      </label>
      <label class="field">
        <span>Password</span>
        <input v-model="password" class="input" type="password" autocomplete="current-password" required />
      </label>

      <button class="btn btn-primary btn-lg btn-block" :disabled="loading || !email || !password">
        <span v-if="loading" class="spinner" aria-hidden="true" />
        Login
      </button>

      <p class="small muted tengah">
        Belum punya akun?
        <RouterLink :to="{ name: 'register', query: route.query }">Daftar sebagai customer</RouterLink>
      </p>

      <div class="demo">
        <p class="small"><strong>Akun demo</strong> (password <code>Lapangin2026</code>)</p>
        <div class="row">
          <button v-for="a in AKUN_DEMO" :key="a.email" type="button" class="btn btn-outline btn-sm" @click="isiDemo(a)">
            {{ a.label }}
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
.auth {
  display: grid;
  place-items: center;
  padding-top: 48px;
  padding-bottom: 64px;
}

.kartu {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: min(440px, 100%);
  padding: 28px;
}

h1 {
  font-size: 1.5rem;
}

.tengah {
  text-align: center;
}

.demo {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: var(--radius);
  background: var(--surface-2);
  border: 1px dashed var(--border-strong);
}

code {
  padding: 1px 6px;
  border-radius: 6px;
  background: var(--surface);
}
</style>
