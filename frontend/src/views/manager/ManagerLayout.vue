<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import AppIcon from '@/components/AppIcon'
import RequestState from '@/components/RequestState.vue'
import { useAuthStore } from '@/stores/auth'
import { useManagerStore } from '@/stores/manager'

const auth = useAuthStore()
const manager = useManagerStore()
const route = useRoute()

const MENU = [
  { to: '/manager', label: 'Dashboard', ikon: 'chart', exact: true },
  { to: '/manager/bookings', label: 'Booking masuk', ikon: 'inbox' },
  { to: '/manager/agenda', label: 'Agenda harian', ikon: 'calendar' },
  { to: '/manager/courts', label: 'Lapang & tarif', ikon: 'court' },
  { to: '/manager/schedule', label: 'Jam buka & penutupan', ikon: 'clock' },
  { to: '/manager/venue', label: 'Pengaturan venue', ikon: 'sliders' },
]

const menuList = computed(() => {
  const items = [...MENU]
  if (auth.isSuperadmin) {
    items.push({ to: '/manager/users', label: 'Kelola akun', ikon: 'users' })
  }
  return items
})

onMounted(() => {
  if (!manager.venues.length) manager.muat()
})
</script>

<template>
  <div class="container layout">
    <aside class="sidebar card">
      <label class="field">
        <span>Venue</span>
        <select v-model="manager.venueId" class="select" :disabled="!manager.venues.length">
          <option v-for="v in manager.venues" :key="v.id" :value="v.id">
            {{ v.nama }}{{ v.is_active ? '' : ' (nonaktif)' }}
          </option>
        </select>
      </label>
      <nav aria-label="Menu manager">
        <RouterLink
          v-for="m in menuList"
          :key="m.to"
          :to="m.to"
          class="menu"
          :active-class="m.exact ? '' : 'aktif'"
          :exact-active-class="'aktif'"
        >
          <AppIcon :name="m.ikon" :size="18" />{{ m.label }}
        </RouterLink>
      </nav>
      <RouterLink
        v-if="manager.venue"
        :to="{ name: 'venue', params: { slug: manager.venue.slug } }"
        class="small publik"
      >
        Lihat halaman publik
      </RouterLink>
    </aside>

    <section class="konten">
      <!-- pengaturan venue & kelola pengguna tetap bisa dibuka walau belum punya venue -->
      <RouterView
        v-if="manager.venue || route.name === 'manager-venue' || route.name === 'manager-users'"
        :key="route.name === 'manager-users' ? 'users' : (manager.venue?.id ?? 0)"
      />
      <RequestState
        v-else
        :loading="manager.loading || (!manager.error && !manager.venues.length && !manager.sudahDimuat)"
        :error="manager.error"
        :kosong="manager.sudahDimuat && !manager.venues.length"
        judul-kosong="Kamu belum punya venue"
        pesan-kosong="Tambahkan venue pertama di menu Pengaturan venue."
        :tinggi="300"
        @ulang="manager.muat()"
      >
        <template #aksi-kosong>
          <RouterLink to="/manager/venue" class="btn btn-primary btn-sm">Tambah venue</RouterLink>
        </template>
      </RequestState>
    </section>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 24px;
  padding-top: 24px;
  padding-bottom: 56px;
  align-items: start;
}

.sidebar {
  position: sticky;
  top: 84px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 10px;
  color: var(--text-2);
  font-weight: 600;
  font-size: 0.92rem;
}

.menu:hover {
  background: var(--surface-2);
  text-decoration: none;
}

.menu.aktif {
  background: var(--brand-soft);
  color: var(--brand-ink);
}

.publik {
  padding: 0 12px;
}

.konten {
  min-width: 0;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .sidebar {
    position: static;
  }

  nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .menu {
    white-space: nowrap;
  }
}
</style>
