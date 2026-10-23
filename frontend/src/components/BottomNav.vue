<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/AppIcon'
import ModalDialog from '@/components/ModalDialog.vue'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/auth'
import { useManagerStore } from '@/stores/manager'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const manager = useManagerStore()
const toast = useToastStore()
const route = useRoute()
const router = useRouter()
const { tema, gantiTema } = useTheme()

const modalAkun = ref(false)
const keluarLoading = ref(false)

const navItems = computed(() => {
  if (!auth.sudahLogin) {
    return [
      { to: '/', name: 'home', label: 'Beranda', ikon: 'home', exact: true },
      { to: '/?focus=search', name: 'search', label: 'Cari', ikon: 'search' },
      { to: '/login', name: 'login', label: 'Masuk', ikon: 'login' },
    ]
  }

  if (auth.isManager) {
    return [
      { to: '/manager', name: 'manager-dashboard', label: 'Dashboard', ikon: 'chart', exact: true },
      { to: '/manager/bookings', name: 'manager-bookings', label: 'Booking', ikon: 'inbox' },
      { to: '/manager/agenda', name: 'manager-agenda', label: 'Agenda', ikon: 'calendar' },
      { to: '/', name: 'home', label: 'Publik', ikon: 'home', exact: true },
      { aksi: 'akun', label: 'Akun', ikon: 'user' },
    ]
  }

  // default customer
  return [
    { to: '/', name: 'home', label: 'Beranda', ikon: 'home', exact: true },
    { to: '/?focus=search', name: 'search', label: 'Cari', ikon: 'search' },
    { to: '/bookings', name: 'bookings', label: 'Booking', ikon: 'calendar' },
    { aksi: 'akun', label: 'Akun', ikon: 'user' },
  ]
})

function isAktif(item) {
  if (item.aksi === 'akun') return modalAkun.value
  if (item.name === 'search') return route.path === '/' && route.query.focus === 'search'
  if (item.exact) return route.path === item.to
  return route.path.startsWith(item.to)
}

function klikNav(item) {
  if (item.aksi === 'akun') {
    modalAkun.value = true
  }
}

async function keluar() {
  keluarLoading.value = true
  try {
    await auth.logout()
    manager.reset()
    modalAkun.value = false
    toast.info('Kamu sudah logout.')
    router.push({ name: 'home' })
  } finally {
    keluarLoading.value = false
  }
}
</script>

<template>
  <div>
    <!-- Bottom Navigation Bar Mobile -->
    <nav class="bottom-nav" aria-label="Navigasi bawah mobile">
      <div class="bottom-nav-inner">
        <template v-for="(item, index) in navItems" :key="index">
          <button
            v-if="item.aksi"
            type="button"
            class="nav-tab"
            :class="{ aktif: isAktif(item) }"
            @click="klikNav(item)"
          >
            <div class="ikon-wrap">
              <AppIcon :name="item.ikon" :size="20" />
            </div>
            <span class="label">{{ item.label }}</span>
          </button>
          <RouterLink
            v-else
            :to="item.to"
            class="nav-tab"
            :class="{ aktif: isAktif(item) }"
          >
            <div class="ikon-wrap">
              <AppIcon :name="item.ikon" :size="20" />
            </div>
            <span class="label">{{ item.label }}</span>
          </RouterLink>
        </template>
      </div>
    </nav>

    <!-- Modal Profil / Akun Cepat -->
    <ModalDialog :buka="modalAkun" judul="Akun Pengguna" @tutup="modalAkun = false">
      <div v-if="auth.user" class="akun-modal-body">
        <div class="profil-card">
          <span class="avatar-besar" aria-hidden="true">{{ auth.user.nama.charAt(0) }}</span>
          <div class="profil-detail">
            <h3>{{ auth.user.nama }}</h3>
            <p class="muted small">{{ auth.user.email }}</p>
            <span class="badge" :class="auth.isSuperadmin ? 'badge-admin' : (auth.isManager ? 'info' : 'success')">
              {{ auth.user.role.toUpperCase() }}
            </span>
          </div>
        </div>

        <div class="opsi-list">
          <button type="button" class="btn btn-outline btn-block opsi-item" @click="gantiTema">
            <AppIcon :name="tema === 'dark' ? 'sun' : 'moon'" :size="18" />
            <span>Tema: {{ tema === 'dark' ? 'Gelap' : 'Terang' }}</span>
          </button>
        </div>
      </div>
      <template #aksi>
        <button type="button" class="btn btn-ghost" @click="modalAkun = false">Tutup</button>
        <button type="button" class="btn btn-danger" :disabled="keluarLoading" @click="keluar">
          <span v-if="keluarLoading" class="spinner" aria-hidden="true" />
          {{ keluarLoading ? 'Keluar...' : 'Logout' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.bottom-nav {
  display: none;
}

@media (max-width: 820px) {
  .bottom-nav {
    display: block;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 55;
    background: color-mix(in srgb, var(--surface) 95%, transparent);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-top: 1px solid var(--border);
    box-shadow: 0 -4px 20px rgb(0 0 0 / 7%);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }

  .bottom-nav-inner {
    display: flex;
    align-items: center;
    justify-content: space-around;
    height: 60px;
    max-width: 480px;
    margin: 0 auto;
    padding: 0 4px;
  }

  .nav-tab {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    height: 100%;
    border: none;
    background: transparent;
    color: var(--muted);
    text-decoration: none;
    cursor: pointer;
    padding: 4px 2px;
    transition: color 0.15s ease, transform 0.1s ease;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  .nav-tab:active {
    transform: scale(0.94);
  }

  .ikon-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 26px;
    border-radius: 12px;
    transition: background-color 0.2s ease, transform 0.2s ease;
  }

  .label {
    font-size: 0.72rem;
    font-weight: 600;
    line-height: 1.1;
    letter-spacing: -0.01em;
  }

  .nav-tab.aktif {
    color: var(--brand-ink);
  }

  .nav-tab.aktif .ikon-wrap {
    background: var(--brand-soft);
    color: var(--brand-ink);
    transform: translateY(-1px);
  }

  .nav-tab.aktif .label {
    font-weight: 700;
  }
}

.akun-modal-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.profil-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: var(--radius);
  background: var(--surface-2);
}

.avatar-besar {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--brand);
  color: var(--on-brand);
  font-size: 1.3rem;
  font-weight: 700;
  flex-shrink: 0;
}

.profil-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profil-detail h3 {
  font-size: 1.05rem;
  font-weight: 700;
}

.badge-admin {
  background: #f3e8ff;
  color: #7e22ce;
}

:root[data-theme='dark'] .badge-admin {
  background: #3b0764;
  color: #d8b4fe;
}

.opsi-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.opsi-item {
  justify-content: flex-start;
  padding: 10px 14px;
}
</style>
