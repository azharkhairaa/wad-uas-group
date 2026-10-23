<script setup>
import { ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/AppIcon'
import BrandLogo from '@/components/BrandLogo.vue'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/auth'
import { useManagerStore } from '@/stores/manager'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const manager = useManagerStore()
const toast = useToastStore()
const router = useRouter()
const route = useRoute()
const { tema, gantiTema } = useTheme()
const keluarLoading = ref(false)

async function keluar() {
  keluarLoading.value = true
  try {
    await auth.logout()
    manager.reset()
    toast.info('Kamu sudah logout.')
    router.push({ name: 'home' })
  } finally {
    keluarLoading.value = false
  }
}
</script>

<template>
  <header class="header">
    <div class="container header-inner">
      <RouterLink to="/" class="brand" aria-label="Lapangin, ke beranda">
        <BrandLogo />
      </RouterLink>

      <div class="mobile-actions">
        <button
          class="btn btn-ghost btn-sm tema"
          :aria-label="tema === 'dark' ? 'Pakai tema terang' : 'Pakai tema gelap'"
          @click="gantiTema"
        >
          <AppIcon :name="tema === 'dark' ? 'sun' : 'moon'" :size="18" />
        </button>
        <span v-if="auth.sudahLogin" class="avatar avatar-hp" aria-hidden="true">
          {{ auth.user.nama.charAt(0) }}
        </span>
      </div>

      <nav id="menu-utama" class="nav" aria-label="Menu utama">
        <RouterLink to="/" class="nav-link" exact-active-class="aktif">Cari lapang</RouterLink>
        <RouterLink v-if="auth.isCustomer" to="/bookings" class="nav-link" active-class="aktif">
          Booking saya
        </RouterLink>
        <RouterLink v-if="auth.isManager" to="/manager" class="nav-link" active-class="aktif">
          Dashboard manager
        </RouterLink>

        <div class="nav-akhir">
          <button
            class="btn btn-ghost btn-sm tema"
            :aria-label="tema === 'dark' ? 'Pakai tema terang' : 'Pakai tema gelap'"
            @click="gantiTema"
          >
            <AppIcon :name="tema === 'dark' ? 'sun' : 'moon'" :size="18" />
          </button>
          <template v-if="auth.sudahLogin">
            <div class="user">
              <span class="avatar" aria-hidden="true">{{ auth.user.nama.charAt(0) }}</span>
              <span class="user-teks">
                <strong>{{ auth.user.nama }}</strong>
                <small>{{ auth.isManager ? 'Venue manager' : 'Customer' }}</small>
              </span>
            </div>
            <button class="btn btn-outline btn-sm" :disabled="keluarLoading" @click="keluar">
              <span v-if="keluarLoading" class="spinner" aria-hidden="true" />
              {{ keluarLoading ? 'Keluar...' : 'Logout' }}
            </button>
          </template>
          <template v-else-if="auth.siap">
            <RouterLink
              :to="route.meta.tamu ? { name: 'login' } : { name: 'login', query: { redirect: route.fullPath } }"
              class="btn btn-ghost btn-sm"
            >
              Login
            </RouterLink>
            <RouterLink to="/register" class="btn btn-primary btn-sm">Daftar</RouterLink>
          </template>
        </div>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 64px;
}

.brand:hover {
  text-decoration: none;
}

.nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.nav-link {
  padding: 8px 12px;
  border-radius: 9px;
  color: var(--text-2);
  font-weight: 600;
  font-size: 0.92rem;
}

.nav-link:hover {
  background: var(--surface-2);
  text-decoration: none;
}

.nav-link.aktif {
  color: var(--brand-ink);
  background: var(--brand-soft);
}

.nav-akhir {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.tema {
  font-size: 1rem;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--brand);
  color: var(--on-brand);
  font-weight: 700;
}

.user-teks {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
  font-size: 0.85rem;
}

.user-teks small {
  color: var(--muted);
}

.mobile-actions {
  display: none;
}

@media (max-width: 820px) {
  .mobile-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: auto;
  }

  .avatar-hp {
    width: 32px;
    height: 32px;
    font-size: 0.85rem;
  }

  .nav {
    display: none !important;
  }
}
</style>
