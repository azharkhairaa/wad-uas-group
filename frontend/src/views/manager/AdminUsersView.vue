<script setup>
import { computed, reactive, ref } from 'vue'

import { adminApi } from '@/api'
import AppIcon from '@/components/AppIcon'
import ModalDialog from '@/components/ModalDialog.vue'
import RequestState from '@/components/RequestState.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const users = ref([])
const loading = ref(false)
const error = ref('')
const cari = ref('')
const filterRole = ref('')

const KOSONG = {
  nama: '',
  email: '',
  no_hp: '',
  role: 'manager',
  password: 'Lapangin2026',
}
const form = reactive({ ...KOSONG })
const modal = ref(false)
const menyimpan = ref(false)
const togglingId = ref(null)
const pesanError = ref('')

async function muat() {
  loading.value = true
  error.value = ''
  try {
    const hasil = await adminApi.users()
    users.value = hasil
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
muat()

const ringkasan = computed(() => {
  const total = users.value.length
  const manager = users.value.filter((u) => u.role === 'manager').length
  const customer = users.value.filter((u) => u.role === 'customer').length
  const superadmin = users.value.filter((u) => u.role === 'superadmin').length
  return { total, manager, customer, superadmin }
})

const daftarTampil = computed(() => {
  const q = cari.value.trim().toLowerCase()
  return users.value.filter((u) => {
    const cocokRole = !filterRole.value || u.role === filterRole.value
    const cocokTeks = !q || u.nama.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
    return cocokRole && cocokTeks
  })
})

function bukaModal() {
  Object.assign(form, KOSONG)
  pesanError.value = ''
  modal.value = true
}

async function simpan() {
  pesanError.value = ''
  menyimpan.value = true
  try {
    await adminApi.tambahUser({
      nama: form.nama.trim(),
      email: form.email.trim(),
      no_hp: form.no_hp.trim() || null,
      role: form.role,
      password: form.password,
    })
    toast.sukses(`Akun ${form.role} untuk ${form.nama} berhasil dibuat!`)
    modal.value = false
    await muat()
  } catch (e) {
    pesanError.value = e.message
  } finally {
    menyimpan.value = false
  }
}

async function toggleAktif(u) {
  if (u.id === auth.user?.id) {
    toast.gagal('Tidak dapat menonaktifkan akun sendiri')
    return
  }
  togglingId.value = u.id
  const statusBaru = !u.is_active
  try {
    await adminApi.ubahUser(u.id, { is_active: statusBaru })
    u.is_active = statusBaru
    toast.sukses(`Status ${u.nama} berhasil diubah jadi ${statusBaru ? 'Aktif' : 'Nonaktif'}`)
  } catch (e) {
    toast.gagal(e.message)
  } finally {
    togglingId.value = null
  }
}

function roleBadgeClass(role) {
  if (role === 'superadmin') return 'badge-admin'
  if (role === 'manager') return 'badge-manager'
  return 'badge-customer'
}
</script>

<template>
  <div class="admin-users">
    <div class="row antara wrap-header">
      <div>
        <h1 class="judul">Kelola Pengguna</h1>
        <p class="muted">Kelola seluruh akun pengguna, buat akun manager baru, dan atur hak akses.</p>
      </div>
      <button class="btn btn-primary" @click="bukaModal">
        <AppIcon name="users" :size="18" />
        Tambah Akun Baru
      </button>
    </div>

    <!-- Statistik ringkas -->
    <div class="grid-stats">
      <div class="card stat-card">
        <div class="stat-num">{{ ringkasan.total }}</div>
        <div class="stat-label">Total Pengguna</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num stat-blue">{{ ringkasan.manager }}</div>
        <div class="stat-label">Manager Venue</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num stat-green">{{ ringkasan.customer }}</div>
        <div class="stat-label">Customer</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num stat-orange">{{ ringkasan.superadmin }}</div>
        <div class="stat-label">Superadmin</div>
      </div>
    </div>

    <!-- Filter & Pencarian -->
    <div class="row antara bar-filter wrap-filter">
      <div class="filter-group">
        <button
          type="button"
          class="btn btn-sm"
          :class="filterRole === '' ? 'btn-primary' : 'btn-outline'"
          @click="filterRole = ''"
        >
          Semua
        </button>
        <button
          type="button"
          class="btn btn-sm"
          :class="filterRole === 'manager' ? 'btn-primary' : 'btn-outline'"
          @click="filterRole = 'manager'"
        >
          Manager
        </button>
        <button
          type="button"
          class="btn btn-sm"
          :class="filterRole === 'customer' ? 'btn-primary' : 'btn-outline'"
          @click="filterRole = 'customer'"
        >
          Customer
        </button>
        <button
          type="button"
          class="btn btn-sm"
          :class="filterRole === 'superadmin' ? 'btn-primary' : 'btn-outline'"
          @click="filterRole = 'superadmin'"
        >
          Superadmin
        </button>
      </div>

      <div class="search-box">
        <AppIcon name="search" :size="16" class="search-icon" />
        <input
          v-model="cari"
          type="text"
          class="input input-sm search-input"
          placeholder="Cari nama atau email..."
        />
      </div>
    </div>

    <!-- Data Table -->
    <RequestState :loading="loading" :error="error" :kosong="!daftarTampil.length" judul-kosong="Tidak ada pengguna ditemukan" @ulang="muat">
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Nama & Email</th>
              <th>No. Handphone</th>
              <th>Peran</th>
              <th>Venue Dikelola</th>
              <th>Status</th>
              <th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in daftarTampil" :key="u.id" :class="{ nonaktif: !u.is_active }">
              <td>
                <div class="nama-user">{{ u.nama }}</div>
                <div class="muted small">{{ u.email }}</div>
              </td>
              <td>{{ u.no_hp || '-' }}</td>
              <td>
                <span class="badge" :class="roleBadgeClass(u.role)">
                  {{ u.role.toUpperCase() }}
                </span>
              </td>
              <td>
                <span v-if="u.venues && u.venues.length" class="venue-list">
                  {{ u.venues.join(', ') }}
                </span>
                <span v-else class="muted small">-</span>
              </td>
              <td>
                <span class="badge" :class="u.is_active ? 'success' : 'danger'">
                  {{ u.is_active ? 'Aktif' : 'Nonaktif' }}
                </span>
              </td>
              <td>
                <button
                  class="btn btn-ghost btn-sm"
                  :disabled="u.id === auth.user?.id || togglingId === u.id"
                  @click="toggleAktif(u)"
                >
                  <span v-if="togglingId === u.id" class="spinner" aria-hidden="true" />
                  {{ togglingId === u.id ? 'Mengubah...' : (u.is_active ? 'Nonaktifkan' : 'Aktifkan') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </RequestState>

    <!-- Modal Tambah Akun -->
    <ModalDialog :buka="modal" judul="Buat Akun Pengguna / Manager Baru" :lebar="540" @tutup="modal = false">
      <form id="form-user" class="form-grid" @submit.prevent="simpan">
        <div v-if="pesanError" class="alert danger full" role="alert">{{ pesanError }}</div>

        <label class="field full">
          <span>Nama Lengkap</span>
          <input
            v-model.trim="form.nama"
            class="input"
            required
            minlength="2"
            maxlength="100"
            placeholder="Mis. Ahmad Fauzi"
          />
        </label>

        <label class="field full">
          <span>Email</span>
          <input
            v-model.trim="form.email"
            class="input"
            type="email"
            required
            placeholder="Mis. manager.setiabudi@lapangin.id"
          />
        </label>

        <label class="field">
          <span>No. Handphone</span>
          <input
            v-model.trim="form.no_hp"
            class="input"
            placeholder="Mis. 08123456789"
          />
        </label>

        <label class="field">
          <span>Peran (Role)</span>
          <select v-model="form.role" class="select" required>
            <option value="manager">Manager Venue</option>
            <option value="customer">Customer</option>
            <option value="superadmin">Superadmin</option>
          </select>
        </label>

        <label class="field full">
          <span>Password</span>
          <input
            v-model="form.password"
            class="input"
            type="text"
            required
            minlength="6"
            placeholder="Minimal 6 karakter"
          />
          <span class="muted small">Default awal: Lapangin2026</span>
        </label>
      </form>

      <template #aksi>
        <button type="button" class="btn btn-ghost" :disabled="menyimpan" @click="modal = false">Batal</button>
        <button form="form-user" class="btn btn-primary" :disabled="menyimpan">
          <span v-if="menyimpan" class="spinner" aria-hidden="true" />
          {{ menyimpan ? 'Menyimpan...' : 'Simpan Akun' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.admin-users {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.wrap-header {
  align-items: flex-start;
  gap: 16px;
}

.judul {
  margin-bottom: 4px;
}

.grid-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.stat-card {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-num {
  font-size: 1.8rem;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--muted);
}

.stat-blue {
  color: var(--brand);
}

.stat-green {
  color: #10b981;
}

.stat-orange {
  color: var(--accent);
}

.bar-filter {
  gap: 12px;
  align-items: center;
}

.wrap-filter {
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 240px;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--muted);
  pointer-events: none;
}

.search-input {
  padding-left: 32px;
  width: 100%;
}

.nama-user {
  font-weight: 600;
}

.venue-list {
  font-size: 0.88rem;
  color: var(--brand);
}

.badge-admin {
  background: var(--brand);
  color: #fff;
}

.badge-manager {
  background: #0284c7;
  color: #fff;
}

.badge-customer {
  background: var(--surface-2);
  color: var(--text);
  border: 1px solid var(--border);
}

.nonaktif {
  opacity: 0.6;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form-grid .full {
  grid-column: span 2;
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  .form-grid .full {
    grid-column: span 1;
  }
}
</style>
