<script setup>
import { reactive, ref } from 'vue'

import { managerApi } from '@/api'
import ModalDialog from '@/components/ModalDialog.vue'
import { useManagerStore } from '@/stores/manager'
import { useToastStore } from '@/stores/toast'
import { MODE_KONFIRMASI } from '@/utils/status'

const manager = useManagerStore()
const toast = useToastStore()

function dariVenue(v) {
  return {
    nama: v?.nama || '',
    kota: v?.kota || 'Bandung',
    alamat: v?.alamat || '',
    telepon: v?.telepon || '',
    deskripsi: v?.deskripsi || '',
    fasilitas: (v?.fasilitas || []).join(', '),
    mode_konfirmasi: v?.mode_konfirmasi || 'otomatis',
    persen_deposit: v?.persen_deposit ?? 50,
    batas_bayar_menit: v?.batas_bayar_menit ?? 30,
  }
}

function keData(f) {
  return {
    nama: f.nama.trim(),
    kota: f.kota.trim(),
    alamat: f.alamat.trim(),
    telepon: f.telepon.trim() || null,
    deskripsi: f.deskripsi.trim() || null,
    fasilitas: f.fasilitas.split(',').map((x) => x.trim()).filter(Boolean),
    mode_konfirmasi: f.mode_konfirmasi,
    persen_deposit: Number(f.persen_deposit),
    batas_bayar_menit: Number(f.batas_bayar_menit),
  }
}

const form = reactive(dariVenue(manager.venue))
const menyimpan = ref(false)
const pesanError = ref('')

const baru = reactive(dariVenue(null))
const modalBaru = ref(!manager.venue)
const errorBaru = ref('')
const menyimpanBaru = ref(false)

async function simpan() {
  menyimpan.value = true
  pesanError.value = ''
  try {
    const hasil = await managerApi.ubahVenue(manager.venue.id, keData(form))
    manager.perbarui(hasil)
    toast.sukses('Pengaturan venue disimpan.')
  } catch (e) {
    pesanError.value = e.message
  } finally {
    menyimpan.value = false
  }
}

async function gantiAktif() {
  try {
    const hasil = await managerApi.ubahVenue(manager.venue.id, { is_active: !manager.venue.is_active })
    manager.perbarui(hasil)
    toast.info(hasil.is_active ? 'Venue tampil lagi di pencarian.' : 'Venue disembunyikan dari pencarian.')
  } catch (e) {
    toast.gagal(e.message)
  }
}

async function tambahVenue() {
  errorBaru.value = ''
  menyimpanBaru.value = true
  try {
    const hasil = await managerApi.tambahVenue(keData(baru))
    manager.perbarui(hasil)
    manager.venueId = hasil.id
    modalBaru.value = false
    Object.assign(baru, dariVenue(null))
    toast.sukses(`${hasil.nama} ditambahkan. Lanjutkan dengan menambah lapang.`)
  } catch (e) {
    errorBaru.value = e.message
  } finally {
    menyimpanBaru.value = false
  }
}
</script>

<template>
  <div class="stack">
    <div class="page-head">
      <div>
        <h1>Pengaturan venue</h1>
        <p>Profil venue, cara konfirmasi booking dan aturan deposit.</p>
      </div>
      <button class="btn btn-outline" @click="modalBaru = true">+ Tambah venue</button>
    </div>

    <form v-if="manager.venue" class="card card-body stack" @submit.prevent="simpan">
      <div v-if="pesanError" class="alert danger" role="alert">{{ pesanError }}</div>
      <div class="form-grid">
        <label class="field">
          <span>Nama venue</span>
          <input v-model="form.nama" class="input" required minlength="3" maxlength="120" />
        </label>
        <label class="field">
          <span>Kota</span>
          <input v-model="form.kota" class="input" required minlength="3" maxlength="60" />
        </label>
        <label class="field full">
          <span>Alamat</span>
          <input v-model="form.alamat" class="input" required minlength="5" maxlength="255" />
        </label>
        <label class="field">
          <span>Telepon</span>
          <input v-model="form.telepon" class="input" inputmode="tel" maxlength="16" />
        </label>
        <label class="field">
          <span>Fasilitas</span>
          <input v-model="form.fasilitas" class="input" placeholder="Parkir, Musala, Kantin" />
          <small>Pisahkan dengan koma</small>
        </label>
        <label class="field full">
          <span>Deskripsi</span>
          <textarea v-model="form.deskripsi" class="textarea" maxlength="2000" rows="3" />
        </label>
      </div>

      <fieldset class="mode">
        <legend class="field-label">Konfirmasi booking</legend>
        <label v-for="(label, kode) in MODE_KONFIRMASI" :key="kode" class="opsi">
          <input v-model="form.mode_konfirmasi" type="radio" name="mode" :value="kode" />
          <span>
            <strong>{{ label }}</strong>
            <small class="muted">
              {{ kode === 'otomatis' ? 'Begitu customer membayar DP, booking langsung terkonfirmasi.' : 'Setelah DP dibayar, booking menunggu kamu setujui atau tolak.' }}
            </small>
          </span>
        </label>
      </fieldset>

      <div class="form-grid">
        <label class="field">
          <span>Deposit (DP) dalam persen</span>
          <input v-model.number="form.persen_deposit" class="input" type="number" min="10" max="100" step="5" required />
          <small>10 sampai 100. Isi 100 kalau customer wajib bayar lunas di awal.</small>
        </label>
        <label class="field">
          <span>Batas waktu bayar DP (menit)</span>
          <input v-model.number="form.batas_bayar_menit" class="input" type="number" min="10" max="1440" step="5" required />
          <small>Lewat dari ini, booking kedaluwarsa dan slot dilepas.</small>
        </label>
      </div>

      <div class="kaki">
        <button type="button" class="btn btn-ghost" @click="gantiAktif">
          {{ manager.venue.is_active ? 'Sembunyikan venue dari pencarian' : 'Tampilkan venue lagi' }}
        </button>
        <button class="btn btn-primary" :disabled="menyimpan">
          <span v-if="menyimpan" class="spinner" aria-hidden="true" />
          {{ menyimpan ? 'Menyimpan...' : 'Simpan pengaturan' }}
        </button>
      </div>
    </form>

    <ModalDialog :buka="modalBaru" judul="Tambah venue" :lebar="620" @tutup="modalBaru = false">
      <form id="form-venue-baru" class="form-grid" @submit.prevent="tambahVenue">
        <div v-if="errorBaru" class="alert danger full" role="alert">{{ errorBaru }}</div>
        <label class="field full">
          <span>Nama venue</span>
          <input v-model="baru.nama" class="input" required minlength="3" maxlength="120" />
        </label>
        <label class="field">
          <span>Kota</span>
          <input v-model="baru.kota" class="input" required minlength="3" maxlength="60" />
        </label>
        <label class="field">
          <span>Mode konfirmasi</span>
          <select v-model="baru.mode_konfirmasi" class="select">
            <option v-for="(label, kode) in MODE_KONFIRMASI" :key="kode" :value="kode">{{ label }}</option>
          </select>
        </label>
        <label class="field full">
          <span>Alamat</span>
          <input v-model="baru.alamat" class="input" required minlength="5" maxlength="255" />
        </label>
        <label class="field">
          <span>Deposit (%)</span>
          <input v-model.number="baru.persen_deposit" class="input" type="number" min="10" max="100" required />
        </label>
        <label class="field">
          <span>Fasilitas</span>
          <input v-model="baru.fasilitas" class="input" placeholder="Parkir, Musala" />
        </label>
        <p class="muted small full">Jam operasional awal 08:00–22:00 setiap hari, bisa diubah setelah venue dibuat.</p>
      </form>
      <template #aksi>
        <button class="btn btn-ghost" :disabled="menyimpanBaru" @click="modalBaru = false">Batal</button>
        <button class="btn btn-primary" type="submit" form="form-venue-baru" :disabled="menyimpanBaru">
          <span v-if="menyimpanBaru" class="spinner" aria-hidden="true" />
          {{ menyimpanBaru ? 'Menyimpan...' : 'Tambah venue' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: 0;
}

.mode {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
  padding: 0;
  border: 0;
}

.mode legend {
  margin-bottom: 8px;
}

.opsi {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
}

.opsi:has(input:checked) {
  border-color: var(--brand);
  background: var(--brand-soft);
}

.opsi input {
  margin-top: 4px;
  accent-color: var(--brand);
}

.opsi span {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kaki {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

@media (max-width: 640px) {
  .mode {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
